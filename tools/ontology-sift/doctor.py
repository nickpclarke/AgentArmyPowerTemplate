"""Doctor — proves the ARC-ADR-032 thesis offline and deterministically:

  - a conformant fragment SNAPS to canonical with PROV-O lineage
  - a fragment with an under-mediated relator is QUARANTINED at L4 (SHACL)
  - a fragment whose gUFO and BFO classifications disagree is QUARANTINED at L3
    (the reasoner cross-check — pure SHACL would not catch it)
  - nothing plausible-but-unproven reaches the canonical graph

Exit 0 iff every check holds. Run: `python doctor.py` from this directory.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from sift_engine import Engine, SNAPPED, QUARANTINED
from proposer import FixtureProposer

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

_CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, cond, detail: str = "") -> None:
    ok = bool(cond)
    _CHECKS.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


def level(cand, prefix: str):
    for lv in cand.levels:
        if lv["level"].startswith(prefix):
            return lv
    return None


def main() -> int:
    # Force UTF-8 stdout so the report's non-ASCII glyphs never crash under a
    # Windows cp1252 console (a recurring fleet gotcha on Windows runners).
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass
    if OUT.exists():
        shutil.rmtree(OUT)
    proposer = FixtureProposer(HERE / "fixtures" / "proposals")
    engine = Engine(proposer, OUT, repair_budget=2)
    cands = {c.fragment_id: c for c in engine.run(proposer.load())}

    print("ontology-sift doctor — ARC-ADR-032 thin slice\n")
    for fid, c in sorted(cands.items()):
        last_fail = next((lv["level"] for lv in reversed(c.levels) if not lv["ok"]), "—")
        print(f"  · {fid}: state={c.state} repair_round={c.repair_round} first_block={last_fail}")

    print("\nassertions:")
    conf = cands.get("frag-conformant-001")
    check("conformant snaps to canonical", conf and conf.state == SNAPPED)
    check("conformant emits canonical ttl", conf and conf.snapped_to and (OUT / conf.snapped_to).exists())
    check("conformant emits PROV-O lineage", (OUT / "lineage" / "frag-conformant-001.prov.ttl").exists())

    vs = cands.get("frag-violating-shacl-001")
    l4 = level(vs, "L4") if vs else None
    check("under-mediated relator quarantined", vs and vs.state == QUARANTINED)
    check("...blocked at L4 (SHACL)", l4 and not l4["ok"], (l4 or {}).get("detail", ""))
    check("...kept out of canonical", not (OUT / "canonical" / "frag-violating-shacl-001.ttl").exists())

    vr = cands.get("frag-violating-reason-001")
    l3 = level(vr, "L3") if vr else None
    check("gUFO/BFO disagreement quarantined", vr and vr.state == QUARANTINED)
    check("...blocked at L3 (reasoner)", l3 and not l3["ok"], (l3 or {}).get("detail", ""))
    check("...kept out of canonical", not (OUT / "canonical" / "frag-violating-reason-001.ttl").exists())

    canon = sorted((OUT / "canonical").glob("*.ttl"))
    check("ONLY proven fragments reach canonical",
          len(canon) == 1 and canon[0].stem == "frag-conformant-001",
          ", ".join(p.name for p in canon) or "<none>")

    passed = sum(1 for _, ok, _ in _CHECKS if ok)
    total = len(_CHECKS)
    ok = passed == total
    print(f"\n{'ALL PASS' if ok else 'FAILED'} — {passed}/{total} checks")
    print(f"holographic graph: {OUT / 'holographic.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
