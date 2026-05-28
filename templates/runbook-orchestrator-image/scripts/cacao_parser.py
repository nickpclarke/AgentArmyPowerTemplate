"""OASIS CACAO 2.0 security-playbook JSON → IR Graph.

CACAO navigates by identifier references inside each step (on_completion,
on_success/on_failure, on_true/on_false, cases, next_steps). We normalize those
straight onto the IR Node routing fields; no edge objects are synthesized.
Spec: https://docs.oasis-open.org/cacao/security-playbooks/v2.0/
"""
from __future__ import annotations

import json

from ir import Command, Graph, Node, NodeKind


def parse_text(text: str) -> Graph:
    return parse_obj(json.loads(text))


def parse_obj(obj: dict) -> Graph:
    workflow = obj.get("workflow", {}) or {}
    graph = Graph(
        id=obj.get("id", ""),
        name=obj.get("name", ""),
        source_format="cacao",
        start_id=obj.get("workflow_start", ""),
        raw=obj,
    )
    for step_id, step in workflow.items():
        graph.nodes[step_id] = _step_to_node(step_id, step or {})
    return graph


def _step_to_node(step_id: str, step: dict) -> Node:
    step_type = step.get("type")
    name = step.get("name", "")

    if step_type == "start":
        return Node(step_id, NodeKind.START, name,
                    on_completion=step.get("on_completion"),
                    trigger=_trigger(step), raw=step)

    if step_type == "end":
        return Node(step_id, NodeKind.END, name, raw=step)

    if step_type == "action":
        commands = [
            Command(type=c.get("type", ""), command=c.get("command", ""), raw=c)
            for c in step.get("commands", []) or []
        ]
        return Node(step_id, NodeKind.ACTION, name,
                    commands=commands,
                    agent=step.get("agent"),
                    targets=list(step.get("targets", []) or []),
                    on_completion=step.get("on_completion"),
                    on_success=step.get("on_success"),
                    on_failure=step.get("on_failure"),
                    delay_ms=int(step.get("delay", 0) or 0),
                    raw=step)

    if step_type == "if-condition":
        return Node(step_id, NodeKind.DECISION, name,
                    decision_type="if",
                    condition=step.get("condition"),
                    condition_lang="stix",
                    on_true=step.get("on_true"),
                    on_false=step.get("on_false"),
                    on_completion=step.get("on_completion"),
                    raw=step)

    if step_type == "while-condition":
        return Node(step_id, NodeKind.DECISION, name,
                    decision_type="while",
                    condition=step.get("condition"),
                    condition_lang="stix",
                    on_true=step.get("on_true"),
                    on_completion=step.get("on_completion"),
                    raw=step)

    if step_type == "switch-condition":
        return Node(step_id, NodeKind.DECISION, name,
                    decision_type="switch",
                    switch_var=step.get("switch"),
                    cases=dict(step.get("cases", {}) or {}),
                    on_completion=step.get("on_completion"),
                    raw=step)

    if step_type == "parallel":
        return Node(step_id, NodeKind.PARALLEL, name,
                    next_steps=list(step.get("next_steps", []) or []),
                    on_completion=step.get("on_completion"),
                    raw=step)

    if step_type == "playbook-action":
        return Node(step_id, NodeKind.CALL, name,
                    call_ref=step.get("playbook_id"),
                    on_completion=step.get("on_completion"),
                    on_success=step.get("on_success"),
                    on_failure=step.get("on_failure"),
                    raw=step)

    # Unknown / extension step type — treat as an opaque pass-through action.
    return Node(step_id, NodeKind.ACTION, name or (step_type or "unknown"),
                on_completion=step.get("on_completion"), raw=step)


def _trigger(step: dict) -> dict:
    """A CACAO start step has no native trigger grammar. We let authors opt in
    via a non-normative `step_extensions.trigger` block so the serve-mode
    dispatcher can subscribe a playbook to a `fleet.*` subject."""
    ext = step.get("step_extensions", {}) or {}
    trig = ext.get("trigger")
    if isinstance(trig, dict):
        return trig
    return {"kind": "none"}
