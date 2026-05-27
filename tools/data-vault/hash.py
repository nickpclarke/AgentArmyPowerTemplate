#!/usr/bin/env python3
"""Data Vault 2.1 — canonical SHA-256 hash key / hash diff library (Python).

Bit-identical to tools/data-vault/hash.mjs. Shared test vectors live in
hash.vectors.json. See docs/data-vault/strategy.md §3 for the algorithm.

CLI:
  python hash.py --help
  python hash.py --hub  customer_id --value C-12345
  python hash.py --link customer_id=C-12345 order_id=O-99
  python hash.py --diff first_name=Ada last_name=Lovelace email=null
  python hash.py --test
  python hash.py --update-vectors
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Sequence

VECTORS_PATH = Path(__file__).resolve().parent / "hash.vectors.json"

DEFAULTS = {
    "hash_algorithm": "sha256",
    "separator": "||",
    "null_sentinel": "^^",
    "case_fold": "upper",
    "trim": True,
    "unicode_form": "NFC",
}


def normalize_business_key(value: Any, opts: Mapping[str, Any] = DEFAULTS, *, case_sensitive: bool = False) -> str:
    if value is None:
        return opts["null_sentinel"]
    s = str(value)
    uform = opts.get("unicode_form", "NFC")
    if uform and uform != "none":
        s = unicodedata.normalize(uform, s)
    if opts.get("trim", True):
        s = s.strip()
    if not case_sensitive:
        cf = opts.get("case_fold", "upper")
        if cf == "upper":
            s = s.upper()
        elif cf == "lower":
            s = s.lower()
    return s


def normalize_attribute(value: Any, opts: Mapping[str, Any] = DEFAULTS) -> str:
    if value is None:
        return opts["null_sentinel"]
    s = str(value)
    uform = opts.get("unicode_form", "NFC")
    if uform and uform != "none":
        s = unicodedata.normalize(uform, s)
    # Descriptive attributes: preserve case + whitespace.
    return s


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hub_hash(
    values: Mapping[str, Any],
    business_keys: Sequence[str] | None = None,
    opts: Mapping[str, Any] = DEFAULTS,
    case_sensitive_map: Mapping[str, bool] | None = None,
) -> str:
    keys = list(business_keys) if business_keys is not None else list(values.keys())
    cs = case_sensitive_map or {}
    parts = [normalize_business_key(values.get(k), opts, case_sensitive=cs.get(k, False)) for k in keys]
    return sha256_hex(opts["separator"].join(parts))


link_hash = hub_hash


def sat_hash_diff(attributes: Mapping[str, Any], opts: Mapping[str, Any] = DEFAULTS) -> str:
    names = sorted(attributes.keys())
    parts = [normalize_attribute(attributes[n], opts) for n in names]
    return sha256_hex(opts["separator"].join(parts))


# ---------- Tests ---------------------------------------------------------


def run_tests(update_vectors: bool = False) -> int:
    vectors = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    opts = {**DEFAULTS, **vectors.get("config", {})}
    failures: list[str] = []

    for v in vectors["hub_keys"]:
        cs = v.get("case_sensitive", {})
        normalized_parts = [
            normalize_business_key(v["values"].get(k), opts, case_sensitive=bool(cs.get(k, False)))
            for k in v["business_keys"]
        ]
        normalized = opts["separator"].join(normalized_parts)
        h = sha256_hex(normalized)
        if normalized != v["expected_normalized"]:
            failures.append(f'HUB "{v["name"]}": normalized="{normalized}" expected="{v["expected_normalized"]}"')
        if update_vectors:
            v["expected_hash"] = h
        elif v["expected_hash"] != "_computed_at_runtime" and v["expected_hash"] != h:
            failures.append(f'HUB "{v["name"]}": hash={h} expected={v["expected_hash"]}')

    for v in vectors["sat_hash_diffs"]:
        names = sorted(v["attributes"].keys())
        normalized_parts = [normalize_attribute(v["attributes"][n], opts) for n in names]
        normalized = opts["separator"].join(normalized_parts)
        h = sha256_hex(normalized)
        if normalized != v["expected_normalized"]:
            failures.append(f'SAT "{v["name"]}": normalized="{normalized}" expected="{v["expected_normalized"]}"')
        if update_vectors:
            v["expected_hash"] = h
        elif v["expected_hash"] != "_computed_at_runtime" and v["expected_hash"] != h:
            failures.append(f'SAT "{v["name"]}": hash={h} expected={v["expected_hash"]}')

    if update_vectors:
        VECTORS_PATH.write_text(json.dumps(vectors, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {VECTORS_PATH}")
        return 0
    if failures:
        for f in failures:
            print("  FAIL: " + f, file=sys.stderr)
        print(f"\n{len(failures)} test failure(s).", file=sys.stderr)
        return 1
    print(f'OK: {len(vectors["hub_keys"])} hub + {len(vectors["sat_hash_diffs"])} sat vectors passed.')
    return 0


# ---------- CLI -----------------------------------------------------------


def _value_or_null(v: str | None) -> Any:
    if v is None:
        return None
    if v in ("null", "NULL"):
        return None
    return v


def _parse_pairs(pairs: Sequence[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for p in pairs:
        if "=" not in p:
            raise SystemExit(f"Bad pair (need key=value): {p}")
        k, v = p.split("=", 1)
        out[k] = _value_or_null(v)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="hash.py",
        description="Data Vault 2.1 canonical hash library (Python).",
    )
    p.add_argument("--hub", help="single-column hub hash; combine with --value")
    p.add_argument("--value", help="value for --hub (use 'null' for NULL)")
    p.add_argument("--link", action="store_true", help="link/composite hash from key=value pairs")
    p.add_argument("--diff", action="store_true", help="sat hash diff from attribute=value pairs")
    p.add_argument("--test", action="store_true", help="run vector tests")
    p.add_argument("--update-vectors", action="store_true", help="recompute expected_hash in hash.vectors.json")
    p.add_argument("pairs", nargs="*", help="key=value pairs for --link / --diff")
    args = p.parse_args(argv)

    if args.test:
        return run_tests()
    if args.update_vectors:
        return run_tests(update_vectors=True)

    if args.hub:
        values = {args.hub: _value_or_null(args.value)}
        print(hub_hash(values, [args.hub]))
        return 0

    if args.link or args.diff:
        values = _parse_pairs(args.pairs)
        if args.diff:
            print(sat_hash_diff(values))
        else:
            print(hub_hash(values, list(values.keys())))
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
