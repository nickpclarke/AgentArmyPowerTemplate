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

Run: python scripts/check_sync_path_drift.py             (exit 0 = in sync, 1 = drift)
     python scripts/check_sync_path_drift.py --self-test  (exercise the matching logic)
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


def parse_on_push_paths(text: str) -> list[str]:
    """Extract on.push.paths from a workflow's YAML *text*.

    Takes text (not a Path) so the self-test can feed synthetic workflows. Handles the
    YAML 1.1 gotcha where the bare key `on:` resolves to the boolean True, not the string
    "on" -- so we look the block up under both spellings.
    """
    doc = yaml.safe_load(text)
    if not isinstance(doc, dict):
        raise ValueError("workflow YAML did not parse to a mapping")
    on = doc.get("on", doc.get(True))
    push = on.get("push") if isinstance(on, dict) else None
    if not isinstance(push, dict) or "paths" not in push:
        raise ValueError("no on.push.paths block to validate")
    paths = push["paths"]
    # A scalar `paths: "AGENTS.md"` is valid YAML, but list()-ing a string splits it into
    # characters -> confusing phantom drift. Require an explicit list of strings.
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        raise ValueError("on.push.paths must be a list of strings")
    return list(paths)


def load_trigger_paths(wf_path: Path) -> list[str]:
    try:
        return parse_on_push_paths(wf_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        sys.exit(f"::error::{wf_path}: {exc}.")


def find_missing(manifest_paths: list[str], trigger_paths: list[str]) -> list[str]:
    """Manifest paths the trigger fails to cover -- exact match or the `dir/**` convention.

    Returned in manifest order so the failure message reads top-to-bottom.
    """
    triggers = set(trigger_paths)
    return [
        p for p in manifest_paths
        if p not in triggers and f"{p}/**" not in triggers
    ]


def find_extras(trigger_paths: list[str], manifest_paths: list[str]) -> list[str]:
    """Trigger paths with no manifest backing and not known sync machinery (typo / stale)."""
    manifest = set(manifest_paths)
    return sorted(
        t for t in set(trigger_paths)
        if t not in TRIGGER_ONLY_OK
        and t not in manifest
        and t.removesuffix("/**") not in manifest
    )


def main() -> int:
    manifest_paths = json.loads(MANIFEST.read_text(encoding="utf-8"))["paths"]
    trigger_paths = load_trigger_paths(WORKFLOW)
    rel_wf = WORKFLOW.relative_to(REPO).as_posix()
    rel_manifest = MANIFEST.relative_to(REPO).as_posix()

    # Hard invariant: every synced path must be covered by the trigger (exact, or as dir/**).
    missing = find_missing(manifest_paths, trigger_paths)
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
    extras = find_extras(trigger_paths, manifest_paths)
    if extras:
        print(
            f"::warning::{rel_wf} on.push.paths has entries absent from {rel_manifest} and "
            f"not known sync machinery (typo or stale?): {', '.join(extras)}"
        )

    print(f"OK: all {len(manifest_paths)} synced paths are covered by the sync trigger.")
    return 0


def self_test() -> int:
    """Exercise the matching logic on synthetic inputs -- no repo files required.

    Covers the documented convention (dir/** <-> bare dir), the core 'missing path' bug
    class PR #368 hit, the trigger-only-machinery allowance, stale-extra detection, the
    YAML 1.1 `on:`->True parsing gotcha, and rejection of a malformed (scalar / non-string)
    paths block.
    """
    failures: list[str] = []
    ran = 0

    def expect(name: str, got: object, want: object) -> None:
        nonlocal ran
        ran += 1
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    def expect_raises(name: str, fn) -> None:
        nonlocal ran
        ran += 1
        try:
            fn()
        except ValueError:
            return
        failures.append(f"{name}: expected ValueError, none raised")

    # dir/** in the trigger covers a bare directory in the manifest (the convention).
    expect("dir-glob covers bare dir",
           find_missing([".claude/agents"], [".claude/agents/**"]), [])
    # an exact file entry is covered by the identical trigger entry.
    expect("exact file covered",
           find_missing(["AGENTS.md"], ["AGENTS.md"]), [])
    # a manifest path absent from the trigger is reported (the #368 drift bug).
    expect("missing path detected",
           find_missing(["AGENTS.md", ".claude/hooks/setup-dotnet.sh"], ["AGENTS.md"]),
           [".claude/hooks/setup-dotnet.sh"])
    # results come back in manifest order, covered entries dropped.
    expect("missing preserves manifest order",
           find_missing(["a", "b", "c"], ["b"]), ["a", "c"])
    # the sync machinery is trigger-only by design and must not be flagged as an extra.
    expect("machinery is not an extra",
           find_extras(sorted(TRIGGER_ONLY_OK), []), [])
    # a trigger entry with no manifest backing surfaces as an extra (typo / stale).
    expect("stale extra flagged",
           find_extras(["ghost.md"], []), ["ghost.md"])
    # a dir/** trigger whose bare dir IS in the manifest is not an extra.
    expect("dir-glob with manifest dir is not an extra",
           find_extras([".claude/agents/**"], [".claude/agents"]), [])
    # YAML 1.1 reads bare `on:` as boolean True -- we must still find push.paths.
    expect("yaml on:->True gotcha handled",
           parse_on_push_paths(
               "on:\n  push:\n    branches: [main]\n"
               "    paths:\n      - \"AGENTS.md\"\n      - \".claude/agents/**\"\njobs: {}\n"
           ),
           ["AGENTS.md", ".claude/agents/**"])
    # a scalar `paths:` is valid YAML but must be rejected, not split into characters.
    expect_raises("scalar paths rejected",
                  lambda: parse_on_push_paths(
                      "on:\n  push:\n    paths: \"AGENTS.md\"\njobs: {}\n"))
    # a list with a non-string entry is rejected too.
    expect_raises("non-string paths entry rejected",
                  lambda: parse_on_push_paths(
                      "on:\n  push:\n    paths:\n      - 42\njobs: {}\n"))

    if failures:
        print("self-test FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"self-test: all {ran} assertions passed.")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(self_test())
    raise SystemExit(main())
