#!/usr/bin/env python3
"""
One-way sync of the Claude Code microVM helper surface from the AgentArmy hub
to spoke repos (frontend-core, backend-core, ... see scripts/spoke_sync.config.json).

The hub is the source of truth. For each spoke this script clones it, mirrors the
allowlisted paths from the hub (so deletions propagate too), writes a provenance
stamp, and opens/updates a pull request. Spokes' microVM agents otherwise can't
see the hub's agent roster / commands / hooks — this gives them repo-local copies.

Usage:
    python scripts/sync_helpers_to_spokes.py                 # PR into every spoke
    python scripts/sync_helpers_to_spokes.py --dry-run       # clone + diff, no push/PR
    python scripts/sync_helpers_to_spokes.py --spoke backend-core
    python scripts/sync_helpers_to_spokes.py --config path/to/config.json

Requires: git and gh (GitHub CLI), authenticated with write access to the spokes.
In CI, set GH_TOKEN to a token with `repo` scope across the spoke repos.

Safety: paths in the config `deny` list are refused even if they appear in `paths`
(secrets, *.local.json, worktrees). The script aborts before touching any spoke if
a denied entry is present in `paths`.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STAMP_REL = ".claude/.agentarmy-sync.json"
# Always-ignored when copying a directory tree, regardless of config.
COPY_IGNORE = [".git", "__pycache__", "node_modules", "*.local.json", "worktrees"]

# Seeded into a spoke ONLY if it has no CLAUDE.md, so we never clobber a spoke's
# own guidance. {spoke} is the repo name. The @AGENTS.md line imports the shared,
# fleet-wide agent guidance that the sync delivers; the spoke owns everything else.
SEED_CLAUDE_MD = """# {spoke} — repository guidance

This repository is an AgentArmy **spoke** (a layer implementation). Unlike the hub
template, it contains real source code to build, run, test, and deploy.

