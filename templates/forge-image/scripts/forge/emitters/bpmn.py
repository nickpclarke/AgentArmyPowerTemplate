"""forge IR → BPMN 2.0 XML (one file per Process).

Emits the runbook-orchestrator kernel's BPMN dialect (ARC-ADR-031 / ARC-ADR-038 §process):
a process modeled in the ontology IR compiles to an artifact the kernel parses and executes.
The output is validated against the kernel's own validate_bpmn — see tests/bpmn_emit_check.py.

Determinism (load-bearing for the byte-identical doctor): steps in declared order, flows in a
stable order, no timestamps, UTF-8 + LF, single trailing LF.
"""
from __future__ import annotations

import os
from xml.sax.saxutils import escape, quoteattr

from ..ir import Model, Process, ProcessStep

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
TARGET_NS = "http://agentarmy.dev/ontology"
_START = "start"


def emit(model: Model, out_dir: str) -> list[str]:
    """Write one ``<process-id>.bpmn`` per Process. Returns the relative paths written
    (empty when the model declares no processes)."""
    os.makedirs(out_dir, exist_ok=True)
    written: list[str] = []
    for proc in sorted(model.processes, key=lambda p: p.id):
        rel = f"{proc.id}.bpmn"
        with open(os.path.join(out_dir, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(_render(proc))
        written.append(rel)
    return written


def _flow_id(source: str, target: str) -> str:
    return f"sf-{source}-{target}"


def _default_flow_id(step: ProcessStep) -> str | None:
    # For a decision, the last branch is the unconditional default.
    return _flow_id(step.name, step.next[-1]) if step.next else None


def _render(proc: Process) -> str:
    lines: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(
        f'<definitions xmlns="{BPMN_NS}" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        f'targetNamespace="{TARGET_NS}" id="def-{escape(proc.id)}">'
    )

    msg_id = f"msg-{proc.id}"
    if proc.trigger_kind == "message" and proc.trigger_subject:
        lines.append(f"  <message id={quoteattr(msg_id)} name={quoteattr(proc.trigger_subject)} />")

    lines.append(
        f"  <process id={quoteattr(proc.id)} name={quoteattr(proc.name)} isExecutable=\"true\">"
    )
    lines += _start_event(proc, msg_id)
    for step in proc.steps:
        lines += _step_element(step)
    lines += _flows(proc)
    lines.append("  </process>")
    lines.append("</definitions>")
    lines.append("")  # single trailing LF
    return "\n".join(lines)


def _start_event(proc: Process, msg_id: str) -> list[str]:
    name = proc.name or proc.id
    if proc.trigger_kind == "message" and proc.trigger_subject:
        return [
            f'    <startEvent id="{_START}" name={quoteattr(name)}>',
            f"      <messageEventDefinition messageRef={quoteattr(msg_id)} />",
            "    </startEvent>",
        ]
    if proc.trigger_kind == "timer" and proc.trigger_schedule:
        return [
            f'    <startEvent id="{_START}" name={quoteattr(name)}>',
            f"      <timerEventDefinition><timeCycle>{escape(proc.trigger_schedule)}</timeCycle></timerEventDefinition>",
            "    </startEvent>",
        ]
    return [f'    <startEvent id="{_START}" name={quoteattr(name)} />']


def _step_element(step: ProcessStep) -> list[str]:
    sid = quoteattr(step.name)
    nm = quoteattr(step.name)
    kind = step.kind
    if kind == "service":
        return [f'    <serviceTask id={sid} name={quoteattr(step.agent or step.name)} implementation="##WebService" />']
    if kind == "emit-event":
        return [f"    <serviceTask id={sid} name={quoteattr(step.subject or step.name)} />"]
    if kind == "manual":
        return [f"    <userTask id={sid} name={nm} />"]
    if kind == "wait":
        if step.timeout:
            return [
                f"    <intermediateCatchEvent id={sid} name={nm}>",
                f"      <timerEventDefinition><timeDuration>{escape(step.timeout)}</timeDuration></timerEventDefinition>",
                "    </intermediateCatchEvent>",
            ]
        return [
            f"    <intermediateCatchEvent id={sid} name={nm}>",
            "      <messageEventDefinition />",
            "    </intermediateCatchEvent>",
        ]
    if kind == "decision":
        default_flow = _default_flow_id(step)
        default_attr = f" default={quoteattr(default_flow)}" if default_flow else ""
        return [f"    <exclusiveGateway id={sid} name={nm}{default_attr} />"]
    if kind == "parallel":
        return [f"    <parallelGateway id={sid} name={nm} />"]
    if kind == "call":
        return [f"    <callActivity id={sid} name={nm} calledElement={quoteattr(step.calls or '')} />"]
    if kind == "end":
        return [f"    <endEvent id={sid} name={nm} />"]
    # Unknown kind → a generic task (the kernel turns it into an observable event).
    return [f"    <task id={sid} name={nm} />"]


def _flows(proc: Process) -> list[str]:
    steps = proc.steps
    if not steps:
        return []
    out: list[str] = []
    first = steps[0].name
    out.append(
        f"    <sequenceFlow id={quoteattr(_flow_id(_START, first))} "
        f'sourceRef="{_START}" targetRef={quoteattr(first)} />'
    )
    for i, step in enumerate(steps):
        if step.kind == "end":
            continue
        targets = list(step.next)
        if not targets and i + 1 < len(steps):
            targets = [steps[i + 1].name]
        for j, tgt in enumerate(targets):
            fid = quoteattr(_flow_id(step.name, tgt))
            conditional = (
                step.kind == "decision" and j == 0 and bool(step.condition) and len(targets) > 1
            )
            if conditional:
                out.append(
                    f"    <sequenceFlow id={fid} sourceRef={quoteattr(step.name)} targetRef={quoteattr(tgt)}>"
                )
                out.append(
                    f'      <conditionExpression xsi:type="tFormalExpression">{escape(step.condition or "")}</conditionExpression>'
                )
                out.append("    </sequenceFlow>")
            else:
                out.append(
                    f"    <sequenceFlow id={fid} sourceRef={quoteattr(step.name)} targetRef={quoteattr(tgt)} />"
                )
    return out
