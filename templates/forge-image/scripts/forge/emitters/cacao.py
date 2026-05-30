"""forge IR → OASIS CACAO 2.0 JSON playbook (one file per Process).

The second executable projection the runbook-orchestrator kernel runs (the first is BPMN).
CACAO has no timer / event-wait primitive, so `wait` steps project to a manual action — a
documented v1 limitation (ARC-ADR-031). Validated against the kernel's validate_cacao.

Determinism: a fixed generation timestamp + a uuid5 derived from the process id (no wall
clock, no randomness), sorted keys, UTF-8 + LF, single trailing LF.
"""
from __future__ import annotations

import json
import os
import uuid

from ..ir import Model, Process, ProcessStep

# Placeholder set at generation time (deterministic). A publish step stamps the real
# created/modified; the kernel only requires millisecond-UTC syntax here.
_GENERATED_TS = "2026-01-01T00:00:00.000Z"
_NS = uuid.NAMESPACE_URL
_DEFAULT_AGENT = "agentarmy-runtime"


def emit(model: Model, out_dir: str) -> list[str]:
    """Write one ``<process-id>.cacao.json`` per Process. Returns the relative paths written."""
    os.makedirs(out_dir, exist_ok=True)
    written: list[str] = []
    for proc in sorted(model.processes, key=lambda p: p.id):
        rel = f"{proc.id}.cacao.json"
        with open(os.path.join(out_dir, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(_playbook(proc), indent=2, sort_keys=True))
            fh.write("\n")
        written.append(rel)
    return written


def _uuid(seed: str) -> str:
    return str(uuid.uuid5(_NS, f"urn:agentarmy:{seed}"))


def _playbook(proc: Process) -> dict:
    steps = proc.steps
    workflow: dict[str, dict] = {"start": {"type": "start"}}
    if steps:
        workflow["start"]["on_completion"] = steps[0].name

    agents: dict[str, dict] = {}
    for i, step in enumerate(steps):
        nxt = list(step.next)
        seq = steps[i + 1].name if (not nxt and i + 1 < len(steps)) else None
        workflow[step.name] = _step(step, nxt, seq, agents)

    if not agents:
        agents[_DEFAULT_AGENT] = {"type": "agentarmy", "name": _DEFAULT_AGENT}

    return {
        "type": "playbook",
        "spec_version": "cacao-2.0",
        "id": f"playbook--{_uuid('process:' + proc.id)}",
        "name": proc.name or proc.id,
        "description": f"Generated from ontology process '{proc.id}' (ARC-ADR-038).",
        "created_by": f"identity--{_uuid('forge')}",
        "created": _GENERATED_TS,
        "modified": _GENERATED_TS,
        "workflow_start": "start",
        "workflow": workflow,
        "agent_definitions": agents,
    }


def _step(step: ProcessStep, nxt: list[str], seq: str | None, agents: dict) -> dict:
    kind = step.kind
    if kind in ("service", "emit-event", "manual", "wait"):
        agent = step.agent or _DEFAULT_AGENT
        agents.setdefault(agent, {"type": "agentarmy", "name": agent})
        cmd_type = "manual" if kind in ("manual", "wait") else "http-api"
        out: dict = {
            "type": "action",
            "commands": [{"type": cmd_type, "command": step.agent or step.subject or step.name}],
            "agent": agent,
        }
        target = nxt[0] if nxt else seq
        if target:
            out["on_completion"] = target
        return out
    if kind == "decision":
        out = {"type": "if-condition", "condition": step.condition or "true"}
        if nxt:
            out["on_true"] = nxt[0]
        if len(nxt) > 1:
            out["on_false"] = nxt[1]
        return out
    if kind == "parallel":
        return {"type": "parallel", "next_steps": nxt}
    if kind == "call":
        out = {"type": "playbook-action"}
        if step.calls:
            out["playbook_id"] = step.calls
        target = nxt[0] if nxt else seq
        if target:
            out["on_completion"] = target
        return out
    if kind == "end":
        return {"type": "end"}
    agents.setdefault(_DEFAULT_AGENT, {"type": "agentarmy", "name": _DEFAULT_AGENT})
    return {
        "type": "action",
        "commands": [{"type": "manual", "command": step.name}],
        "agent": _DEFAULT_AGENT,
    }
