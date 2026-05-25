#!/usr/bin/env python3
"""
Check for drift between the committed generated code and a fresh regeneration.

This is the drift gate: it regenerates in a temp dir and byte-for-byte compares
against the committed tree. EOL differences are caught. Exit 0 if clean, non-zero
if any differences found.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def resolve_repo_root() -> Path:
    """Resolve the repository root from this script's location."""
    script = Path(__file__).resolve()
    return script.parents[2]


def run_generator(model: Path, out_dir: Path, repo_root: Path) -> bool:
    """Run the generator subprocess. Return True if success, False otherwise."""
    generator = repo_root / "tools" / "modelgen" / "generate_middle_core.py"
    result = subprocess.run(
        [sys.executable, str(generator), "--model", str(model), "--out", str(out_dir)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Generator failed: {result.stdout}\n{result.stderr}")
        return False
    return True


def compare_trees(temp_dir: Path, committed_dir: Path) -> tuple[bool, list[str]]:
    """
    Byte-for-byte compare temp_dir against committed_dir.
    Return (is_identical, list of differences).
    """
    differences = []

    # Collect all files from both dirs.
    temp_files = set()
    committed_files = set()

    if temp_dir.exists():
        for path in temp_dir.rglob("*"):
            if path.is_file():
                temp_files.add(path.relative_to(temp_dir))

    if committed_dir.exists():
        for path in committed_dir.rglob("*"):
            if path.is_file():
                committed_files.add(path.relative_to(committed_dir))

    # Check for added files.
    added = temp_files - committed_files
    if added:
        for rel_path in sorted(added):
            differences.append(f"  ADDED: {rel_path}")

    # Check for removed files.
    removed = committed_files - temp_files
    if removed:
        for rel_path in sorted(removed):
            differences.append(f"  REMOVED: {rel_path}")

    # Check for changed files.
    common = temp_files & committed_files
    for rel_path in sorted(common):
        temp_content = (temp_dir / rel_path).read_bytes()
        committed_content = (committed_dir / rel_path).read_bytes()
        if temp_content != committed_content:
            differences.append(f"  CHANGED: {rel_path}")

    return len(differences) == 0, differences


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Drift gate: regenerate and compare against committed generated code."
    )
    parser.add_argument(
        "--model",
        type=Path,
        help="Path to model.yaml (default: <repo>/model/middle-core/model.yaml)",
    )
    parser.add_argument(
        "--generated",
        type=Path,
        help="Path to generated dir (default: <repo>/templates/middle-core/generated)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Regenerate in place (write mode), do not check for drift.",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root()

    if not args.model:
        args.model = repo_root / "model" / "middle-core" / "model.yaml"
    if not args.generated:
        args.generated = repo_root / "templates" / "middle-core" / "generated"

    args.model = args.model.resolve()
    args.generated = args.generated.resolve()

    if not args.model.exists():
        print(f"ERROR: model not found: {args.model}")
        return 1

    if args.write:
        # Regen in place.
        if not run_generator(args.model, args.generated, repo_root):
            return 1
        print(f"Regenerated into {args.generated}")
        return 0

    # Gate mode: regenerate in temp dir and compare.
    with tempfile.TemporaryDirectory() as temp:
        temp_out = Path(temp) / "generated"
        if not run_generator(args.model, temp_out, repo_root):
            return 1

        is_clean, differences = compare_trees(temp_out, args.generated)

        if is_clean:
            print("Generated code is in sync with model (no drift detected).")
            return 0

        print("DRIFT DETECTED: generated code differs from model:")
        for diff in differences:
            print(diff)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
