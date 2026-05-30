"""Intermediate Representation — the schema parsers fill and emitters consume.

A deliberately small surface. The point of forge is that adding a new input
(YAML / Turtle / JSON-LD / N-Triples) only requires writing a parser to this
IR, and adding a new output language only requires writing an emitter that
reads from it. The IR is the source of architectural truth — keep it tight.

Determinism rules (load-bearing for the byte-identical doctor check):
  * All collections are sorted before serialization happens in emitters.
  * Field iteration order in emitters is the model's declared order — parsers
    MUST preserve the source order they observe (YAML mapping order via the
    standard pyyaml loader; RDF parsers sort URIs lexicographically since
    RDF has no native order).
  * `annotations` is a dict[str, str] — keys are sorted in emitters.

A model is a versioned bundle of object types. Object types have fields
(scalar attrs) and relations (links to other object types). Relations carry
cardinality + inverse name so emitters can produce bidirectional projections.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Field:
    """A scalar attribute on an ObjectType.

    `type` is a forge-native primitive name; emitters map it to their
    language's nearest equivalent. Supported scalars (v0+):
        string | int | long | float | bool | datetime | uuid | json

    `optional` controls nullability in emitter output (e.g. C# `?`, TS `| null`,
    Python `Optional[...]`).

    `default` is a literal value (string-encoded) or None. Emitters only
    consume it if the target language allows default values on records.
    """

    name: str
    type: str
    optional: bool = False
    default: Optional[str] = None


@dataclass(frozen=True)
class Relation:
    """A link from one ObjectType to another.

    `cardinality` is one of: "one" | "many".
    `inverse` is the name of the back-reference projection on the target
    type (forge emits an `I{Inverse}Projection` interface in C#, a paired
    field in TS/Python).
    """

    name: str
    target: str
    cardinality: str = "one"
    inverse: Optional[str] = None


@dataclass(frozen=True)
class ObjectType:
    """A named, structured record. Closest analogue to an OWL Class / DTO."""

    name: str
    fields: tuple[Field, ...] = ()
    relations: tuple[Relation, ...] = ()
    annotations: tuple[tuple[str, str], ...] = ()
    """Tuple-of-tuples (sorted by key) so the dataclass stays frozen+hashable."""

    @property
    def annotation_map(self) -> dict[str, str]:
        return dict(self.annotations)


@dataclass(frozen=True)
class ProcessStep:
    """One activity in a Process. `kind` selects the BPMN element the emitter writes:
        service     → serviceTask (invokes the Agent Gateway; `agent` = slug)
        emit-event  → serviceTask that publishes a CloudEvent on `subject`
        manual      → userTask (HITL ack)
        wait        → intermediateCatchEvent (timer if `timeout`, else a message wait)
        decision    → exclusiveGateway (first `next` carries `condition`, last is default)
        parallel    → parallelGateway (fans out to every `next`)
        call        → callActivity (`calls` = sub-process id; recursive nesting)
        end         → endEvent
    `next` lists successor step names; empty = fall through to the next declared step.
    """

    name: str
    kind: str
    agent: Optional[str] = None
    calls: Optional[str] = None
    subject: Optional[str] = None
    timeout: Optional[str] = None
    condition: Optional[str] = None
    next: tuple[str, ...] = ()


@dataclass(frozen=True)
class Process:
    """A perdurant (UFO «event»/«situation») that transforms endurants over time.
    Compiles to a BPMN/CACAO artifact the runbook-orchestrator kernel executes
    (ARC-ADR-031 Q5 / ARC-ADR-038). `trigger_kind` is message|timer|signal|manual|none."""

    id: str
    name: str = ""
    trigger_kind: str = "none"
    trigger_subject: Optional[str] = None
    trigger_schedule: Optional[str] = None
    steps: tuple[ProcessStep, ...] = ()


@dataclass
class Model:
    """The whole input bundle. version + namespace control emitter output paths."""

    version: str
    namespace: str
    object_types: list[ObjectType] = field(default_factory=list)
    processes: list[Process] = field(default_factory=list)
    source_uri: Optional[str] = None
    """Where this model was loaded from (file URI / http URL / blob URI).
    Threaded into emitter file-headers for provenance."""

    def get(self, name: str) -> Optional[ObjectType]:
        for ot in self.object_types:
            if ot.name == name:
                return ot
        return None

    def sorted_types(self) -> list[ObjectType]:
        """Lexicographic sort — used as the canonical iteration order in emitters."""
        return sorted(self.object_types, key=lambda t: t.name)


# ---------------------------------------------------------------------------
# Type validation — emitters call this before emitting to fail fast on a bad
# IR (saves a confusing compile error downstream).
# ---------------------------------------------------------------------------
ALLOWED_SCALARS = frozenset(
    {"string", "int", "long", "float", "bool", "datetime", "uuid", "json"}
)
ALLOWED_CARDINALITIES = frozenset({"one", "many"})
ALLOWED_STEP_KINDS = frozenset(
    {"service", "emit-event", "manual", "wait", "decision", "parallel", "call", "end"}
)


def validate(model: Model) -> list[str]:
    """Return a list of validation errors (empty on success).

    Checked invariants:
      * every Field.type is in ALLOWED_SCALARS
      * every Relation.cardinality is in ALLOWED_CARDINALITIES
      * every Relation.target refers to an existing ObjectType in the model
      * no two ObjectTypes share a name
      * no two Fields on one ObjectType share a name (same for Relations)
    """
    errors: list[str] = []

    names = [ot.name for ot in model.object_types]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        errors.append(f"duplicate ObjectType names: {dupes}")

    known = set(names)
    for ot in model.object_types:
        fnames = [f.name for f in ot.fields]
        if len(set(fnames)) != len(fnames):
            errors.append(f"ObjectType {ot.name!r}: duplicate Field names")
        rnames = [r.name for r in ot.relations]
        if len(set(rnames)) != len(rnames):
            errors.append(f"ObjectType {ot.name!r}: duplicate Relation names")
        for f in ot.fields:
            if f.type not in ALLOWED_SCALARS:
                errors.append(
                    f"ObjectType {ot.name!r} Field {f.name!r}: "
                    f"type {f.type!r} not in {sorted(ALLOWED_SCALARS)}"
                )
        for r in ot.relations:
            if r.cardinality not in ALLOWED_CARDINALITIES:
                errors.append(
                    f"ObjectType {ot.name!r} Relation {r.name!r}: "
                    f"cardinality {r.cardinality!r} not in "
                    f"{sorted(ALLOWED_CARDINALITIES)}"
                )
            if r.target not in known:
                errors.append(
                    f"ObjectType {ot.name!r} Relation {r.name!r}: "
                    f"target {r.target!r} not declared in model"
                )

    proc_ids = [p.id for p in model.processes]
    if len(set(proc_ids)) != len(proc_ids):
        errors.append("duplicate Process ids")
    for p in model.processes:
        if not p.steps:
            errors.append(f"Process {p.id!r}: must declare at least one step")
        step_names = {s.name for s in p.steps}
        for s in p.steps:
            if s.kind not in ALLOWED_STEP_KINDS:
                errors.append(
                    f"Process {p.id!r} step {s.name!r}: kind {s.kind!r} "
                    f"not in {sorted(ALLOWED_STEP_KINDS)}"
                )
            if s.kind == "call" and not s.calls:
                errors.append(f"Process {p.id!r} step {s.name!r}: call step requires 'calls'")
            for nxt in s.next:
                if nxt not in step_names:
                    errors.append(
                        f"Process {p.id!r} step {s.name!r}: next {nxt!r} "
                        f"is not a step in this process"
                    )

    return errors
