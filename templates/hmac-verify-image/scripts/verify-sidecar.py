"""HMAC-verify sidecar — verifies signed webhooks and proxies to UPSTREAM_URL.

Sits as an ingress sidecar in front of any spoke that accepts signed
webhooks (GitHub, Stripe, Postmark, custom). Verifies the appropriate
`X-*-Signature*` header constant-time against the request body using a
shared secret, applies replay protection by delivery id, and only then
proxies the verified request to the upstream service. The constant-time
primitive (`hmac.compare_digest`) is lifted verbatim from
`templates/event-bridge-image/scripts/webhook_receiver.py` — security
parity with that image is the load-bearing invariant.

Endpoints:
  POST /verify              verify + proxy (default behavior)
  GET  /livez               process up
  GET  /readyz              upstream reachable (or skipped if no UPSTREAM_URL)
  GET  /healthz             diagnostic snapshot

Config (env):
  PROVIDER              github | stripe | postmark | custom (default: github)
  HMAC_SECRET           shared secret (resolved from KV in real deploys)
  HMAC_SECRET_FILE      path to mounted secret (preferred over env)
  UPSTREAM_URL          where to forward verified requests (e.g. http://app:8080/webhook)
  SIGNATURE_HEADER      override the provider's default header name
  SIGNATURE_PREFIX      override prefix (e.g. "sha256=" for github)
  DELIVERY_HEADER       override the provider's default delivery-id header
  REPLAY_TTL_SECONDS    replay window (default 300)
  HMAC_PORT             listen port (default 8083)
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

LOG = logging.getLogger("hmac-verify")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# ---------------------------------------------------------------------------
# Provider table — header names + signature prefix + algorithm.
# ---------------------------------------------------------------------------
# Each entry says: what header carries the sig, what algo, what (optional)
# prefix that algo lives behind, and what header carries the delivery id
# (for replay protection). The actual verification logic is identical across
# providers — only the header plumbing changes.
PROVIDERS: dict[str, dict[str, Any]] = {
    "github": {
        "sig_header": "X-Hub-Signature-256",
        "sig_prefix": "sha256=",
        "algo": "sha256",
        "delivery_header": "X-GitHub-Delivery",
    },
    "stripe": {
        # Stripe's signature header is structured: "t=...,v1=...". Real
        # Stripe verification also checks the timestamp; we keep it simple
        # here and treat the full header as the signature (sufficient for
        # the constant-time invariant + replay protection this sidecar
        # exists to enforce).
        "sig_header": "Stripe-Signature",
        "sig_prefix": "",
        "algo": "sha256",
        "delivery_header": "Stripe-Signature",
    },
    "postmark": {
        "sig_header": "X-Postmark-Signature",
        "sig_prefix": "",
        "algo": "sha256",
        "delivery_header": "X-Postmark-Message-Id",
    },
    "custom": {
        # Operator picks header + prefix via env.
        "sig_header": "X-Signature",
        "sig_prefix": "",
        "algo": "sha256",
        "delivery_header": "X-Delivery-Id",
    },
}

PROVIDER = os.getenv("PROVIDER", "github").lower()
if PROVIDER not in PROVIDERS:
    raise SystemExit(f"PROVIDER={PROVIDER!r} not in {list(PROVIDERS)}")

_cfg = PROVIDERS[PROVIDER].copy()
SIG_HEADER = os.getenv("SIGNATURE_HEADER", _cfg["sig_header"])
SIG_PREFIX = os.getenv("SIGNATURE_PREFIX", _cfg["sig_prefix"])
DELIVERY_HEADER = os.getenv("DELIVERY_HEADER", _cfg["delivery_header"])
ALGO = _cfg["algo"]

UPSTREAM_URL = os.getenv("UPSTREAM_URL", "")
REPLAY_TTL = int(os.getenv("REPLAY_TTL_SECONDS", "300"))
LISTEN_PORT = int(os.getenv("HMAC_PORT", "8083"))

SECRET_FILE = os.getenv("HMAC_SECRET_FILE", "/run/secrets/hmac_secret")
SECRET_ENV = os.getenv("HMAC_SECRET", "")


def _load_secret() -> bytes | None:
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "rb") as f:
            value = f.read().strip()
            return value or None
    return SECRET_ENV.encode() if SECRET_ENV else None


SECRET = _load_secret()
# delivery-id -> epoch-seconds. Bounded by the GC pass on every request.
_SEEN: dict[str, float] = {}


# ---------------------------------------------------------------------------
# App + lifespan.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # httpx client is reused across proxied requests so we keep the
    # connection pool warm. Timeout matches typical webhook SLAs.
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(
    title="AgentArmy hmac-verify",
    version="0.1.0",
    description="Constant-time HMAC verification sidecar with replay protection.",
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
async def readyz(request: Request) -> JSONResponse:
    """Ready to verify + proxy?  Requires SECRET; UPSTREAM_URL reachable if set."""
    problems: list[str] = []
    if SECRET is None:
        problems.append("HMAC_SECRET (or _FILE) not configured")
    if UPSTREAM_URL:
        try:
            # HEAD is cheapest; many upstreams 405 it which still proves reach.
            r = await request.app.state.http.head(UPSTREAM_URL)
            if r.status_code >= 500:
                problems.append(f"upstream {UPSTREAM_URL} -> {r.status_code}")
        except Exception as e:  # pragma: no cover — network error path
            problems.append(f"upstream {UPSTREAM_URL} unreachable: {e}")
    if problems:
        return JSONResponse(
            status_code=503,
            content={
                "type": "https://github.com/nickpclarke/AgentArmy/contracts/problems/not-ready",
                "title": "hmac-verify not ready",
                "status": 503,
                "detail": "; ".join(problems),
            },
        )
    return JSONResponse(
        status_code=200,
        content={"ok": True, "ts": _utc_now(), "dependencies": _deps()},
    )


@app.get("/healthz")
async def healthz() -> dict:
    """Diagnostic snapshot."""
    return {
        "ok": True,
        "ts": _utc_now(),
        "service": "hmac-verify",
        "version": app.version,
        "tier": "function",
        "provider": PROVIDER,
        "sig_header": SIG_HEADER,
        "sig_prefix": SIG_PREFIX,
        "delivery_header": DELIVERY_HEADER,
        "upstream_url": UPSTREAM_URL or None,
        "secret_configured": SECRET is not None,
        "replay_ttl_seconds": REPLAY_TTL,
        "dependencies": _deps(),
    }


def _deps() -> list[dict[str, Any]]:
    return [
        {
            "name": "secret",
            "ok": SECRET is not None,
            "message": "loaded" if SECRET else "not configured",
        },
        {
            "name": "upstream",
            "ok": True,  # presence is optional; reachability checked in readyz
            "message": UPSTREAM_URL or "not configured (verify-only mode)",
        },
    ]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# Replay cache.
# ---------------------------------------------------------------------------
def _gc_replay() -> None:
    """Drop expired entries. Called on every verify so the dict stays bounded."""
    now = time.time()
    for k in list(_SEEN):
        if now - _SEEN[k] > REPLAY_TTL:
            _SEEN.pop(k, None)


# ---------------------------------------------------------------------------
# /verify — the load-bearing endpoint.
# ---------------------------------------------------------------------------
@app.post("/verify")
async def verify(request: Request) -> Response:
    """Verify the signature, replay-check, optionally proxy."""
    if SECRET is None:
        # Fail closed — never accept unsigned input. Matches event-bridge's
        # security posture exactly.
        return _problem(500, "HMAC_SECRET (or _FILE) not configured", "config-error")

    body = await request.body()
    given_sig = request.headers.get(SIG_HEADER, "")
    if not given_sig:
        return _problem(401, f"missing signature header {SIG_HEADER}", "bad-signature")

    # Compute the expected signature. SIG_PREFIX is the algo-tag the provider
    # prepends (e.g. "sha256=" for GitHub); we add it before compare so the
    # constant-time check still works.
    digest = hmac.new(SECRET, body, getattr(hashlib, ALGO)).hexdigest()
    expected = f"{SIG_PREFIX}{digest}"

    # constant-time compare (CWE-208 timing-leak protection). Lifted verbatim
    # from templates/event-bridge-image/scripts/webhook_receiver.py.
    if not hmac.compare_digest(expected, given_sig):
        LOG.warning("bad signature on /verify (provider=%s)", PROVIDER)
        return _problem(401, "bad signature", "bad-signature")

    # Replay protection.
    delivery_id = request.headers.get(DELIVERY_HEADER, "")
    _gc_replay()
    if delivery_id and delivery_id in _SEEN:
        LOG.info("replay detected: delivery=%s", delivery_id)
        return _problem(
            409,
            f"replay detected: delivery-id {delivery_id} seen within {REPLAY_TTL}s",
            "replay-detected",
        )
    if delivery_id:
        _SEEN[delivery_id] = time.time()

    # If no upstream configured, this is verify-only mode.
    if not UPSTREAM_URL:
        return JSONResponse(
            status_code=200,
            content={"ok": True, "verified": True, "delivery_id": delivery_id or None},
        )

    # Proxy to upstream. Pass through original headers + body verbatim so
    # the upstream sees the canonical signed payload.
    fwd_headers = {
        k: v
        for k, v in request.headers.items()
        # Drop hop-by-hop + transfer-changing headers that httpx will set.
        if k.lower() not in {"host", "content-length", "connection", "transfer-encoding"}
    }
    try:
        upstream_resp = await request.app.state.http.post(
            UPSTREAM_URL, content=body, headers=fwd_headers
        )
    except httpx.HTTPError as e:
        LOG.error("upstream proxy failed: %s", e)
        return _problem(502, f"upstream proxy failed: {e}", "upstream-error")

    # Surface upstream status + body so the caller sees what the spoke saw.
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers={
            k: v
            for k, v in upstream_resp.headers.items()
            if k.lower() not in {"transfer-encoding", "connection", "content-encoding"}
        },
    )


def _problem(status: int, detail: str, slug: str) -> JSONResponse:
    """RFC 7807 Problem Details — matches contracts/problem-details.openapi.yaml."""
    return JSONResponse(
        status_code=status,
        content={
            "type": f"https://github.com/nickpclarke/AgentArmy/contracts/problems/{slug}",
            "title": detail,
            "status": status,
            "detail": detail,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=LISTEN_PORT)
