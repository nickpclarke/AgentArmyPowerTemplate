"""Python emitter — forge IR → `*.g.py` (Pydantic v2 models) for backend-core.

Output:
    {out_dir}/
      data_platform_contracts.g.py   -- one module, all models

Shape per ObjectType `Document`:
    class Document(BaseModel):
        id: UUID
        title: str
        body: Optional[str] = None
        created_at: datetime
        author: 'User'                  # relation, cardinality=one
        # for many: tags: list['Tag']

Pydantic v2 ConfigDict allows forward references — we use string annotations
for relation targets so emitter order doesn't matter.
"""
from __future__ import annotations

import os

from ..ir import Field, Model, Relation, validate

# forge primitive -> Python type
_PY_TYPE: dict[str, str] = {
    "string": "str",
    "int": "int",
    "long": "int",
    "float": "float",
    "bool": "bool",
    "datetime": "datetime",
    "uuid": "UUID",
    "json": "Any",
}

INDENT = "    "


def emit(model: Model, out_dir: str) -> list[str]:
    errors = validate(model)
    if errors:
        raise ValueError("invalid model: " + "; ".join(errors))

    os.makedirs(out_dir, exist_ok=True)
    contents = _render(model)
    out_path = os.path.join(out_dir, "data_platform_contracts.g.py")
    with open(out_path, "wb") as f:
        f.write(contents.encode("utf-8"))
    return ["data_platform_contracts.g.py"]


def _render(model: Model) -> str:
    lines: list[str] = []
    lines.append('"""@generated — emitted by agentarmy-forge.')
    lines.append("")
    lines.append(f"forge.version: {_forge_version()}")
    lines.append(f"model.version: {model.version}")
    lines.append(f"source.uri:    {model.source_uri or '<inline>'}")
    lines.append("")
    lines.append("DO NOT EDIT. Re-run forge against the source ontology to regenerate.")
    lines.append('"""')
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from datetime import datetime")
    lines.append("from typing import Any, Optional")
    lines.append("from uuid import UUID")
    lines.append("")
    lines.append("from pydantic import BaseModel, ConfigDict")
    lines.append("")
    lines.append("")

    for ot in model.object_types:
        lines.extend(_render_model(ot))
        lines.append("")
        lines.append("")

    # Forward-ref resolution — Pydantic v2 needs an explicit model_rebuild()
    # for string-annotated relations to materialise.
    for ot in model.object_types:
        lines.append(f"{ot.name}.model_rebuild()")
    lines.append("")

    text = "\n".join(lines).rstrip("\n") + "\n"
    return text


def _render_model(ot) -> list[str]:
    out: list[str] = []
    out.append(f"class {ot.name}(BaseModel):")
    out.append(f'{INDENT}"""{_doc(ot)}"""')
    out.append(f"{INDENT}model_config = ConfigDict(populate_by_name=True)")
    out.append("")
    has_any = False
    for f in ot.fields:
        py_type = _PY_TYPE.get(f.type, "Any")
        if f.optional:
            out.append(f"{INDENT}{_snake(f.name)}: Optional[{py_type}] = None")
        else:
            default = ""
            if f.default is not None:
                default = f" = {_lit(f.type, f.default)}"
            out.append(f"{INDENT}{_snake(f.name)}: {py_type}{default}")
        has_any = True
    for r in ot.relations:
        if r.cardinality == "many":
            out.append(f"{INDENT}{_snake(r.name)}: list['{r.target}'] = []")
        else:
            out.append(f"{INDENT}{_snake(r.name)}: Optional['{r.target}'] = None")
        has_any = True
    if not has_any:
        out.append(f"{INDENT}pass")
    return out


def _doc(ot) -> str:
    ann = ot.annotation_map
    return (
        ann.get("http://www.w3.org/2000/01/rdf-schema#label")
        or ann.get("rdfs:label")
        or ann.get("label")
        or ot.name
    )


def _lit(forge_type: str, raw: str) -> str:
    if forge_type in ("int", "long", "float"):
        return raw
    if forge_type == "bool":
        return "True" if raw.lower() == "true" else "False"
    # default — string literal with simple escaping
    safe = raw.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{safe}"'


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


def _forge_version() -> str:
    from .. import __version__

    return __version__
