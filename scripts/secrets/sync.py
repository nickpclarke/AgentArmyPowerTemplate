"""Pull secrets from akv01-agentarmy → local .env / .secrets files.

Reads scripts/secrets/secrets-manifest.json; for each entry, calls
`az keyvault secret show` and writes the value to the declared local target.

Two target types:
  env_file    — sets `<KEY>=<value>` line in a .env file (creates or updates).
  secret_file — writes the raw value to a file (single-secret-per-file pattern
                used by docker-compose Docker secrets and backend-core's
                ARCADEDB_PASSWORD_FILE convention).

Security:
  - Values are never echoed to stdout. Only secret NAMES + write targets are
    printed. The script's exit code reflects overall success.
  - umask 0o077 set before writing — files end up owner-readable only on POSIX.
    On Windows, ACL inheritance from the user profile already accomplishes this.
  - All target paths are validated to live UNDER the hub repo OR a sibling
    spoke directory (one level up, no traversal beyond that). No absolute paths,
    no `..` deeper than the parent.

Usage:
  python scripts/secrets/sync.py             # apply all entries
  python scripts/secrets/sync.py --dry-run   # show what would change, no writes
  python scripts/secrets/sync.py --only KV_NAME[,KV_NAME...]   # subset
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = HUB_ROOT / "scripts" / "secrets" / "secrets-manifest.json"
DEFAULT_VAULT = "akv01-agentarmy"


@dataclass
class Entry:
    kv_name: str
    description: str
    consumer: str
    target_type: str  # "env_file" or "secret_file"
    target_path: Path  # absolute, validated
    target_key: str | None  # only for env_file


def _safe_target_path(raw: str) -> Path:
    """Resolve `raw` relative to HUB_ROOT; reject if it escapes the workspace.

    Valid scopes: under HUB_ROOT itself OR under a sibling at ../<spoke>.
    Anything else (drive-absolute, deeper-up traversal) is rejected so a
    manifest typo can't clobber arbitrary files on the system.
    """
    candidate = (HUB_ROOT / raw).resolve()
    workspace_root = HUB_ROOT.parent.resolve()  # the C:/Dev/ (or equivalent) parent
    try:
        candidate.relative_to(workspace_root)
    except ValueError:
        raise ValueError(
            f"Target path {raw!r} resolves outside the workspace ({workspace_root}); refusing."
        )
    return candidate


def load_manifest(only: set[str] | None = None) -> tuple[str, list[Entry]]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"manifest not found: {MANIFEST_PATH}")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    vault = data.get("vault") or DEFAULT_VAULT
    entries: list[Entry] = []
    for raw in data.get("secrets", []):
        kv_name = raw["kv_name"]
        if only and kv_name not in only:
            continue
        write = raw["writes_to"]
        entries.append(
            Entry(
                kv_name=kv_name,
                description=raw.get("description", ""),
                consumer=raw.get("consumer", "?"),
                target_type=write["type"],
                target_path=_safe_target_path(write["path"]),
                target_key=write.get("key"),
            )
        )
    return vault, entries


def _az_executable() -> str:
    """Return the full path to the `az` CLI executable.

    On Windows the CLI ships as `az.CMD` and Python's subprocess refuses to
    invoke `.cmd`/`.bat` shims unless the absolute path is used. shutil.which
    handles the `.CMD` extension correctly via PATHEXT.
    """
    exe = shutil.which("az")
    if not exe:
        raise EnvironmentError(
            "az CLI not on PATH. Install Azure CLI and `az login` first."
        )
    return exe


def _az_secret_value(vault: str, name: str) -> str:
    """Fetch a single secret value via `az keyvault secret show`.

    Returned bytes are stripped of a trailing newline. The az CLI itself does
    NOT log the value to its diagnostic logs by default.
    """
    result = subprocess.run(
        [_az_executable(), "keyvault", "secret", "show",
         "--vault-name", vault,
         "--name", name,
         "--query", "value",
         "-o", "tsv"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"az keyvault secret show failed for {name!r}: "
            f"{result.stderr.strip() or '(no stderr)'}"
        )
    value = result.stdout.rstrip("\n").rstrip("\r")
    if not value:
        raise RuntimeError(f"empty value returned for secret {name!r}")
    return value


def _update_env_file(path: Path, key: str, value: str) -> str:
    """Upsert KEY=value in a .env file, preserving other lines.

    Returns "created" | "updated" | "unchanged".
    """
    # Strict key pattern — refuses anything that could break .env parsing.
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
        raise ValueError(f"refusing to write non-standard env key {key!r}")

    line = f"{key}={value}\n"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(line, encoding="utf-8")
        return "created"

    existing = path.read_text(encoding="utf-8").splitlines(keepends=True)
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=", re.ASCII)
    replaced = False
    out_lines: list[str] = []
    for existing_line in existing:
        if not replaced and pattern.match(existing_line):
            if existing_line == line:
                # exact match — no-op
                path.write_text("".join(existing), encoding="utf-8")
                return "unchanged"
            out_lines.append(line)
            replaced = True
        else:
            out_lines.append(existing_line)
    if not replaced:
        if out_lines and not out_lines[-1].endswith("\n"):
            out_lines[-1] = out_lines[-1] + "\n"
        out_lines.append(line)
    path.write_text("".join(out_lines), encoding="utf-8")
    return "updated"


def _write_secret_file(path: Path, value: str) -> str:
    """Overwrite path with `value` (no newline). Returns created|updated|unchanged."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.read_bytes()
        new_bytes = value.encode("utf-8")
        if current == new_bytes:
            return "unchanged"
        path.write_bytes(new_bytes)
        return "updated"
    path.write_bytes(value.encode("utf-8"))
    return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync fleet secrets from Key Vault to local files.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report which files would change without writing.")
    parser.add_argument("--only", default="",
                        help="Comma-separated KV names to limit the sync to (default: all).")
    args = parser.parse_args(argv)

    # Owner-readable only when we create files (POSIX). On Windows the user's
    # NTFS ACLs inherit from the profile and already restrict to the user.
    if hasattr(os, "umask"):
        os.umask(0o077)

    only = {s.strip() for s in args.only.split(",") if s.strip()} if args.only else None
    vault, entries = load_manifest(only)
    if not entries:
        print("No manifest entries to sync (after --only filter).", file=sys.stderr)
        return 1

    print(f"Vault: {vault}")
    print(f"Mode:  {'DRY RUN — no writes' if args.dry_run else 'APPLY'}")
    print("-" * 72)

    failures = 0
    for entry in entries:
        rel = entry.target_path.relative_to(HUB_ROOT.parent)
        label = (
            f"{entry.kv_name:<24} -> {rel}"
            + (f"::{entry.target_key}" if entry.target_key else "")
        )
        try:
            if args.dry_run:
                # Confirm the secret EXISTS without reading the value (--query name).
                probe = subprocess.run(
                    [_az_executable(), "keyvault", "secret", "show",
                     "--vault-name", vault, "--name", entry.kv_name,
                     "--query", "name", "-o", "tsv"],
                    capture_output=True, text=True, check=False,
                )
                if probe.returncode != 0:
                    raise RuntimeError(probe.stderr.strip() or "unknown az error")
                print(f"  WOULD SYNC  {label}")
                continue

            value = _az_secret_value(vault, entry.kv_name)
            try:
                if entry.target_type == "env_file":
                    if not entry.target_key:
                        raise ValueError("env_file target requires `key`")
                    result = _update_env_file(entry.target_path, entry.target_key, value)
                elif entry.target_type == "secret_file":
                    result = _write_secret_file(entry.target_path, value)
                else:
                    raise ValueError(f"unknown target type: {entry.target_type}")
            finally:
                # Drop the value from local scope ASAP.
                value = ""  # noqa: F841
            print(f"  [{result:<9}] {label}")
        except Exception as exc:
            failures += 1
            print(f"  [FAIL     ] {label}  -- {exc}", file=sys.stderr)

    print("-" * 72)
    if failures == 0:
        print(f"OK  {len(entries)} secret(s) processed")
        return 0
    print(f"FAIL  {failures} of {len(entries)} failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
