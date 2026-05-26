"""AgentArmy webhook receiver — HTTP → CloudEvent → NATS JetStream.

Receives signed webhooks (GitHub HMAC-SHA256 to start), verifies the signature
with `hmac.compare_digest` (constant-time — secure-by-default), enforces a small
replay-protection cache keyed by the source's delivery id, wraps the payload as
a CloudEvents v1.0 envelope, and publishes to NATS at `${SUBJECT_PREFIX}.<event>`.

Endpoints:
  GET  /healthz             liveness + NATS URL echo
  POST /webhooks/github     GitHub webhook (HMAC sha256 via X-Hub-Signature-256)

Environment:
  NATS_URL                       default nats://nats:4222
  SUBJECT_PREFIX                 default fleet.gh
  GITHUB_WEBHOOK_SECRET_FILE     path to mounted secret (preferred)
  GITHUB_WEBHOOK_SECRET          env fallback (dev only)
  REPLAY_TTL_SECONDS             default 300
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import nats
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

NATS_URL = os.environ.get("NATS_URL", "nats://nats:4222")
SUBJECT_PREFIX = os.environ.get("SUBJECT_PREFIX", "fleet.gh")
STREAM_NAME = os.environ.get("STREAM_NAME", "FLEET")
STREAM_SUBJECTS = os.environ.get("STREAM_SUBJECTS", "fleet.>")
SECRET_FILE = os.environ.get("GITHUB_WEBHOOK_SECRET_FILE", "/run/secrets/github_webhook_secret")
SECRET_ENV = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
REPLAY_TTL = int(os.environ.get("REPLAY_TTL_SECONDS", "300"))


def _load_secret() -> bytes | None:
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "rb") as f:
            value = f.read().strip()
            return value or None
    return SECRET_ENV.encode() if SECRET_ENV else None


# Loaded once at module import; the entrypoint mounts the secret before serve.
SECRET = _load_secret()
# delivery-id → epoch-seconds. Bounded by the GC pass on every request.
_SEEN: dict[str, float] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.nc = await nats.connect(NATS_URL)
    js = app.state.nc.jetstream()
    # Auto-create the stream so events are durable + replayable. Idempotent —
    # add_stream errors with "stream already exists" on re-entry, which we swallow.
    try:
        await js.add_stream(name=STREAM_NAME, subjects=[STREAM_SUBJECTS])
    except Exception:
        pass
    app.state.js = js
    try:
        yield
    finally:
        await app.state.nc.drain()


app = FastAPI(title="AgentArmy webhook receiver", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "nats": NATS_URL}


def _gc_replay() -> None:
    now = time.time()
    for k in list(_SEEN):
        if now - _SEEN[k] > REPLAY_TTL:
            _SEEN.pop(k, None)


@app.post("/webhooks/github")
async def github(
    req: Request,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
    x_github_delivery: str = Header(default=""),
):
    if SECRET is None:
        # Fail closed — never accept unsigned input.
        raise HTTPException(500, "GITHUB_WEBHOOK_SECRET (or _FILE) not configured")
    body = await req.body()
    expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_hub_signature_256):
        raise HTTPException(401, "bad signature")

    # Replay protection.
    _gc_replay()
    if x_github_delivery and x_github_delivery in _SEEN:
        return JSONResponse({"status": "duplicate", "delivery": x_github_delivery}, status_code=200)
    if x_github_delivery:
        _SEEN[x_github_delivery] = time.time()

    # CloudEvents v1.0 envelope. The original body is the `data`.
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        data = {"raw": body.decode("latin-1", errors="replace")}

    event_type = f"github.{x_github_event or 'unknown'}"
    cloudevent = {
        "specversion": "1.0",
        "id": x_github_delivery or str(uuid4()),
        "source": "https://github.com/webhook",
        "type": event_type,
        "datacontenttype": "application/json",
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": data,
    }
    subject = f"{SUBJECT_PREFIX}.{x_github_event or 'unknown'}"
    ack = await req.app.state.js.publish(subject, json.dumps(cloudevent).encode("utf-8"))
    return JSONResponse(
        {
            "status": "published",
            "subject": subject,
            "id": cloudevent["id"],
            "type": event_type,
            "stream": ack.stream,
            "seq": ack.seq,
        },
        status_code=202,
    )
