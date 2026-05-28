"""Runbook execution kernel + safe command executor + CLI.

One kernel runs the IR graph produced by either parser. The default executor is
a *safe orchestrator*: it never blindly runs ssh/bash/powershell. Instead it
emits observable CloudEvents for api/event commands, requires HITL acknowledgement
for manual steps, and dry-runs shell commands (logging what *would* run). Real
shell execution is a deliberately deferred, opt-in capability.

CLI:
  python runbook_engine.py validate <file>
  python runbook_engine.py run <file> [context.json]
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field

import bpmn_parser
import cacao_parser
import validators
from ir import Graph, Node, NodeKind

MAX_STEPS = 1000  # global guard against runaway loops / cycles


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def detect_format(path: str, text: str) -> str:
    head = text.lstrip()[:64]
    if path.endswith((".bpmn", ".xml")) or head.startswith("<"):
        return "bpmn"
    if path.endswith(".json") or head.startswith("{"):
        return "cacao"
    raise ValueError(f"cannot determine runbook format for {path}")


def load(path: str) -> Graph:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    fmt = detect_format(path, text)
    return bpmn_parser.parse_text(text) if fmt == "bpmn" else cacao_parser.parse_text(text)


def validate_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    fmt = detect_format(path, text)
    if fmt == "bpmn":
        return validators.validate_bpmn(text)
    return validators.validate_cacao(json.loads(text))


# --------------------------------------------------------------------------- #
# Condition evaluation (subset, per format — never eval())
# --------------------------------------------------------------------------- #
_OPS = {
    "==": lambda a, b: a == b, "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">=": lambda a, b: _num(a) >= _num(b), "<=": lambda a, b: _num(a) <= _num(b),
    ">": lambda a, b: _num(a) > _num(b), "<": lambda a, b: _num(a) < _num(b),
}
# juel/feel: ${ var OP literal } ; stix: var:path OP literal  (subset)
_JUEL_RE = re.compile(r"\$?\{?\s*([\w.]+)\s*(==|!=|>=|<=|>|<)\s*(.+?)\s*\}?$")
_STIX_RE = re.compile(r"\[?\s*([\w:.\-]+)\s*(=|!=|>=|<=|>|<)\s*(.+?)\s*\]?$")


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _unquote(token: str):
    token = token.strip()
    if len(token) >= 2 and token[0] in "'\"" and token[-1] == token[0]:
        return token[1:-1]
    if token.lower() in ("true", "false"):
        return token.lower() == "true"
    return token


def eval_condition(expr: str | None, lang: str | None, context: dict) -> bool:
    if not expr:
        return False
    pattern = _STIX_RE if lang == "stix" else _JUEL_RE
    match = pattern.match(expr.strip())
    if not match:
        return False
    var, op, literal = match.group(1), match.group(2), _unquote(match.group(3))
    # stix variable refs look like __name__:value or object:prop — take the head token.
    var = var.lstrip("_").split(":")[0].split(".")[0].rstrip("_")
    actual = context.get(var)
    fn = _OPS.get(op)
    if fn is None:
        return False
    if op in (">", "<", ">=", "<="):
        return bool(fn(actual, literal))
    if _is_numeric(actual) and _is_numeric(literal):
        return bool(fn(_num(actual), _num(literal)))
    return bool(fn(str(actual), str(literal)))


def _is_numeric(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------- #
# Safe executor
# --------------------------------------------------------------------------- #
_DRY_RUN_TYPES = {"ssh", "bash", "powershell", "openc2-http", "sigma", "yara",
                  "caldera-cmd", "kestrel", "elastic", "jupyter-notebook"}
_EMIT_TYPES = {"http-api", "emit-event"}


class SafeExecutor:
    """The safe-orchestrator posture (ARC-ADR-031): observe, don't detonate."""

    def __init__(self, emit=None, allow_exec: bool = False):
        self.emit = emit  # callable(event_type: str, data: dict) | None
        self.allow_exec = allow_exec

    def execute(self, node: Node, context: dict) -> tuple[bool, list[dict]]:
        results = []
        ok = True
        for cmd in node.commands:
            res = self._run_command(node, cmd, context)
            results.append(res)
            if not res.get("ok", True):
                ok = False
        return ok, results

    def _run_command(self, node: Node, cmd, context: dict) -> dict:
        base = {"command_type": cmd.type, "command": cmd.command}
        if cmd.type == "manual":
            return {**base, "action": "manual-ack-required", "hitl": True, "ok": True}
        if cmd.type in _EMIT_TYPES:
            event = {"step": node.id, "agent": node.agent,
                     "targets": node.targets, **base}
            if self.emit:
                self.emit("fleet.runbook.command", event)
            return {**base, "action": "emitted-event", "ok": True}
        if cmd.type in _DRY_RUN_TYPES:
            if self.allow_exec:
                # Real execution is deliberately not implemented in v1 — fall back
                # to dry-run rather than ship a half-built remote-exec path.
                return {**base, "action": "dry-run (real-exec deferred)",
                        "would_execute": True, "ok": True}
            return {**base, "action": "dry-run", "would_execute": True, "ok": True}
        return {**base, "action": "dry-run (unknown type)", "ok": True}


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
@dataclass
class RunResult:
    status: str                       # "completed" | "error"
    trace: list[dict] = field(default_factory=list)
    error: str | None = None


