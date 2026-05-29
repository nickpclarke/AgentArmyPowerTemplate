"""abstraction-mcp doctor — proves the MCP image's payload is correct WITHOUT a backend
or docker: both tools are registered, the HTTP surface mounts at /abstract, and the proxy
refuses a non-http backend URL (so keys never leave backend-core). Exit 0 on pass."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# container: server.py/client.py copied next to doctor.py. local dev: tools/mcp-abstraction/.
for _cand in (HERE, HERE.parents[1] / "tools" / "mcp-abstraction"):
    if (_cand / "server.py").exists():
        sys.path.insert(0, str(_cand))
        break

import client  # noqa: E402
import server  # noqa: E402

EXPECTED_TOOLS = {"abstract_schemas", "build_adapter"}


def main() -> int:
    print("abstraction-mcp doctor — payload correctness (no backend, no docker)")
    print("-" * 70)
    ok = True

    tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
    for name in sorted(EXPECTED_TOOLS):
        present = name in tools
        ok = ok and present
        print(f"[{'PASS' if present else 'FAIL'}] tool registered: {name}")

    path = server.mcp.settings.streamable_http_path
    path_ok = path == "/abstract"
    ok = ok and path_ok
    print(f"[{'PASS' if path_ok else 'FAIL'}] streamable-http surface mounts at /abstract (got {path!r})")

    # The proxy must refuse a non-http backend (defends against scheme confusion / SSRF).
    os.environ["ABSTRACTION_API_URL"] = "ftp://evil.example"
    try:
        client._api_base()
        guard_ok = False
    except ValueError:
        guard_ok = True
    finally:
        os.environ.pop("ABSTRACTION_API_URL", None)
    ok = ok and guard_ok
    print(f"[{'PASS' if guard_ok else 'FAIL'}] proxy rejects non-http backend URL (keys stay server-side)")

    print("-" * 70)
    if ok:
        print("ALL PASS — tools exposed at /abstract; backend stays a proxy target, never exposed.")
        return 0
    print("FAIL — image payload incorrect.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
