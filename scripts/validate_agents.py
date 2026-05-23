#!/usr/bin/env python3
"""Validate agent definition files under .claude/agents/categories/.

Checks, for every agent file (excluding README.md / TAXONOMY.md):
  - frontmatter exists and is parseable YAML
  - required fields present: name, description, tools, model
  - `name` matches the filename (kebab-case stem)
  - `model` is one of the allowed values
  - no duplicate `name` across the whole tree

Exits non-zero (and prints each problem) if any check fails. Run locally with
`python scripts/validate_agents.py`; also run in CI via validate.yml.
"""

import sys
from pathlib import Path
from collections import defaultdict

import yaml

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ALLOWED_MODELS = {"opus", "sonnet", "haiku", "default"}
REQUIRED_FIELDS = ("name", "description", "tools", "model")
SKIP = {"README.md", "TAXONOMY.md"}


def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, "no YAML frontmatter (file does not start with '---')"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "malformed frontmatter (missing closing '---')"
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        return None, f"invalid YAML frontmatter: {e}"
    if not isinstance(meta, dict):
        return None, "frontmatter is not a mapping"
    return meta, None


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    agents_dir = repo_root / ".claude" / "agents" / "categories"

    if not agents_dir.is_dir():
        print(f"ERROR: agents directory not found: {agents_dir}", file=sys.stderr)
        return 1

    errors: list[str] = []
    names_to_files: dict[str, list[str]] = defaultdict(list)
    count = 0

    for path in sorted(agents_dir.rglob("*.md")):
        if path.name in SKIP:
            continue
        count += 1
        rel = path.relative_to(repo_root)

        meta, err = parse_frontmatter(path)
        if err:
            errors.append(f"{rel}: {err}")
            continue

        for field in REQUIRED_FIELDS:
            value = meta.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"{rel}: missing required frontmatter field '{field}'")

        name = meta.get("name")
        if isinstance(name, str) and name.strip():
            stem = path.stem
            if name != stem:
                errors.append(
                    f"{rel}: name '{name}' does not match filename '{stem}'"
                )
            names_to_files[name].append(str(rel))

        model = meta.get("model")
        if isinstance(model, str) and model.strip() and model not in ALLOWED_MODELS:
            errors.append(
                f"{rel}: model '{model}' not in allowed set {sorted(ALLOWED_MODELS)}"
            )

    for name, files in names_to_files.items():
        if len(files) > 1:
            errors.append(f"duplicate agent name '{name}' in: {', '.join(files)}")

    if errors:
        print(f"Validated {count} agent files — {len(errors)} problem(s) found:\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print(f"✓ Validated {count} agent files — all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
