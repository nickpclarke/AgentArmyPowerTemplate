"""TypeScript emitter — forge IR → `*.g.ts` for frontend-core consumption.

Output:
    {out_dir}/
      data-platform-contracts.g.ts   -- types + Zod schemas

Shape per ObjectType `Document`:
    export interface Document {
      id: string;
      title: string;
      body: string | null;
      createdAt: string;
      author: User;       // relation, cardinality=one
      // for many: tags: Tag[];
    }

    export const DocumentSchema = z.object({
      id: z.string().uuid(),
      title: z.string(),
      body: z.string().nullable(),
      createdAt: z.string().datetime(),
    });

Determinism: same rules as the C# emitter.
"""
from __future__ import annotations

import os

from ..ir import Field, Model, Relation, validate

# forge primitive -> TS type
_TS_TYPE: dict[str, str] = {
    "string": "string",
    "int": "number",
    "long": "number",
    "float": "number",
    "bool": "boolean",
    "datetime": "string",  # ISO 8601 string at the wire layer
    "uuid": "string",
    "json": "unknown",
}

# forge primitive -> Zod schema fragment
_ZOD: dict[str, str] = {
    "string": "z.string()",
    "int": "z.number().int()",
    "long": "z.number().int()",
    "float": "z.number()",
    "bool": "z.boolean()",
    "datetime": "z.string().datetime()",
    "uuid": "z.string().uuid()",
    "json": "z.unknown()",
}

INDENT = "  "


def emit(model: Model, out_dir: str) -> list[str]:
    errors = validate(model)
    if errors:
        raise ValueError("invalid model: " + "; ".join(errors))

    os.makedirs(out_dir, exist_ok=True)
    contents = _render(model)
    out_path = os.path.join(out_dir, "data-platform-contracts.g.ts")
    with open(out_path, "wb") as f:
        f.write(contents.encode("utf-8"))
    return ["data-platform-contracts.g.ts"]


def _render(model: Model) -> str:
    lines: list[str] = []
    lines.append("// @generated — emitted by agentarmy-forge")
    lines.append(f"//   forge.version: {_forge_version()}")
    lines.append(f"//   model.version: {model.version}")
    lines.append(f"//   source.uri:    {model.source_uri or '<inline>'}")
    lines.append("//   DO NOT EDIT. Re-run forge against the source ontology to regenerate.")
    lines.append("")
    lines.append("import { z } from 'zod';")
    lines.append("")

    # Interfaces first (they reference each other by name; TS forward-references
    # are fine within the same module).
    for ot in model.object_types:
        lines.extend(_render_interface(ot))
        lines.append("")

    # Then Zod schemas. Schemas don't reference each other in this baseline —
    # cross-reference would require z.lazy + ordering work; defer to a later
    # iteration since frontend code rarely round-trips nested graphs in v2.
    for ot in model.object_types:
        lines.extend(_render_schema(ot))
        lines.append("")

    text = "\n".join(lines).rstrip("\n") + "\n"
    return text


def _render_interface(ot) -> list[str]:
    out: list[str] = []
    out.append(f"export interface {ot.name} {{")
    for f in ot.fields:
        ts_type = _TS_TYPE.get(f.type, "unknown")
        if f.optional:
            out.append(f"{INDENT}{_camel(f.name)}: {ts_type} | null;")
        else:
            out.append(f"{INDENT}{_camel(f.name)}: {ts_type};")
    for r in ot.relations:
        if r.cardinality == "many":
            out.append(f"{INDENT}{_camel(r.name)}: {r.target}[];")
        else:
            out.append(f"{INDENT}{_camel(r.name)}: {r.target};")
    out.append("}")
    return out


def _render_schema(ot) -> list[str]:
    out: list[str] = []
    out.append(f"export const {ot.name}Schema = z.object({{")
    for f in ot.fields:
        frag = _ZOD.get(f.type, "z.unknown()")
        if f.optional:
            frag = f"{frag}.nullable()"
        out.append(f"{INDENT}{_camel(f.name)}: {frag},")
    out.append("});")
    return out


def _camel(name: str) -> str:
    """snake/PascalCase -> camelCase."""
    if not name:
        return name
    parts: list[str] = []
    chunk: list[str] = []
    for ch in name:
        if ch in ("_", "-"):
            if chunk:
                parts.append("".join(chunk))
                chunk = []
        else:
            chunk.append(ch)
    if chunk:
        parts.append("".join(chunk))
    if not parts:
        return name
    head = parts[0]
    head = head[:1].lower() + head[1:]
    tail = "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return head + tail


def _forge_version() -> str:
    from .. import __version__

    return __version__
