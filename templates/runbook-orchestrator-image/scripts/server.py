"""Serve mode — the isolated helper that responds to runbook events and triggers.

Indexes RUNBOOK_DIR, subscribes each event-triggered runbook to its `fleet.*`
subject on NATS JetStream, and runs the matching runbook when a CloudEvent
arrives. Also exposes a tiny control API. NATS is optional: with no reachable
broker the helper still serves the control API and manual triggers, so it
degrades to a fully standalone, file-only worker.

Endpoints:
  GET  /healthz                       liveness + index summary
  GET  /runbooks                      list indexed runbooks (id, trigger, validity)
  POST /runbooks/{runbook_id}/trigger run a runbook now; JSON body = context
"""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from runbook_engine import Engine, SafeExecutor
from triggers import RunbookIndex

RUNBOOK_DIR = os.environ.get("RUNBOOK_DIR", "/runbooks")
NATS_URL = os.environ.get("NATS_URL", "nats://nats:4222")
STREAM_NAME = os.environ.get("STREAM_NAME", "FLEET")
STREAM_SUBJECTS = os.environ.get("STREAM_SUBJECTS", "fleet.>")
RESULT_SUBJECT = os.environ.get("RESULT_SUBJECT", "fleet.runbook.completed")
COMMAND_SUBJECT = os.environ.get("COMMAND_SUBJECT", "fleet.runbook.command")


def _cloudevent(event_type: str, data: dict) -> dict:
    return {
        "specversion": "1.0",
        "id": str(uuid4()),
        "source": "https://agentarmy.dev/runbook-orchestrator",
        "type": event_type,
        "datacontenttype": "application/json",
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": data,
    }


def _spawn(app: FastAPI, coro) -> None:
    """Fire-and-forget a coroutine, holding a reference so it isn't GC'd."""
    task = asyncio.ensure_future(coro)
    app.state.tasks.add(task)
    task.add_done_callback(app.state.tasks.discard)


def _publish(app: FastAPI, subject: str, data: dict) -> None:
    js = getattr(app.state, "js", None)
    if js is not None:
        _spawn(app, js.publish(subject, json.dumps(_cloudevent(subject, data)).encode()))


def run_entry(app: FastAPI, entry, context: dict) -> dict:
    executor = SafeExecutor(emit=lambda _t, data: _publish(app, COMMAND_SUBJECT, data))
    result = Engine(executor=executor).run(entry.graph, context)
    summary = {"runbook": entry.id, "name": entry.name, "format": entry.format,
               "status": result.status, "steps": len(result.trace),
               "error": result.error}
    _publish(app, RESULT_SUBJECT, summary)
    return summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.tasks = set()
    index = RunbookIndex(RUNBOOK_DIR)
    index.reload()
    app.state.index = index
    app.state.subjects = index.by_subject()
    app.state.nc = None
    app.state.js = None

    async def on_event(msg):
        try:
            payload = json.loads(msg.data.decode())
            context = payload.get("data", payload) if isinstance(payload, dict) else {}
        except Exception:  # noqa: BLE001
            context = {}
        for entry in app.state.subjects.get(msg.subject, []):
            run_entry(app, entry, context if isinstance(context, dict) else {})
        await msg.ack()

    try:
        import nats
        app.state.nc = await nats.connect(NATS_URL, connect_timeout=3)
        js = app.state.nc.jetstream()
        try:
            await js.add_stream(name=STREAM_NAME, subjects=[STREAM_SUBJECTS])
        except Exception:  # noqa: BLE001 — stream already exists
            pass
        app.state.js = js
        for subject in app.state.subjects:
            await js.subscribe(subject, cb=on_event,
                               durable=f"runbook-{subject.replace('.', '-')}")
    except Exception as exc:  # noqa: BLE001 — degrade to control-API-only
        print(json.dumps({"event": "nats.unavailable", "detail": str(exc)}), flush=True)

    try:
        yield
    finally:
        if app.state.nc is not None:
            await app.state.nc.drain()


app = FastAPI(title="AgentArmy runbook orchestrator", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "runbooks": len(app.state.index.entries),
            "subscribed_subjects": list(app.state.subjects.keys()),
            "nats": NATS_URL if app.state.js is not None else None}


@app.get("/runbooks")
def list_runbooks() -> dict:
    return {"runbooks": [e.summary() for e in app.state.index.entries]}


@app.post("/runbooks/{runbook_id}/trigger")
async def trigger(runbook_id: str, req: Request) -> JSONResponse:
    entry = app.state.index.find(runbook_id)
    if entry is None:
        raise HTTPException(404, f"unknown runbook '{runbook_id}'")
    if not entry.valid:
        raise HTTPException(422, {"errors": entry.errors})
    try:
        context = await req.json()
    except Exception:  # noqa: BLE001 — empty / non-JSON body
        context = {}
    summary = run_entry(app, entry, context if isinstance(context, dict) else {})
    return JSONResponse(summary, status_code=200)