class Engine:
    def __init__(self, executor: SafeExecutor | None = None, logger=None):
        self.executor = executor or SafeExecutor()
        self.logger = logger or (lambda rec: print(json.dumps(rec), flush=True))
        self._steps = 0

    def run(self, graph: Graph, context: dict | None = None) -> RunResult:
        context = dict(context or {})
        self._steps = 0
        result = RunResult(status="completed")
        try:
            self._run_segment(graph, graph.start_id, set(), context, result)
        except Exception as exc:  # noqa: BLE001 — surface any kernel fault as a run error
            result.status = "error"
            result.error = str(exc)
            self._emit(result, {"event": "run.error", "error": str(exc)})
        return result

    def _run_segment(self, graph, current, stop_ids, context, result) -> str | None:
        """Run from `current` until reaching a node in `stop_ids`, an END, or a
        dead end. Returns the node id it stopped at (or None)."""
        while current is not None and current not in stop_ids:
            self._steps += 1
            if self._steps > MAX_STEPS:
                raise RuntimeError(f"step budget {MAX_STEPS} exceeded (cycle?)")
            node = graph.node(current)
            if node is None:
                raise RuntimeError(f"dangling reference to step '{current}'")
            current = self._step(graph, node, stop_ids, context, result)
        return current

    def _step(self, graph, node: Node, stop_ids, context, result) -> str | None:
        if node.kind == NodeKind.END:
            self._emit(result, {"event": "step.end", "id": node.id, "name": node.name})
            return None

        if node.kind == NodeKind.START:
            self._emit(result, {"event": "step.start", "id": node.id,
                                 "trigger": node.trigger})
            return node.on_completion

        if node.kind == NodeKind.ACTION:
            ok, cmd_results = self.executor.execute(node, context)
            self._emit(result, {"event": "step.action", "id": node.id,
                                 "name": node.name, "ok": ok, "commands": cmd_results})
            return self._next_after(node, ok)

        if node.kind == NodeKind.CATCH_EVENT:
            # In a one-shot run we can't block on an external trigger; record the
            # wait and pass through. Serve mode handles real correlation upstream.
            self._emit(result, {"event": "step.wait", "id": node.id,
                                 "trigger": node.trigger})
            return node.on_completion

        if node.kind == NodeKind.CALL:
            self._emit(result, {"event": "step.call", "id": node.id,
                                 "playbook": node.call_ref})
            return node.on_completion

        if node.kind == NodeKind.DECISION:
            return self._decide(node, context, result)

        if node.kind == NodeKind.PARALLEL:
            return self._parallel(graph, node, stop_ids, context, result)

        raise RuntimeError(f"unknown node kind: {node.kind}")

    def _next_after(self, node: Node, ok: bool) -> str | None:
        if node.on_success is not None or node.on_failure is not None:
            chosen = node.on_success if ok else node.on_failure
            return chosen if chosen is not None else node.on_completion
        return node.on_completion

    def _decide(self, node: Node, context, result) -> str | None:
        dt = node.decision_type
        if dt == "switch":
            value = str(context.get(node.switch_var))
            target = node.cases.get(value) or node.cases.get("default")
            self._emit(result, {"event": "step.switch", "id": node.id,
                                 "value": value, "target": target})
            return target
        if dt == "exclusive":
            for branch in node.branches:
                if eval_condition(branch["condition"], branch.get("condition_lang"), context):
                    self._emit(result, {"event": "step.gateway", "id": node.id,
                                         "matched": branch["condition"],
                                         "target": branch["target"]})
                    return branch["target"]
            self._emit(result, {"event": "step.gateway", "id": node.id,
                                 "matched": "default", "target": node.default_target})
            return node.default_target
        # if / while
        truth = eval_condition(node.condition, node.condition_lang, context)
        self._emit(result, {"event": f"step.{dt}", "id": node.id, "result": truth})
        if dt == "while":
            return node.on_true if truth else node.on_completion
        return node.on_true if truth else node.on_false

    def _parallel(self, graph, node: Node, stop_ids, context, result) -> str | None:
        # BPMN split paired to a join gateway; CACAO converges at on_completion.
        continuation = (graph.node(node.join_id).on_completion
                        if node.join_id else node.on_completion)
        branch_stop = set(stop_ids)
        if node.join_id:
            branch_stop.add(node.join_id)
        elif continuation:
            branch_stop.add(continuation)
        self._emit(result, {"event": "step.parallel", "id": node.id,
                             "branches": node.next_steps})
        for branch in node.next_steps:
            self._run_segment(graph, branch, branch_stop, context, result)
        return continuation

    def _emit(self, result: RunResult, record: dict) -> None:
        result.trace.append(record)
        self.logger(record)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: runbook_engine.py {validate|run} <file> [context.json]", file=sys.stderr)
        return 2
    command, path = argv[0], argv[1]

    if command == "validate":
        errors = validate_file(path)
        if errors:
            print(f"INVALID: {path}", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1
        print(f"VALID: {path}")
        return 0

    if command == "run":
        context = {}
        if len(argv) >= 3:
            with open(argv[2], "r", encoding="utf-8") as fh:
                context = json.load(fh)
        graph = load(path)
        result = Engine().run(graph, context)
        summary = {"event": "run.summary", "runbook": graph.id or path,
                   "format": graph.source_format, "status": result.status,
                   "steps": len(result.trace), "error": result.error}
        print(json.dumps(summary), flush=True)
        return 0 if result.status == "completed" else 1

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
