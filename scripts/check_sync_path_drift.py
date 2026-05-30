#!/usr/bin/env python3
"""Guard against drift between the spoke-sync manifest and the sync workflow's trigger.

Two hand-maintained lists must agree:
  1. scripts/spoke_sync.config.json            -> "paths"          (WHAT syncs hub -> spokes)
  2. .github/workflows/sync-helpers-to-spokes.yml -> on.push.paths (what TRIGGERS a sync)

GitHub Actions evaluates `push.paths` statically and can't read the JSON manifest at
trigger-eval time, so the trigger list is duplicated by hand. If a synced path is missing
from the trigger, an edit to that file lands on the hub but never opens spoke sync PRs --
the bug PR #368 fixed by hand. This check asserts every manifest path is covered by the
trigger so the drift can't silently return, and fails CI otherwise.

Convention: a bare directory in the manifest (e.g. ".claude/agents") maps to a "dir/**"
glob in the trigger; both forms are accepted as coverage.

Run: python scripts/check_sync_path_drift.py   (exit 0 = in sync, 1 = drift)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "scripts" / "spoke_sync.config.json"
WORKFLOW = REPO / ".github" / "workflows" / "sync-helpers-to-spokes.yml"

# Paths that legitimately appear only in the trigger: the sync machinery itself. Editing
# either should re-run the sync, but neither is content that gets copied into spokes, so
# neither belongs in the manifest's `paths`.
TRIGGER_ONLY_OK = {
    "scripts/spoke_sync.config.json",
    "scripts/sync_helpers_to_spokes.py",
}


def load_trigger_paths(wf_path: Path) -> list[str]:
    doc = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    # YAML 1.1 parses the bare key `on:` as the boolean True, so check both spellings.
    on = doc.get("on", doc.get(True))
    if not isinstance(on, dict) or "paths" not in (on.get("push") or {}):
        sys.exit(f"::error::{wf_path} has no on.push.paths to validate.")
    return list(on["push"]["paths"])


def main() -> int:
    manifest_paths = json.loads(MANIFEST.read_text(encoding="utf-8"))["paths"]
    trigger_paths = set(load_trigger_paths(WORKFLOW))
    rel_wf = WORKFLOW.relative_to(REPO).as_posix()
    rel_manifest = MANIFEST.relative_to(REPO).as_posix()

    # Hard invariant: every synced path must be covered by the trigger (exact, or as dir/**).
    missing = [
        p for p in manifest_paths
        if p not in trigger_paths and f"{p}/**" not in trigger_paths
    ]
    if missing:
        print(
            f"::error::{rel_wf} on.push.paths is missing {len(missing)} path(s) that "
            f"{rel_manifest} syncs to spokes. Edits to these files would land on the hub "
            f"but never open spoke sync PRs. Add to the trigger (dirs as 'path/**'):"
        )
        for p in missing:
            print(f"  - \"{p}\"")
        return 1

    # Soft signal: a trigger path with no manifest entry won't break sync, but usually means
    # a typo or a stale entry left behind. Warn (don't fail) so real machinery can be added.
    extras = sorted(
        t for t in trigger_paths
        if t not in TRIGGER_ONLY_OK
        and t not in manifest_paths
        and t.removesuffix("/**") not in manifest_paths
    )
    if extras:
        print(
            f"::warning::{rel_wf} on.push.paths has entries absent from {rel_manifest} and "
            f"not known sync machinery (typo or stale?): {', '.join(extras)}"
        )

    print(f"OK: all {len(manifest_paths)} synced paths are covered by the sync trigger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
