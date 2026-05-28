"""Intermediate representation shared by the BPMN and CACAO parsers.

Both runbook formats are parsed into this one annotated directed graph so a
single execution kernel (runbook_engine.Engine) can drive either format. Only
the parsers and the condition evaluators are format-specific; the kernel sees
nothing but Node / Graph. See docs/runbook-orchestrator.md for the mapping.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeKind(str, Enum):
    START = "start"
    END = "end"
    ACTION = "action"
    DECISION = "decision"   # bpmn exclusiveGateway / cacao if|while|switch
    PARALLEL = "parallel"   # bpmn parallelGateway / cacao parallel
    CATCH_EVENT = "catch_event"  # bpmn intermediateCatchEvent / receiveTask
    CALL = "call"           # bpmn callActivity / cacao playbook-action


@dataclass
class Command:
    """A single command on an ACTION node (CACAO command / BPMN task body)."""
    type: str
    command: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class Node:
    id: str
    kind: NodeKind
    name: str = ""

    # Unconditional / outcome routing (normalized from both formats).
    on_completion: str | None = None
    on_success: str | None = None
    on_failure: str | None = None

    # ACTION
    commands: list[Command] = field(default_factory=list)
    agent: str | None = None
    targets: list[str] = field(default_factory=list)

    # DECISION
    decision_type: str | None = None        # "if" | "while" | "switch" | "exclusive"
    condition: str | None = None
    condition_lang: str | None = None       # "stix" | "juel"
    on_true: str | None = None
    on_false: str | None = None
    switch_var: str | None = None
    cases: dict[str, str] = field(default_factory=dict)
    # BPMN exclusive gateway: ordered [{condition, condition_lang, target}]
    branches: list[dict] = field(default_factory=list)
    default_target: str | None = None

    # PARALLEL
    next_steps: list[str] = field(default_factory=list)
    join_id: str | None = None              # BPMN join gateway paired to this split

    # CALL
    call_ref: str | None = None

    # START / CATCH_EVENT trigger metadata
    trigger: dict | None = None             # {"kind": "message|timer|signal|none", ...}
    delay_ms: int = 0

    raw: dict = field(default_factory=dict)


@dataclass
class Graph:
    id: str
    name: str
    source_format: str                      # "bpmn" | "cacao"
    start_id: str
    nodes: dict[str, Node] = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    def node(self, nid: str | None) -> Node | None:
        return self.nodes.get(nid) if nid else None

    @property
    def start_trigger(self) -> dict | None:
        start = self.nodes.get(self.start_id)
        return start.trigger if start else None
