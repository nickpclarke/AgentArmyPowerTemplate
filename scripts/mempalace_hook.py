"""Cross-platform MemPalace hook runner for assistant lifecycle hooks."""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys


SUPPORTED_MEMPALACE_HOOKS = ("session-start", "stop", "precompact")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a MemPalace lifecycle hook.")
    parser.add_argument("--hook", required=True)
    parser.add_argument("--harness", default="claude-code")
    args = parser.parse_args()

    if args.hook not in SUPPORTED_MEMPALACE_HOOKS:
        print(
            f"WARNING: MemPalace does not support the {args.hook} hook; skipping.",
            file=sys.stderr,
        )
        return 0

    # Invoke via the current interpreter, not a PATH lookup. Claude Code runs
    # hooks through a minimal-PATH Git Bash that can omit the Python Scripts dir.
    if importlib.util.find_spec("mempalace") is None:
        print(
            f"WARNING: mempalace package not importable; skipping MemPalace {args.hook} hook.",
            file=sys.stderr,
        )
        return 0

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mempalace",
            "hook",
            "run",
            "--hook",
            args.hook,
            "--harness",
            args.harness,
        ],
        env=env,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
