"""sync mode — fetch live board items, apply the vended adapter, emit canonical
WorkItems. Proven against the AgentArmy GitHub Projects v2 board (token from
akv:GithubPAT). Linear runs the same way once a workspace key is supplied."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import connectors  # noqa: E402
from apply import apply_adapter, load_adapter, missing_required  # noqa: E402


def main() -> int:
    source = os.environ.get("BOARD_SOURCE", "github")
    adapter = load_adapter(HERE / f"adapters/{source}.workitem.json")
    if source == "github":
        items = connectors.github_v2_items()
    else:
        raise SystemExit(f"connector for {source!r} not wired (Linear needs a workspace key)")
    workitems = [apply_adapter(adapter, p) for p in items]
    safe = [w for w in workitems if not missing_required(w)]
    print(json.dumps({
        "source": source, "fetched": len(items), "runtime_safe": len(safe),
        "workitems": workitems,
    }, indent=2, default=str))
    return 0 if safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