**Orientation keys** (this repo does not carry the hub's `docs/` — read them here):
- Docs (settled reality): https://nickpclarke.github.io/AgentArmy/
- Labs (vision / WIP, Obsidian): https://publish.obsidian.md/xlabs/Welcome
- Hub pointer: `.agent/hub.json` — repo / board / docs / Labs URLs. You don't need hub
  board access; reporting back is automatic via `.github/workflows/notify-hub.yml`.

## Shared agent guidance

The AgentArmy specialist roster, routing rules, skills, and chaining patterns are
shared across the fleet and synced from the hub. Do not edit `AGENTS.md` here — edit
it in the hub. It is imported below:

@AGENTS.md

## Spoke-specific guidance

<!-- Add this layer's own build/run/test/deploy notes here. This file is yours;
     it is never overwritten by the sync. -->
"""


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("owner", "spokes", "paths"):
        if not cfg.get(key):
            raise ValueError(f"config missing required key: {key}")
    return cfg


def is_denied(rel_path: str, deny: list[str]) -> bool:
    name = Path(rel_path).name
    for pat in deny:
        if rel_path == pat or name == pat or fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_path, pat):
            return True
    return False


def validate_paths(cfg: dict) -> list[str]:
    """Ensure every source path exists in the hub and none is denied. Returns the paths."""
    deny = cfg.get("deny", [])
    problems = []
    for rel in cfg["paths"]:
        if is_denied(rel, deny):
            problems.append(f"  DENIED path present in `paths`: {rel}")
        if not (REPO_ROOT / rel).exists():
            problems.append(f"  source path does not exist in hub: {rel}")
    if problems:
        raise SystemExit("config validation failed:\n" + "\n".join(problems))
    return cfg["paths"]


def _ignore_factory():
    def _ignore(_dir, names):
        return {n for n in names if any(fnmatch.fnmatch(n, pat) for pat in COPY_IGNORE)}
    return _ignore


def mirror_path(rel: str, dest_root: Path) -> None:
    """Make dest_root/rel an exact copy of hub/rel (dir = mirror incl. deletions)."""
    src = REPO_ROOT / rel
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=_ignore_factory())
    else:
        shutil.copy2(src, dest)


def default_branch(repo: str) -> str:
    out = run(["gh", "repo", "view", repo, "--json", "defaultBranchRef",
               "--jq", ".defaultBranchRef.name"]).stdout.strip()
    return out or "main"


def write_stamp(dest_root: Path, cfg: dict, hub_sha: str, paths: list[str]) -> None:
    stamp = {
        "source": cfg.get("source_repo", f'{cfg["owner"]}/AgentArmy'),
        "hub_sha": hub_sha,
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paths": paths,
        "tool": "scripts/sync_helpers_to_spokes.py",
    }
    stamp_path = dest_root / STAMP_REL
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(json.dumps(stamp, indent=2) + "\n", encoding="utf-8")


def sync_spoke(spoke: str, cfg: dict, paths: list[str], hub_sha: str, dry_run: bool, merge: bool) -> str:
    repo = f'{cfg["owner"]}/{spoke}'
    branch = cfg.get("branch", "chore/agentarmy-helper-sync")
    print(f"\n=== {repo} ===")
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / spoke
        base = default_branch(repo)
        run(["gh", "repo", "clone", repo, str(dest), "--", "--depth", "1", "--branch", base])
        run(["git", "-C", str(dest), "checkout", "-B", branch])

        for rel in paths:
            mirror_path(rel, dest)

        # Seed a CLAUDE.md only if the spoke lacks one — never clobber the spoke's
        # own guidance (CLAUDE.md is also on the deny list). It imports @AGENTS.md.
        claude_md = dest / "CLAUDE.md"
        if not claude_md.exists():
            claude_md.write_text(SEED_CLAUDE_MD.format(spoke=spoke), encoding="utf-8")
            print("  seeded CLAUDE.md (none present) -> imports @AGENTS.md")

        # Stage everything, then FORCE-add the synced paths so a spoke .gitignore can
        # never silently drop them — the failure mode where .claude/ never reached main.
        run(["git", "-C", str(dest), "add", "-A"])
        for rel in paths:
            run(["git", "-C", str(dest), "add", "-f", "--", rel], check=False)
        staged = run(["git", "-C", str(dest), "diff", "--cached", "--name-only"]).stdout.strip()
        if not staged:
            print("  up to date — no changes")
            return "unchanged"

        changed = run(["git", "-C", str(dest), "diff", "--cached", "--stat"]).stdout.strip()
        print(changed)

        if dry_run:
            landing = f"auto-merge into {base}" if merge else "leave the PR open"
            print(f"  [dry-run] would commit (+ sync stamp), push, open a PR, and {landing}")
            return "dry-run"

        # Real run: add the provenance stamp on top of the content changes.
        write_stamp(dest, cfg, hub_sha, paths)
        run(["git", "-C", str(dest), "add", "-f", STAMP_REL])
        run(["git", "-C", str(dest), "config", "user.name", "agentarmy-sync"])
        run(["git", "-C", str(dest), "config", "user.email",
             "agentarmy-sync@users.noreply.github.com"])
        run(["git", "-C", str(dest), "commit", "-m",
             f"chore: sync Claude Code helpers from {cfg.get('source_repo')} @ {hub_sha[:7]}"])
        # Plain --force (not --force-with-lease): the shallow `--branch main` clone has no
        # remote-tracking ref for the sync branch, so --force-with-lease fails with
        # "stale info" on re-runs once the branch exists remotely. This branch is
        # bot-owned and regenerated from the hub each run, so unconditional force is safe.
        run(["git", "-C", str(dest), "push", "--force", "origin", branch])

        number = run(["gh", "pr", "list", "--repo", repo, "--head", branch,
                      "--json", "number", "--jq", ".[0].number"], check=False).stdout.strip()
        if not number:
            body = (
                "One-way sync of the Claude Code microVM helper surface from "
                f"`{cfg.get('source_repo')}` (hub is source of truth).\n\n"
                f"**Hub commit:** `{hub_sha}`\n\n**Synced paths:**\n"
                + "\n".join(f"- `{p}`" for p in paths)
                + "\n\nThese are authoritative copies — edit them in the hub, not here. "
                "Generated by `scripts/sync_helpers_to_spokes.py`."
            )
            run(["gh", "pr", "create", "--repo", repo, "--base", base, "--head", branch,
                 "--title", "chore: sync Claude Code helpers from AgentArmy hub", "--body", body])
            number = run(["gh", "pr", "list", "--repo", repo, "--head", branch,
                          "--json", "number", "--jq", ".[0].number"], check=False).stdout.strip()
            print(f"  opened PR #{number}")
        else:
            print(f"  updated PR #{number}")

        if not merge:
            return f"pr#{number} (open)"

        # GitHub computes mergeability asynchronously after a push; merging too soon
        # fails with "not mergeable". Poll until the state is known, then admin-merge
        # (bypasses required checks/reviews, but still needs a conflict-free state).
        state = ""
        for _ in range(15):
            state = run(["gh", "pr", "view", number, "--repo", repo,
                         "--json", "mergeable", "--jq", ".mergeable"], check=False).stdout.strip()
            if state in ("MERGEABLE", "CONFLICTING"):
                break
            time.sleep(2)
        if state == "CONFLICTING":
            print(f"  PR #{number}: conflicts — left open for manual resolution")
            return f"pr#{number} (conflicts)"
        merged = run(["gh", "pr", "merge", number, "--repo", repo,
                      "--squash", "--admin", "--delete-branch"], check=False)
        if merged.returncode != 0:
            print(f"  PR #{number}: auto-merge failed ({merged.stderr.strip()[:140]}) — left open")
            return f"pr#{number} (merge failed)"
        print(f"  merged PR #{number} into {base}")
        return f"merged#{number}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "scripts" / "spoke_sync.config.json")
    parser.add_argument("--spoke", help="Sync only this spoke (repo name).")
    parser.add_argument("--dry-run", action="store_true", help="Clone + diff only; no push/PR.")
    parser.add_argument("--no-merge", action="store_true",
                        help="Open the PR but do not auto-merge (default is to merge into the spoke's main).")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = validate_paths(cfg)
    hub_sha = run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"]).stdout.strip()
    # Land in main by default — an unmerged PR means the helpers never reach the spoke.
    merge = cfg.get("auto_merge", True) and not args.no_merge

    spokes = [args.spoke] if args.spoke else cfg["spokes"]
    if args.spoke and args.spoke not in cfg["spokes"]:
        print(f"warning: '{args.spoke}' is not in config spokes {cfg['spokes']}", file=sys.stderr)

    run(["gh", "auth", "setup-git"], check=False)  # idempotent; ensures git push uses gh auth in CI

    print(f"hub {cfg.get('source_repo')} @ {hub_sha[:7]} -> {len(spokes)} spoke(s)"
          + (" [auto-merge]" if merge else " [PR only]") + (" [DRY RUN]" if args.dry_run else ""))
    results = {}
    for s in spokes:
        try:
            results[s] = sync_spoke(s, cfg, paths, hub_sha, args.dry_run, merge)
        except Exception as e:  # one spoke failing must not abort the others
            results[s] = f"ERROR: {str(e).splitlines()[0][:120]}"
            print(f"  {s}: ERROR — {str(e).splitlines()[0][:160]}")

    print("\n=== summary ===")
    for spoke, res in results.items():
        print(f"  {spoke}: {res}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
