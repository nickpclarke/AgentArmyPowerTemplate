"""YAML → forge IR.

Schema (the back-compat shape lifted from middle-core's model.yaml):

    version: "1.0.0"
    namespace: "AgentArmy.MiddleCore.Contracts"
    objectTypes:
      - name: Document
        annotations:
          owl: "https://example.org/onto#Document"
        fields:
          - { name: id, type: uuid }
          - { name: title, type: string }
          - { name: body, type: string, optional: true }
          - { name: createdAt, type: datetime }
        relations:
          - { name: author, target: User, cardinality: one, inverse: documents }

Field iteration order in the parsed IR preserves the source mapping order so
the byte-identical doctor check is meaningful (pyyaml SafeLoader preserves
insertion order in CPython 3.7+).
"""
from __future__ import annotations

from typing import Any, Optional

import yaml

from ..ir import Field, Model, ObjectType, Process, ProcessStep, Relation


def parse(source: str | bytes, source_uri: Optional[str] = None) -> Model:
    """Load a YAML model document and convert it to an IR `Model`.

    Raises `ValueError` on a malformed document — the caller surfaces this
    as a 422 in the FastAPI handler / nonzero CLI exit.
    """
    if isinstance(source, bytes):
        source = source.decode("utf-8")

    raw = yaml.safe_load(source)
    if not isinstance(raw, dict):
        raise ValueError("YAML root must be a mapping")

    version = str(raw.get("version", "0.0.0"))
    namespace = str(raw.get("namespace", "AgentArmy.Generated"))
    object_types_raw = raw.get("objectTypes", [])
    if not isinstance(object_types_raw, list):
        raise ValueError("'objectTypes' must be a list")

    object_types: list[ObjectType] = []
    for entry in object_types_raw:
        if not isinstance(entry, dict):
            raise ValueError("each objectTypes entry must be a mapping")
        if "name" not in entry:
            raise ValueError("objectTypes entry missing required 'name'")
        ot = ObjectType(
            name=str(entry["name"]),
            fields=tuple(_parse_fields(entry.get("fields", []))),
            relations=tuple(_parse_relations(entry.get("relations", []))),
            annotations=tuple(
                sorted((str(k), str(v)) for k, v in (entry.get("annotations", {}) or {}).items())
            ),
        )
        object_types.append(ot)

    return Model(
        version=version,
        namespace=namespace,
        object_types=object_types,
        processes=_parse_processes(raw.get("processes", [])),
        source_uri=source_uri,
    )


def _parse_fields(raw: Any) -> list[Field]:
    if not isinstance(raw, list):
        raise ValueError("'fields' must be a list")
    out: list[Field] = []
    for f in raw:
        if not isinstance(f, dict):
            raise ValueError("each field must be a mapping")
        out.append(
            Field(
                name=str(f["name"]),
                type=str(f.get("type", "string")),
                optional=bool(f.get("optional", False)),
                default=None if f.get("default") is None else str(f["default"]),
            )
        )
    return out


def _parse_relations(raw: Any) -> list[Relation]:
    if not isinstance(raw, list):
        raise ValueError("'relations' must be a list")
    out: list[Relation] = []
    for r in raw:
        if not isinstance(r, dict):
            raise ValueError("each relation must be a mapping")
        out.append(
            Relation(
                name=str(r["name"]),
                target=str(r["target"]),
                cardinality=str(r.get("cardinality", "one")),
                inverse=(str(r["inverse"]) if r.get("inverse") else None),
            )
        )
    return out


def _parse_processes(raw: Any) -> list[Process]:
    if not isinstance(raw, list):
        raise ValueError("'processes' must be a list")
    out: list[Process] = []
    for p in raw:
        if not isinstance(p, dict):
            raise ValueError("each process must be a mapping")
        if "id" not in p:
            raise ValueError("process entry missing required 'id'")
        trigger = p.get("trigger", {}) or {}
        if not isinstance(trigger, dict):
            raise ValueError(f"process {p['id']!r}: 'trigger' must be a mapping")
        out.append(
            Process(
                id=str(p["id"]),
                name=str(p.get("name", "")),
                trigger_kind=str(trigger.get("kind", "none")),
                trigger_subject=(str(trigger["subject"]) if trigger.get("subject") else None),
                trigger_schedule=(str(trigger["schedule"]) if trigger.get("schedule") else None),
                steps=tuple(_parse_steps(p.get("steps", []))),
            )
        )
    return out


def _parse_steps(raw: Any) -> list[ProcessStep]:
    if not isinstance(raw, list):
        raise ValueError("'steps' must be a list")
    out: list[ProcessStep] = []
    for s in raw:
        if not isinstance(s, dict):
            raise ValueError("each step must be a mapping")
        if "name" not in s or "kind" not in s:
            raise ValueError("each step requires 'name' and 'kind'")
        nxt = s.get("next", []) or []
        if not isinstance(nxt, list):
            raise ValueError(f"step {s['name']!r}: 'next' must be a list")
        out.append(
            ProcessStep(
                name=str(s["name"]),
                kind=str(s["kind"]),
                agent=(str(s["agent"]) if s.get("agent") else None),
                calls=(str(s["calls"]) if s.get("calls") else None),
                subject=(str(s["subject"]) if s.get("subject") else None),
                timeout=(str(s["timeout"]) if s.get("timeout") else None),
                condition=(str(s["condition"]) if s.get("condition") else None),
                next=tuple(str(n) for n in nxt),
            )
        )
    return out
