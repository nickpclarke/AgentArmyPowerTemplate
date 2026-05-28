"""BPMN 2.0 XML → IR Graph.

Covers the runbook-relevant subset: start/end events (none/message/timer/signal),
service/script/user/manual/send/receive tasks, exclusive + parallel gateways,
intermediate catch events, and call activities. Sequence flows are resolved onto
the IR Node routing fields so the kernel never re-reads the XML.

XML is parsed with defusedxml when available (XXE / billion-laughs hardening for
untrusted runbook files); a stdlib fallback keeps the kernel runnable in a bare
dev environment. The container always ships defusedxml.
"""
from __future__ import annotations

try:  # hardened parser for untrusted input — the container default
    from defusedxml import ElementTree as ET
    SAFE_XML = True
except ImportError:  # dev fallback only
    import xml.etree.ElementTree as ET  # noqa: S405
    SAFE_XML = False

from ir import Command, Graph, Node, NodeKind

_TASK_KINDS = {"task", "serviceTask", "scriptTask", "userTask",
               "manualTask", "sendTask", "businessRuleTask"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_text(text: str) -> Graph:
    return parse_root(ET.fromstring(text))


def parse_root(root) -> Graph:
    messages = {el.get("id"): el.get("name", el.get("id"))
                for el in root.iter() if _local(el.tag) == "message"}

    process = next((c for c in root if _local(c.tag) == "process"), None)
    if process is None:
        raise ValueError("BPMN: no <process> element found")

    flows: dict[str, tuple] = {}      # flow id -> (source, target, condition)
    elements: dict[str, object] = {}  # element id -> xml element
    for el in process:
        ln = _local(el.tag)
        if ln == "sequenceFlow":
            cond = None
            for sub in el:
                if _local(sub.tag) == "conditionExpression":
                    cond = (sub.text or "").strip() or None
            flows[el.get("id")] = (el.get("sourceRef"), el.get("targetRef"), cond)
        elif el.get("id"):
            elements[el.get("id")] = el

    outgoing: dict[str, list[str]] = {}
    incoming: dict[str, list[str]] = {}
    for fid, (src, tgt, _c) in flows.items():
        outgoing.setdefault(src, []).append(fid)
        incoming.setdefault(tgt, []).append(fid)

    def single_target(node_id: str) -> str | None:
        fl = outgoing.get(node_id, [])
        return flows[fl[0]][1] if len(fl) >= 1 else None

    nodes: dict[str, Node] = {}
    splits: list[str] = []
    joins: list[str] = []
    start_id = ""

    for eid, el in elements.items():
        ln = _local(el.tag)
        name = el.get("name", "")

        if ln == "startEvent":
            nodes[eid] = Node(eid, NodeKind.START, name,
                              on_completion=single_target(eid),
                              trigger=_event_trigger(el, messages),
                              raw={"tag": ln})
            if not start_id or nodes[eid].trigger.get("kind") == "message":
                start_id = eid

        elif ln == "endEvent":
            nodes[eid] = Node(eid, NodeKind.END, name, raw={"tag": ln})

        elif ln in _TASK_KINDS:
            nodes[eid] = Node(eid, NodeKind.ACTION, name,
                              commands=_task_commands(el, name),
                              on_completion=single_target(eid),
                              raw={"tag": ln})

        elif ln == "receiveTask":
            nodes[eid] = Node(eid, NodeKind.CATCH_EVENT, name,
                              on_completion=single_target(eid),
                              trigger={"kind": "message", "name": name},
                              raw={"tag": ln})

        elif ln == "intermediateCatchEvent":
            nodes[eid] = Node(eid, NodeKind.CATCH_EVENT, name,
                              on_completion=single_target(eid),
                              trigger=_event_trigger(el, messages),
                              raw={"tag": ln})

        elif ln in ("exclusiveGateway", "inclusiveGateway"):
            branches = []
            default_flow = el.get("default")
            default_target = None
            for fid in outgoing.get(eid, []):
                src, tgt, cond = flows[fid]
                if fid == default_flow:
                    default_target = tgt
                elif cond:
                    branches.append({"condition": cond, "condition_lang": "juel", "target": tgt})
                else:
                    # Unconditional non-default flow: treat as the fallback.
                    default_target = default_target or tgt
            nodes[eid] = Node(eid, NodeKind.DECISION, name,
                              decision_type="exclusive",
                              branches=branches,
                              default_target=default_target,
                              raw={"tag": ln})

        elif ln == "parallelGateway":
            outs = [flows[f][1] for f in outgoing.get(eid, [])]
            node = Node(eid, NodeKind.PARALLEL, name, raw={"tag": ln})
            if len(outs) > 1:
                node.next_steps = outs
                splits.append(eid)
            else:
                node.on_completion = single_target(eid)
                if len(incoming.get(eid, [])) > 1:
                    joins.append(eid)
            nodes[eid] = node

        elif ln == "callActivity":
            nodes[eid] = Node(eid, NodeKind.CALL, name,
                              call_ref=el.get("calledElement"),
                              on_completion=single_target(eid),
                              raw={"tag": ln})

    # Pair a single split with a single join (the common diamond). Multi-join
    # graphs are a documented v1 limitation.
    if len(joins) == 1:
        for sid in splits:
            nodes[sid].join_id = joins[0]

    if not start_id:
        raise ValueError("BPMN: no startEvent found")

    return Graph(id=process.get("id", root.get("id", "")),
                 name=process.get("name", ""),
                 source_format="bpmn",
                 start_id=start_id,
                 nodes=nodes,
                 raw={"messages": messages})


def _task_commands(el, name: str) -> list[Command]:
    ln = _local(el.tag)
    if ln in ("userTask", "manualTask"):
        return [Command(type="manual", command=name or el.get("id", ""))]
    if ln == "scriptTask":
        script = ""
        for sub in el:
            if _local(sub.tag) == "script":
                script = (sub.text or "").strip()
        fmt = el.get("scriptFormat", "bash").lower()
        cmd_type = "powershell" if "powershell" in fmt else "bash"
        return [Command(type=cmd_type, command=script or name)]
    # serviceTask / sendTask / task / businessRuleTask → observable event
    impl = el.get("implementation", "")
    return [Command(type="emit-event", command=name or impl or el.get("id", ""))]


def _event_trigger(el, messages: dict) -> dict:
    for sub in el:
        ln = _local(sub.tag)
        if ln == "messageEventDefinition":
            ref = sub.get("messageRef")
            return {"kind": "message", "name": messages.get(ref, ref), "ref": ref}
        if ln == "timerEventDefinition":
            spec = {_local(t.tag): (t.text or "").strip() for t in sub}
            return {"kind": "timer", **spec}
        if ln == "signalEventDefinition":
            return {"kind": "signal", "ref": sub.get("signalRef")}
    return {"kind": "none"}
