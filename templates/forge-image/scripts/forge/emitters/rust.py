"""Rust emitter — forge IR → `*.g.rs` (serde structs + state enums) for rust-api-v2.

Output:
    {out_dir}/
      data_platform_contracts.g.rs   -- one module, all data objects

Shape per ObjectType `AgentData` (state_property="state", states=[registered, active, …]):
    /// AgentData
    #[derive(Clone, Debug, Serialize, Deserialize)]
    pub struct AgentData {
        pub agent_id: String,
        pub state: AgentDataState,        // the state_property field, retyped to the enum
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
    #[serde(rename_all = "kebab-case")]
    pub enum AgentDataState {
        Registered,
        Active,
    }

Determinism (load-bearing for the byte-identical doctor check): types iterate in
`sorted_types()` order; fields/relations/states in declared order; LF endings; no timestamps.
Output is dependency-light — only `use serde::{Deserialize, Serialize};` (json fields use the
fully-qualified `serde_json::Value`, list-scalars `Vec<…>` + `#[serde(default)]`).
"""
from __future__ import annotations

import os

from ..ir import Model, ObjectType, validate

# forge primitive -> Rust type (kept dependency-light; uuid/datetime are String like the
# data-platform contract, which types ids/timestamps as `string`).
_RS_TYPE: dict[str, str] = {
    "string": "String",
    "int": "i32",
    "long": "i64",
    "float": "f64",
    "bool": "bool",
    "datetime": "String",
    "uuid": "String",
    "json": "serde_json::Value",
}

INDENT = "    "


def emit(model: Model, out_dir: str) -> list[str]:
    errors = validate(model)
    if errors:
        raise ValueError("invalid model: " + "; ".join(errors))

    os.makedirs(out_dir, exist_ok=True)
    contents = _render(model)
    out_path = os.path.join(out_dir, "data_platform_contracts.g.rs")
    with open(out_path, "wb") as f:
        f.write(contents.encode("utf-8"))
    return ["data_platform_contracts.g.rs"]


def _render(model: Model) -> str:
    lines: list[str] = []
    lines.append("// @generated — emitted by agentarmy-forge.")
    lines.append("//")
    lines.append(f"//   forge.version: {_forge_version()}")
    lines.append(f"//   model.version: {model.version}")
    lines.append(f"//   source.uri:    {model.source_uri or '<inline>'}")
    lines.append("//")
    lines.append("//   DO NOT EDIT. Re-run forge against the source ontology to regenerate.")
    lines.append("#![allow(dead_code)]")
    lines.append("")
    lines.append("use serde::{Deserialize, Serialize};")
    lines.append("")

    blocks: list[list[str]] = []
    for ot in model.sorted_types():
        blocks.append(_render_struct(ot))
        if ot.states:
            blocks.append(_render_enum(ot))

    for block in blocks:
        lines.extend(block)
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def _render_struct(ot: ObjectType) -> list[str]:
    out: list[str] = []
    out.append(f"/// {_doc(ot)}")
    out.append("#[derive(Clone, Debug, Serialize, Deserialize)]")
    out.append(f"pub struct {ot.name} {{")
    for f in ot.fields:
        if ot.state_property and f.name == ot.state_property and ot.states:
            out.append(f"{INDENT}pub {_snake(f.name)}: {ot.name}State,")
        elif f.is_list:
            inner = _RS_TYPE.get(f.type, "String")
            out.append(f"{INDENT}#[serde(default)]")
            out.append(f"{INDENT}pub {_snake(f.name)}: Vec<{inner}>,")
        else:
            ty = _RS_TYPE.get(f.type, "String")
            out.append(f"{INDENT}pub {_snake(f.name)}: {_wrap_optional(f, ty)},")
    for r in ot.relations:
        if r.cardinality == "many":
            out.append(f"{INDENT}#[serde(default)]")
            out.append(f"{INDENT}pub {_snake(r.name)}: Vec<{r.target}>,")
        else:
            out.append(f"{INDENT}pub {_snake(r.name)}: Option<Box<{r.target}>>,")
    out.append("}")
    return out


def _render_enum(ot: ObjectType) -> list[str]:
    out: list[str] = []
    out.append("#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]")
    out.append('#[serde(rename_all = "kebab-case")]')
    out.append(f"pub enum {ot.name}State {{")
    for state in ot.states:
        out.append(f"{INDENT}{_pascal(state)},")
    out.append("}")
    return out


def _wrap_optional(f, ty: str) -> str:
    return f"Option<{ty}>" if f.optional else ty


def _doc(ot: ObjectType) -> str:
    ann = ot.annotation_map
    return (
        ann.get("http://www.w3.org/2000/01/rdf-schema#label")
        or ann.get("rdfs:label")
        or ann.get("label")
        or ot.name
    )


def _snake(name: str) -> str:
    """camel/PascalCase -> snake_case (idempotent on snake)."""
    out: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and out and out[-1] != "_":
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch.lower() if ch.isupper() else ch)
    return "".join(out).replace("-", "_")


def _pascal(name: str) -> str:
    """kebab/snake/space -> PascalCase enum variant (in-progress -> InProgress)."""
    parts = name.replace("-", " ").replace("_", " ").split()
    return "".join(p[:1].upper() + p[1:] for p in parts)


def _forge_version() -> str:
    from .. import __version__

    return __version__
