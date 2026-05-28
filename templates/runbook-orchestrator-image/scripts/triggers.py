"""Runbook directory index + trigger derivation for serve mode.

Scans a directory of runbook files (the orchestrator's *only* required input),
parses each, and exposes the subset that should fire on a bus event keyed by the
`fleet.*` subject derived from its start trigger. Pure stdlib — no broker import
here, so it stays unit-testable in isolation.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from runbook_engine import load, validate_file

_RUNBOOK_EXT = (".bpmn", ".xml", ".json")


@dataclass
class RunbookEntry:
    path: str
    id: str = ""
    name: str = ""
    format: str = "?"
    trigger: dict = field(default_factory=lambda: {"kind": "none"})
    valid: bool = False
    errors: list[str] = field(default_factory=list)
    graph: object | None = None

    def summary(self) -> dict:
        return {"id": self.id, "name": self.name, "format": self.format,
                "trigger": self.trigger, "valid": self.valid,
                "errors": self.errors, "path": self.path}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def subject_for(trigger: dict) -> str | None:
    if trigger.get("kind") not in ("message", "signal"):
        return None
    if trigger.get("subject"):
        return trigger["subject"]
    name = trigger.get("name") or trigger.get("ref")
    return f"fleet.runbook.{slugify(name)}" if name else None


class RunbookIndex:
    def __init__(self, directory: str):
        self.directory = directory
        self.entries: list[RunbookEntry] = []

    def reload(self) -> list[RunbookEntry]:
        self.entries = []
        for root, _dirs, files in os.walk(self.directory):
            for filename in sorted(files):
                if filename.endswith(_RUNBOOK_EXT):
                    self._index_one(os.path.join(root, filename))
        return self.entries

    def _index_one(self, path: str) -> None:
        if path.endswith(".json") and not _looks_like_playbook(path):
            return  # a non-playbook JSON (e.g. a context file) — skip silently
        entry = RunbookEntry(path=path)
        try:
            entry.errors = validate_file(path)
        except Exception as exc:  # noqa: BLE001
            entry.errors = [f"load error: {exc}"]
        try:
            graph = load(path)
            entry.graph = graph
            entry.format = graph.source_format
            entry.id = graph.id or path
            entry.name = graph.name
            entry.trigger = graph.start_trigger or {"kind": "none"}
        except Exception as exc:  # noqa: BLE001
            entry.errors = entry.errors + [f"parse error: {exc}"]
        entry.valid = not entry.errors
        self.entries.append(entry)

    def by_subject(self) -> dict[str, list[RunbookEntry]]:
        mapping: dict[str, list[RunbookEntry]] = {}
        for entry in self.entries:
            if not entry.valid:
                continue
            subject = subject_for(entry.trigger)
            if subject:
                mapping.setdefault(subject, []).append(entry)
        return mapping

    def find(self, runbook_id: str) -> RunbookEntry | None:
        return next((e for e in self.entries if e.id == runbook_id), None)


def _looks_like_playbook(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
        return isinstance(obj, dict) and obj.get("type") == "playbook"
    except Exception:  # noqa: BLE001
        return False
