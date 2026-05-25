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
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STAMP_REL = ".claude/.agentarmy-sync.json"
# Always-ignored when copying a directory tree, regardless of config.
COPY_IGNORE = [".git", "__pycache__", "node_modules", "*.local.json", "worktrees"]


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


def sync_spoke(spoke: str, cfg: dict, paths: list[str], hub_sha: str, dry_run: bool) -> str:
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

        run(["git", "-C", str(dest), "add", "-A"])
        staged = run(["git", "-C", str(dest), "diff", "--cached", "--name-only"]).stdout.strip()
        if not staged:
            print("  up to date — no changes")
            return "unchanged"

        changed = run(["git", "-C", str(dest), "diff", "--cached", "--stat"]).stdout.strip()
        print(changed)

        if dry_run:
            print("  [dry-run] would commit the above + a sync stamp, push, and open a PR")
            return "dry-run"

        # Real run: add the provenance stamp on top of the content changes.
        write_stamp(dest, cfg, hub_sha, paths)
        run(["git", "-C", str(dest), "add", STAMP_REL])
        run(["git", "-C", str(dest), "config", "user.name", "agentarmy-sync"])
        run(["git", "-C", str(dest), "config", "user.email",
             "agentarmy-sync@users.noreply.github.com"])
        run(["git", "-C", str(dest), "commit", "-m",
             f"chore: sync Claude Code helpers from {cfg.get('source_repo')} @ {hub_sha[:7]}"])
        run(["git", "-C", str(dest), "push", "--force-with-lease", "origin", branch])

        existing = run(["gh", "pr", "list", "--repo", repo, "--head", branch,
                        "--json", "number", "--jq", ".[0].number"], check=False).stdout.strip()
        if existing:
            print(f"  updated existing PR #{existing}")
            return f"pr#{existing}"
        body = (
            "One-way sync of the Claude Code microVM helper surface from "
            f"`{cfg.get('source_repo')}` (hub is source of truth).\n\n"
            f"**Hub commit:** `{hub_sha}`\n\n**Synced paths:**\n"
            + "\n".join(f"- `{p}`" for p in paths)
            + "\n\nThese are authoritative copies — edit them in the hub, not here. "
            "Generated by `scripts/sync_helpers_to_spokes.py`."
        )
        url = run(["gh", "pr", "create", "--repo", repo, "--base", base, "--head", branch,
                   "--title", "chore: sync Claude Code helpers from AgentArmy hub",
                   "--body", body]).stdout.strip()
        print(f"  opened PR: {url}")
        return url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "scripts" / "spoke_sync.config.json")
    parser.add_argument("--spoke", help="Sync only this spoke (repo name).")
    parser.add_argument("--dry-run", action="store_true", help="Clone + diff only; no push/PR.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = validate_paths(cfg)
    hub_sha = run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"]).stdout.strip()

    spokes = [args.spoke] if args.spoke else cfg["spokes"]
    if args.spoke and args.spoke not in cfg["spokes"]:
        print(f"warning: '{args.spoke}' is not in config spokes {cfg['spokes']}", file=sys.stderr)

    run(["gh", "auth", "setup-git"], check=False)  # idempotent; ensures git push uses gh auth in CI

    print(f"hub {cfg.get('source_repo')} @ {hub_sha[:7]} -> {len(spokes)} spoke(s)"
          + (" [DRY RUN]" if args.dry_run else ""))
    results = {s: sync_spoke(s, cfg, paths, hub_sha, args.dry_run) for s in spokes}

    print("\n=== summary ===")
    for spoke, res in results.items():
        print(f"  {spoke}: {res}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
