"""board-sync runtime — apply a PROVEN field adapter to a source work-item payload to
produce a canonical WorkItem (ARC-ADR-036).

No embedder, no abstraction service at runtime: the adapter was discovered, escalated,
and VALIDATED at build time by the abstraction meta-service and vended into
``adapters/``. This runtime just projects a live payload through that proven map — so
a GitHub issue and a Linear issue come out as the same canonical shape.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED = ["Identifier", "Title", "Status"]


def _get(payload: dict, path: str):
    """Read a (possibly dotted) source-field path from a payload."""
    cur = payload
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def load_adapter(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def apply_adapter(adapter: dict, payload: dict) -> dict:
    """Project a source payload into a canonical WorkItem via ``adapter['map']``
    ({canonical_field: source_field_path}). Carries source provenance."""
    item: dict = {"_source": adapter.get("source"),
                  "_canonical_type": adapter.get("canonical_type", "WorkItem")}
    for canonical, source_field in (adapter.get("map") or {}).items():
        item[canonical] = _get(payload, source_field)
    return item


def missing_required(item: dict) -> list[str]:
    return [r for r in REQUIRED if item.get(r) in (None, "", [])]
