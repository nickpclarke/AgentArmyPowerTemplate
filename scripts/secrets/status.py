"""Report freshness of local secrets vs Key Vault.

For each entry in scripts/secrets/secrets-manifest.json:
  - Reads KV `attributes.updated` and `attributes.expires` (no value).
  - Reads the local target's mtime (or marks "missing" if absent).
  - Reports stale / current / missing / unknown per row.

This script ONLY READS — it never writes a file and never echoes a secret
value. Safe to run on a cadence (heartbeat, CI). Exit code: 0 if all rows are
"current"; 1 if any row is "stale" or "missing"; 2 on configuration error.

Usage:
  python scripts/secrets/status.py           # human-readable table
  python scripts/secrets/status.py --json    # machine-readable
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = HUB_ROOT / "scripts" / "secrets" / "secrets-manifest.json"
DEFAULT_VAULT = "akv01-agentarmy"


@dataclass
class Row:
    kv_name: str
    consumer: str
    target: str
    kv_updated: str | None     # ISO 8601 from KV
    kv_expires: str | None     # ISO 8601 from KV (may be None — no expiry set)
    local_mtime: str | None    # ISO 8601 from filesystem
    state: str                 # "current" | "stale" | "missing" | "unknown" | "error"
    detail: str                # free-form (mostly for error rows)


def _safe_target_path(raw: str) -> Path:
    candidate = (HUB_ROOT / raw).resolve()
    workspace_root = HUB_ROOT.parent.resolve()
    try:
        candidate.relative_to(workspace_root)
    except ValueError:
        raise ValueError(f"target path {raw!r} escapes workspace")
    return candidate


def _az_executable() -> str:
    exe = shutil.which("az")
    if not exe:
        raise EnvironmentError("az CLI not on PATH; run `az login` and retry.")
    return exe


def _az_attrs(vault: str, name: str) -> tuple[str | None, str | None]:
    """Return (updated_iso, expires_iso) without ever fetching the value."""
    result = subprocess.run(
        [_az_executable(), "keyvault", "secret", "show",
         "--vault-name", vault,
         "--name", name,
         "--query", "{updated:attributes.updated, expires:attributes.expires}",
         "-o", "json"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "az command failed")
    parsed = json.loads(result.stdout)
    return parsed.get("updated"), parsed.get("expires")


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    # az returns timestamps like "2026-05-26T20:42:00+00:00"
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def evaluate(vault: str, manifest_entries: list[dict]) -> list[Row]:
    rows: list[Row] = []
    now = datetime.now(timezone.utc)
    for raw in manifest_entries:
        kv_name = raw["kv_name"]
        write = raw["writes_to"]
        target_path = _safe_target_path(write["path"])
        target_label = (
            f"{target_path.relative_to(HUB_ROOT.parent)}"
            + (f"::{write['key']}" if write.get("key") else "")
        )
        kv_updated_iso = None
        kv_expires_iso = None
        local_mtime_iso = None
        state = "unknown"
        detail = ""

        try:
            kv_updated_iso, kv_expires_iso = _az_attrs(vault, kv_name)
        except Exception as exc:
            rows.append(Row(
                kv_name=kv_name, consumer=raw.get("consumer", "?"),
                target=target_label, kv_updated=None, kv_expires=None,
                local_mtime=None, state="error", detail=str(exc),
            ))
            continue

        if not target_path.exists():
            state = "missing"
            detail = "local file absent — run `python scripts/secrets/sync.py`"
        else:
            mtime = datetime.fromtimestamp(target_path.stat().st_mtime, tz=timezone.utc)
            local_mtime_iso = mtime.isoformat()
            kv_updated = _parse_iso(kv_updated_iso)
            if kv_updated and kv_updated > mtime:
                state = "stale"
                detail = "KV value updated AFTER local file mtime — re-sync."
            else:
                state = "current"

        kv_expires = _parse_iso(kv_expires_iso)
        if kv_expires and kv_expires < now:
            # Expiry trumps everything — the KV value itself is expired.
            state = "stale"
            detail = (detail + "; " if detail else "") + f"KV secret expired at {kv_expires_iso}"

        rows.append(Row(
            kv_name=kv_name, consumer=raw.get("consumer", "?"),
            target=target_label, kv_updated=kv_updated_iso,
            kv_expires=kv_expires_iso, local_mtime=local_mtime_iso,
            state=state, detail=detail,
        ))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report freshness of local secrets vs Key Vault.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human table.")
    args = parser.parse_args(argv)

    if not MANIFEST_PATH.exists():
        print(f"manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 2
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    vault = manifest.get("vault") or DEFAULT_VAULT

    try:
        rows = evaluate(vault, manifest.get("secrets", []))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    bad = sum(1 for r in rows if r.state in {"stale", "missing", "error"})

    if args.json:
        print(json.dumps(
            {"vault": vault, "checked": len(rows), "issues": bad,
             "rows": [asdict(r) for r in rows]},
            indent=2,
        ))
    else:
        print(f"Vault: {vault}")
        print(f"Checked {len(rows)} secret(s); {bad} need attention.\n")
        # column widths
        kv_w = max((len(r.kv_name) for r in rows), default=8) + 2
        cons_w = max((len(r.consumer) for r in rows), default=8) + 2
        state_w = 8
        print(f"{'STATE':<{state_w}} {'KV_NAME':<{kv_w}} {'CONSUMER':<{cons_w}} TARGET")
        print("-" * 72)
        for r in rows:
            mark = {
                "current": "ok",
                "stale":   "STALE",
                "missing": "MISSING",
                "error":   "ERROR",
                "unknown": "?",
            }.get(r.state, r.state)
            print(f"{mark:<{state_w}} {r.kv_name:<{kv_w}} {r.consumer:<{cons_w}} {r.target}")
            if r.detail:
                print(f"{'':<{state_w}}   -- {r.detail}")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
