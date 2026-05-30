"""SQL emitter — forge IR + a binding spec → a backend SELECT string (the bindings facet).

Unlike the whole-file emitters (csharp/typescript/python/rust → `emit(model, out_dir)`),
this is a **per-object query helper**: `gen_data_objects.py` calls `EMITTERS[backend](ot, binding)`
for each data object that has a binding in `contracts/bindings.yaml`, and embeds the returned
string in a Rust `pub const … : &str = "<query>";` (so output MUST be a single-line query with no
unescaped double-quotes).

Binding shapes (ARC-ADR-038, validated against the data-platform contract):
    postgres: { relation: <schema.table>, columns: { <canonical_field>: <physical_column>, … } }
    arcadedb: { type: <ArcadeDB document type>, columns?: { <canonical_field>: <property>, … } }

Determinism: columns are projected in the object's **declared field order** (the IR's source
order); no sorting, no timestamps. Every `columns` key must be a real field of the object — an
unknown key raises, so a stale binding fails the build instead of emitting a silent bad query.
"""
from __future__ import annotations

from ..ir import ObjectType


def _field_names(ot: ObjectType) -> list[str]:
    return [f.name for f in ot.fields]


def _validate_columns(ot: ObjectType, columns: dict) -> None:
    known = set(_field_names(ot))
    unknown = [c for c in columns if c not in known]
    if unknown:
        raise ValueError(
            f"binding for {ot.name!r} maps unknown field(s) {unknown} "
            f"(not in the contract: {sorted(known)})"
        )


def emit_postgres(ot: ObjectType, binding: dict) -> str:
    """SELECT <physical> AS <canonical>, … FROM <relation> — column map required per field
    that differs from its canonical name (unmapped fields default to the same column name)."""
    relation = binding.get("relation")
    if not relation:
        raise ValueError(f"postgres binding for {ot.name!r} missing 'relation'")
    columns = binding.get("columns", {}) or {}
    _validate_columns(ot, columns)
    projected = []
    for field in _field_names(ot):
        phys = columns.get(field, field)
        projected.append(f"{phys} AS {field}" if phys != field else field)
    return f"SELECT {', '.join(projected)} FROM {relation}"


def emit_arcadedb(ot: ObjectType, binding: dict) -> str:
    """SELECT <property>, … FROM <type> — ArcadeDB SQL; properties default to canonical field
    names (the common case where the document type already matches the contract)."""
    typ = binding.get("type")
    if not typ:
        raise ValueError(f"arcadedb binding for {ot.name!r} missing 'type'")
    columns = binding.get("columns", {}) or {}
    _validate_columns(ot, columns)
    projected = [columns.get(field, field) for field in _field_names(ot)]
    return f"SELECT {', '.join(projected)} FROM {typ}"


# backend slug → emitter. `gen_data_objects.py` skips slugs not present here (a future backend).
EMITTERS = {
    "postgres": emit_postgres,
    "arcadedb": emit_arcadedb,
}
