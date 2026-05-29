"""board-sync doctor — proves the vended adapters turn real-shaped GitHub v2 + Linear
work items into the SAME canonical WorkItem shape, with the required fields present.
The container's correctness gate (no docker needed to run this proof). Exit 0 on pass."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply import REQUIRED, apply_adapter, load_adapter, missing_required  # noqa: E402

HERE = Path(__file__).resolve().parent
import json  # noqa: E402


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    cases = [
        ("linear", HERE / "adapters/linear.workitem.json", HERE / "samples/linear-issue.json"),
        ("github", HERE / "adapters/github.workitem.json", HERE / "samples/github-issue.json"),
    ]
    print("board-sync doctor — proven adapters: source payload -> canonical WorkItem")
    print("-" * 70)
    ok = True
    produced: dict[str, dict] = {}
    for name, apath, spath in cases:
        adapter = load_adapter(apath)
        item = apply_adapter(adapter, _load(spath))
        produced[name] = item
        miss = missing_required(item)
        passed = not miss
        ok = ok and passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name:7} -> Identifier={item.get('Identifier')!r} "
              f"Title={str(item.get('Title'))[:28]!r} Status={item.get('Status')!r} Sprint={item.get('Sprint')!r}")
        if miss:
            print(f"        missing required: {miss}")
    # unification: both surfaces produce the SAME required canonical fields
    keys = [set(k for k in it if not k.startswith("_")) for it in produced.values()]
    shared = set.intersection(*keys) if keys else set()
    unified = set(REQUIRED).issubset(shared)
    print("-" * 70)
    print(f"[{'PASS' if unified else 'FAIL'}] unified canonical shape — shared fields: {sorted(shared)}")
    ok = ok and unified
    if ok:
        print("\nALL PASS — GitHub v2 and Linear items normalize to one canonical WorkItem.")
        return 0
    print("\nFAIL — an adapter did not produce a complete canonical WorkItem.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
