"""Structural validators for CACAO 2.0 and BPMN 2.0 runbook files.

These are pre-flight checks (not full schema validation): they catch the
mistakes that would make a file unrunnable or ambiguous, mirroring the
conformance rules in the OASIS CACAO 2.0 spec and the BPMN runbook subset.
Each validator returns a list of human-readable error strings (empty = valid).
"""
from __future__ import annotations

import re

ID_RE = re.compile(
    r"^[a-z][a-z0-9-]*--[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

_CONTINUATION = ("on_completion", "on_success", "on_failure")


def validate_cacao(obj: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return ["not a JSON object"]

    if obj.get("type") != "playbook":
        errs.append('type must be "playbook"')
    if obj.get("spec_version") != "cacao-2.0":
        errs.append('spec_version must be "cacao-2.0"')

    for key in ("id", "name", "created_by", "created", "modified",
                "workflow_start", "workflow"):
        if key not in obj:
            errs.append(f"missing required property: {key}")

    for key in ("created", "modified"):
        val = obj.get(key)
        if isinstance(val, str) and not TS_RE.match(val):
            errs.append(f"{key} is not millisecond-precision UTC (…T…:…:…​.000Z): {val}")

    workflow = obj.get("workflow")
    start = obj.get("workflow_start")
    if not isinstance(workflow, dict):
        errs.append("workflow must be an object")
        return errs

    if start is not None:
        if start not in workflow:
            errs.append(f"workflow_start '{start}' is not a key in workflow")
        elif workflow[start].get("type") != "start":
            errs.append(f"workflow_start '{start}' does not reference a start step")

    agents = obj.get("agent_definitions", {}) or {}
    targets = obj.get("target_definitions", {}) or {}
    for step_id, step in workflow.items():
        errs += _validate_cacao_step(step_id, step or {}, workflow, agents, targets)

    return errs


def _validate_cacao_step(step_id, step, workflow, agents, targets) -> list[str]:
    errs: list[str] = []
    where = f"step '{step_id}'"
    step_type = step.get("type")

    if step_type is None:
        errs.append(f"{where}: missing type")
        return errs

    has_completion = "on_completion" in step
    has_outcome = "on_success" in step or "on_failure" in step
    if has_completion and has_outcome:
        errs.append(f"{where}: on_completion is mutually exclusive with on_success/on_failure")

    if step_type == "start" and has_outcome:
        errs.append(f"{where}: start step must not define on_success/on_failure")
    if step_type == "end" and (has_completion or has_outcome):
        errs.append(f"{where}: end step must not define any continuation")

    if step_type == "action":
        if not step.get("commands"):
            errs.append(f"{where}: action step requires a non-empty commands list")
        if not step.get("agent"):
            errs.append(f"{where}: action step requires an agent")
    elif step_type == "parallel":
        if len(step.get("next_steps", []) or []) < 2:
            errs.append(f"{where}: parallel step requires >= 2 next_steps")
    elif step_type in ("if-condition", "while-condition"):
        if not step.get("condition"):
            errs.append(f"{where}: {step_type} requires a condition")
        if not step.get("on_true"):
            errs.append(f"{where}: {step_type} requires on_true")
    elif step_type == "switch-condition":
        if not step.get("switch"):
            errs.append(f"{where}: switch-condition requires a switch variable")
        if not step.get("cases"):
            errs.append(f"{where}: switch-condition requires a non-empty cases map")

    # Reference resolution.
    refs = []
    for key in _CONTINUATION + ("on_true", "on_false"):
        if step.get(key):
            refs.append((key, step[key]))
    for value in (step.get("cases", {}) or {}).values():
        refs.append(("cases", value))
    for value in (step.get("next_steps", []) or []):
        refs.append(("next_steps", value))
    for key, ref in refs:
        if ref not in workflow:
            errs.append(f"{where}: {key} references unknown step '{ref}'")

    if step_type == "action":
        if step.get("agent") and step["agent"] not in agents:
            errs.append(f"{where}: agent '{step['agent']}' not in agent_definitions")
        for tgt in step.get("targets", []) or []:
            if tgt not in targets:
                errs.append(f"{where}: target '{tgt}' not in target_definitions")

    return errs


def validate_bpmn(text: str) -> list[str]:
    try:
        from bpmn_parser import ET, _local  # reuse the hardened parser
    except Exception as exc:  # pragma: no cover
        return [f"BPMN parser unavailable: {exc}"]

    errs: list[str] = []
    try:
        root = ET.fromstring(text)
    except Exception as exc:
        return [f"invalid XML: {exc}"]

    process = next((c for c in root if _local(c.tag) == "process"), None)
    if process is None:
        return ["no <process> element found"]

    ids: set[str] = set()
    flows = []
    starts = 0
    gateways = {}
    for el in process:
        ln = _local(el.tag)
        if el.get("id"):
            ids.add(el.get("id"))
        if ln == "startEvent":
            starts += 1
        elif ln == "sequenceFlow":
            flows.append((el.get("id"), el.get("sourceRef"), el.get("targetRef")))
        elif ln in ("exclusiveGateway", "inclusiveGateway"):
            gateways[el.get("id")] = el.get("default")

    if starts == 0:
        errs.append("process has no startEvent")

    for fid, src, tgt in flows:
        if src not in ids:
            errs.append(f"sequenceFlow '{fid}' sourceRef '{src}' does not resolve")
        if tgt not in ids:
            errs.append(f"sequenceFlow '{fid}' targetRef '{tgt}' does not resolve")

    flow_ids = {f[0] for f in flows}
    for gw, default in gateways.items():
        if default and default not in flow_ids:
            errs.append(f"gateway '{gw}' default '{default}' is not a sequenceFlow id")

    return errs
