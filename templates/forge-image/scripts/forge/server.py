"""FastAPI server — webhook + on-demand generate endpoint.

Endpoints:
  GET  /livez                process up
  GET  /readyz               secrets + upstream backend-core ontology endpoint reachable
  GET  /healthz              diagnostic snapshot
  POST /webhook              HMAC-verified backend-core trigger
  POST /generate             on-demand generation; body matches CLI args

Webhook payload (per ARC-ADR-029 D8):
    { "event": "ontology.changed",
      "version": "2026-05-27T13:00:00Z",
      "etag": "W/\"abc123\"",
      "snapshot_url": "http://backend-core:8000/ontology/snapshot" }

Signature: GitHub-style `X-Hub-Signature-256: sha256=<hex>` over the raw
request body, using `WEBHOOK_HMAC_SECRET`. `hmac.compare_digest` for the
constant-time check — lifted verbatim from templates/hmac-verify-image's
verify-sidecar.py so we maintain security parity (CWE-208 protection).

Generate body:
    { "source": "http://backend-core:8000/ontology/snapshot?version=...",
      "target": "csharp|typescript|python|all",
      "out": "/tmp/forge-out",
      "consumer_repo": "owner/repo"  // optional; opens a PR
    }
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from .cli import TARGETS, generate as _generate_lib

LOG = logging.getLogger("forge")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

LISTEN_PORT = int(os.getenv("FORGE_PORT", "8086"))
HMAC_SECRET = os.getenv("WEBHOOK_HMAC_SECRET", "").encode() or None
DEFAULT_OUT_DIR = os.getenv("FORGE_OUT_DIR", "/tmp/forge-out")
DEFAULT_UPSTREAM = os.getenv("FORGE_DEFAULT_UPSTREAM", "")  # backend-core /ontology/snapshot
SIGNATURE_HEADER = os.getenv("WEBHOOK_SIGNATURE_HEADER", "X-Hub-Signature-256")
SIGNATURE_PREFIX = os.getenv("WEBHOOK_SIGNATURE_PREFIX", "sha256=")


# ---------------------------------------------------------------------------
# Request models.
# ---------------------------------------------------------------------------
class WebhookPayload(BaseModel):
    event: str = Field(..., description="e.g. 'ontology.changed'")
    version: Optional[str] = None
    etag: Optional[str] = None
    snapshot_url: Optional[str] = None


class GenerateRequest(BaseModel):
    source: str = Field(..., description="source URI (file://, http://, azureblob://)")
    target: str = Field("all", description=f"one of {TARGETS}")
    out: Optional[str] = Field(None, description="output dir; default FORGE_OUT_DIR")
    consumer_repo: Optional[str] = Field(
        None, description="if set, open a PR against owner/repo or local:/path/to/bare"
    )
    branch: Optional[str] = None
    if_none_match: Optional[str] = None


# ---------------------------------------------------------------------------
# App + lifespan.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(
    title="agentarmy-forge",
    version=__version__,
    description="Fleet code generator — ontology in, source files out (C# / TS / Python).",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health endpoints — match contracts/health.openapi.yaml.
# ---------------------------------------------------------------------------
@app.get("/livez")
async def livez() -> dict:
    return {"ok": True, "ts": _utc_now()}


@app.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    problems: list[str] = []
    if DEFAULT_UPSTREAM:
        try:
            r = await request.app.state.http.head(DEFAULT_UPSTREAM)
            if r.status_code >= 500:
                problems.append(f"upstream {DEFAULT_UPSTREAM} -> {r.status_code}")
        except Exception as e:
            problems.append(f"upstream {DEFAULT_UPSTREAM} unreachable: {e}")
    if problems:
        return JSONResponse(
            status_code=503,
            content={
                "type": "https://github.com/nickpclarke/AgentArmy/contracts/problems/not-ready",
                "title": "forge not ready",
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
    return {
        "ok": True,
        "ts": _utc_now(),
        "service": "agentarmy-forge",
        "version": __version__,
        "tier": "function",
        "default_upstream": DEFAULT_UPSTREAM or None,
        "out_dir": DEFAULT_OUT_DIR,
        "webhook_secret_configured": HMAC_SECRET is not None,
        "targets_available": list(TARGETS),
        "dependencies": _deps(),
    }


def _deps() -> list[dict[str, Any]]:
    return [
        {
            "name": "hmac_secret",
            "ok": HMAC_SECRET is not None,
            "message": "loaded" if HMAC_SECRET else "not configured (webhook will 500)",
        },
        {
            "name": "default_upstream",
            "ok": True,  # presence is optional
            "message": DEFAULT_UPSTREAM or "not configured (on-demand mode only)",
        },
    ]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# /webhook — HMAC-verified trigger from backend-core.
# ---------------------------------------------------------------------------
@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    if HMAC_SECRET is None:
        # Fail closed — never accept unsigned input.
        raise HTTPException(status_code=500, detail="WEBHOOK_HMAC_SECRET not configured")

    body = await request.body()
    given_sig = request.headers.get(SIGNATURE_HEADER, "")
    if not given_sig:
        raise HTTPException(status_code=401, detail=f"missing {SIGNATURE_HEADER}")

    digest = hmac.new(HMAC_SECRET, body, hashlib.sha256).hexdigest()
    expected = f"{SIGNATURE_PREFIX}{digest}"
    # constant-time compare (CWE-208) — lifted from verify-sidecar.py
    if not hmac.compare_digest(expected, given_sig):
        LOG.warning("bad webhook signature")
        raise HTTPException(status_code=401, detail="bad signature")

    # Parse + dispatch. Default to the configured upstream if the payload
    # doesn't carry a snapshot_url.
    import json

    try:
        payload = WebhookPayload.model_validate_json(body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"bad payload: {e}")

    source = payload.snapshot_url or DEFAULT_UPSTREAM
    if not source:
        raise HTTPException(
            status_code=400,
            detail="no snapshot_url in payload and FORGE_DEFAULT_UPSTREAM unset",
        )

    LOG.info("webhook accepted: event=%s version=%s source=%s", payload.event, payload.version, source)
    try:
        result = _generate_lib(
            source=source,
            target="all",
            out_dir=DEFAULT_OUT_DIR,
            if_none_match=payload.etag,
        )
    except Exception as e:
        LOG.exception("generate failed")
        raise HTTPException(status_code=500, detail=f"generate failed: {e}")
    return JSONResponse(status_code=200, content={"ok": True, "result": result})


# ---------------------------------------------------------------------------
# /generate — on-demand.
# ---------------------------------------------------------------------------
@app.post("/generate")
async def generate(req: GenerateRequest) -> JSONResponse:
    if req.target not in TARGETS:
        raise HTTPException(
            status_code=422, detail=f"target must be one of {TARGETS}; got {req.target!r}"
        )
    out_dir = req.out or DEFAULT_OUT_DIR
    try:
        result = _generate_lib(
            source=req.source,
            target=req.target,
            out_dir=out_dir,
            consumer_repo=req.consumer_repo,
            branch=req.branch,
            if_none_match=req.if_none_match,
        )
    except Exception as e:
        LOG.exception("generate failed")
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(status_code=200, content={"ok": True, "result": result})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=LISTEN_PORT)
