"""Cross-platform MemPalace hook runner for assistant lifecycle hooks."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


SUPPORTED_MEMPALACE_HOOKS = ("session-start", "stop", "precompact")
KNOWN_ASSISTANT_HOOKS = (
    "session-start",
    "user-prompt-submit",
    "pre-tool-use",
    "post-tool-use",
    "stop",
    "precompact",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a MemPalace lifecycle hook.")
    parser.add_argument("--hook", choices=KNOWN_ASSISTANT_HOOKS, required=True)
    parser.add_argument("--harness", default="claude-code")
    args = parser.parse_args()

    if args.hook not in SUPPORTED_MEMPALACE_HOOKS:
        print(
            f"WARNING: MemPalace does not support the {args.hook} hook; skipping.",
            file=sys.stderr,
        )
        return 0

    mempalace = shutil.which("mempalace")
    if mempalace is None:
        print(
            f"WARNING: mempalace is not on PATH; skipping MemPalace {args.hook} hook.",
            file=sys.stderr,
        )
        return 0

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    completed = subprocess.run(
        [
            mempalace,
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
