"""JWT introspection sidecar — POST /introspect over FastAPI.

Realizes the verify-side of ARC-ADR-002. Any spoke that wants a forwarded
user JWT verified calls 127.0.0.1:8084/introspect inside its own pod /
network namespace. The sidecar fetches + caches JWKS, verifies the
signature (RS256/ES256 only — no `none`, no symmetric algorithms for an
asymmetric trust contract), checks issuer/audience/exp/nbf with a
configurable leeway window, and returns the decoded claims (or 401).

Config (env):
    JWKS_URL              — HTTPS URL of the issuer's JWKS document (required for verify)
    JWKS_TTL_SECONDS      — JWKS cache TTL (default: 300)
    JWT_ISSUER            — Expected `iss` claim (optional; skipped if unset, warned)
    JWT_AUDIENCE          — Expected `aud` claim (optional; skipped if unset, warned)
    JWT_LEEWAY_SECONDS    — Clock-skew tolerance for exp/nbf (default: 0)
    JWT_ALGORITHMS        — Comma-list of allowed algs (default: RS256,ES256)
    INTROSPECT_PORT       — Listen port (default: 8084)

The doctor mints its own keypair + JWKS + tokens so the image proves
end-to-end without depending on an external IdP.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
import jwt
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    InvalidTokenError,
    PyJWTError,
)
from pydantic import BaseModel, Field

LOG = logging.getLogger("jwt-introspect")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# ---------------------------------------------------------------------------
# Config (env-driven; all read once at startup).
# ---------------------------------------------------------------------------
JWKS_URL = os.getenv("JWKS_URL", "")
JWKS_TTL_SECONDS = int(os.getenv("JWKS_TTL_SECONDS", "300"))
JWT_ISSUER = os.getenv("JWT_ISSUER", "") or None
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "") or None
JWT_LEEWAY_SECONDS = int(os.getenv("JWT_LEEWAY_SECONDS", "0"))
JWT_ALGORITHMS = [
    a.strip() for a in os.getenv("JWT_ALGORITHMS", "RS256,ES256").split(",") if a.strip()
]
LISTEN_PORT = int(os.getenv("INTROSPECT_PORT", "8084"))

# Algorithm allowlist guard — refuse to start with anything weak even if env
# tries to inject HS* (symmetric) or `none` (CWE-347).
_ALLOWED_ALGS = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}
_blocked = [a for a in JWT_ALGORITHMS if a not in _ALLOWED_ALGS]
if _blocked:
    raise SystemExit(
        f"refusing to start: JWT_ALGORITHMS contains weak/forbidden algs: {_blocked}. "
        f"Allowed: {sorted(_ALLOWED_ALGS)}"
    )

if not JWT_ISSUER:
    LOG.warning("JWT_ISSUER unset — issuer claim will NOT be verified (dev only)")
if not JWT_AUDIENCE:
    LOG.warning("JWT_AUDIENCE unset — audience claim will NOT be verified (dev only)")
if not JWKS_URL:
    LOG.warning("JWKS_URL unset — /introspect will 401 all tokens until configured")


# ---------------------------------------------------------------------------
# JWKS cache — TTL'd, dogpile-safe.
# ---------------------------------------------------------------------------
class _JwksCache:
    """Lazy + lock-guarded JWKS cache.

    PyJWKClient is sync (uses urllib internally), so we wrap a refresh in a
    threadpool executor under an asyncio.Lock to prevent concurrent
    first-callers from each triggering a fetch.
    """

    def __init__(self, url: str, ttl_seconds: int) -> None:
        self._url = url
        self._ttl = ttl_seconds
        self._client: PyJWKClient | None = None
        self._fetched_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_client(self) -> PyJWKClient:
        now = time.time()
        if self._client is not None and (now - self._fetched_at) < self._ttl:
            return self._client
        async with self._lock:
            now = time.time()
            if self._client is not None and (now - self._fetched_at) < self._ttl:
                return self._client
            LOG.info("refreshing JWKS from %s (ttl=%ds)", self._url, self._ttl)
            loop = asyncio.get_event_loop()
            # PyJWKClient.__init__ doesn't fetch; first .get_signing_key_from_jwt
            # call does. We force-fetch here so the cache timestamp reflects
            # real network I/O and we surface a JWKS-unreachable error eagerly.
            client = await loop.run_in_executor(
                None, lambda: PyJWKClient(self._url, cache_keys=True)
            )
            await loop.run_in_executor(None, client.get_jwk_set)
            self._client = client
            self._fetched_at = time.time()
            return self._client

    async def probe(self) -> tuple[bool, str]:
        """Readiness probe — returns (ok, message)."""
        if not self._url:
            return False, "JWKS_URL not configured"
        try:
            async with httpx.AsyncClient(timeout=5.0) as h:
                r = await h.get(self._url)
                if r.status_code >= 400:
                    return False, f"JWKS_URL returned HTTP {r.status_code}"
                # Sanity-check it's JWKS-shaped.
                body = r.json()
                if not isinstance(body, dict) or "keys" not in body:
                    return False, "JWKS_URL did not return a JWKS document (missing 'keys')"
                return True, f"JWKS reachable; {len(body.get('keys', []))} key(s)"
        except Exception as exc:  # noqa: BLE001 — probe surfaces error message
            return False, f"JWKS unreachable: {exc!s}"


_jwks_cache = _JwksCache(JWKS_URL, JWKS_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Request / response models.
# ---------------------------------------------------------------------------
class IntrospectRequest(BaseModel):
    token: str = Field(..., description="The bearer JWT to verify (no 'Bearer ' prefix).")


class IntrospectResponse(BaseModel):
    active: bool
    claims: dict[str, Any] | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# App + lifespan.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Don't block startup on JWKS fetch — readiness reports false until JWKS
    # has been fetched once. Same pattern as local-embedder's lazy model load.
    yield


app = FastAPI(
    title="AgentArmy jwt-introspect",
    version="0.1.0",
    description="JWT introspection sidecar — verifies forwarded user JWTs per ARC-ADR-002.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health endpoints — match contracts/health.openapi.yaml.
# ---------------------------------------------------------------------------
@app.get("/livez")
async def livez() -> dict:
    """Process alive? No dependency checks."""
    return {"ok": True, "ts": _utc_now()}


@app.get("/readyz")
async def readyz() -> JSONResponse:
    """Ready to accept introspect requests? Requires JWKS reachable."""
    ok, msg = await _jwks_cache.probe()
    if not ok:
        return JSONResponse(
            status_code=503,
            content={
                "type": "https://github.com/nickpclarke/AgentArmy/contracts/problems/not-ready",
                "title": "JWKS not reachable",
                "status": 503,
                "detail": msg,
            },
        )
    return JSONResponse(
        status_code=200,
        content={"ok": True, "ts": _utc_now(), "dependencies": _deps(jwks_ok=True, jwks_msg=msg)},
    )


@app.get("/healthz")
async def healthz() -> dict:
    """Diagnostic snapshot — version, issuer, audience, leeway, algs, JWKS state."""
    ok, msg = await _jwks_cache.probe()
    return {
        "ok": True,
        "ts": _utc_now(),
        "service": "jwt-introspect",
        "version": app.version,
        "tier": "function",
        "jwks_url": JWKS_URL,
        "jwks_ttl_seconds": JWKS_TTL_SECONDS,
        "jwks_reachable": ok,
        "issuer": JWT_ISSUER,
        "audience": JWT_AUDIENCE,
        "leeway_seconds": JWT_LEEWAY_SECONDS,
        "algorithms": JWT_ALGORITHMS,
        "dependencies": _deps(jwks_ok=ok, jwks_msg=msg),
    }


def _deps(*, jwks_ok: bool, jwks_msg: str) -> list[dict[str, Any]]:
    return [{"name": "jwks", "ok": jwks_ok, "message": jwks_msg}]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# /introspect — verify the JWT, return claims or 401.
# ---------------------------------------------------------------------------
@app.post("/introspect", response_model=IntrospectResponse)
async def introspect(req: IntrospectRequest) -> JSONResponse:
    if not JWKS_URL:
        return _unauthorized("JWKS_URL not configured on sidecar")
    if not req.token or not isinstance(req.token, str):
        return _unauthorized("token field missing or not a string")

    try:
        client = await _jwks_cache.get_client()
        loop = asyncio.get_event_loop()
        signing_key = await loop.run_in_executor(
            None, lambda: client.get_signing_key_from_jwt(req.token)
        )

        # decode_options: enforce signature + exp; iss/aud only if configured.
        decode_options: dict[str, Any] = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": JWT_AUDIENCE is not None,
            "verify_iss": JWT_ISSUER is not None,
            "require": ["exp"],
        }

        claims = jwt.decode(
            req.token,
            signing_key.key,
            algorithms=JWT_ALGORITHMS,
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            leeway=JWT_LEEWAY_SECONDS,
            options=decode_options,
        )
    except ExpiredSignatureError as exc:
        return _unauthorized(f"token expired: {exc!s}")
    except InvalidSignatureError as exc:
        return _unauthorized(f"signature verification failed: {exc!s}")
    except InvalidIssuerError as exc:
        return _unauthorized(f"issuer mismatch: {exc!s}")
    except InvalidAudienceError as exc:
        return _unauthorized(f"audience mismatch: {exc!s}")
    except InvalidTokenError as exc:
        return _unauthorized(f"invalid token: {exc!s}")
    except PyJWTError as exc:
        return _unauthorized(f"jwt error: {exc!s}")
    except Exception as exc:  # noqa: BLE001 — surface JWKS-fetch problems as 401
        LOG.warning("introspect failed: %s", exc, exc_info=True)
        return _unauthorized(f"introspect failed: {exc!s}")

    return JSONResponse(
        status_code=200,
        content={"active": True, "claims": claims},
    )


def _unauthorized(reason: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"active": False, "error": reason},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=LISTEN_PORT)
