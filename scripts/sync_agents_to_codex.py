#!/usr/bin/env python3
"""
Sync Claude agent definitions (.claude/agents/categories/)
to Codex custom agents (.codex/agents/) as TOML profiles.
"""

import re
from pathlib import Path

# PyYAML is preferred, but this script is SYNCED into spoke repos and run by the Codex
# SessionStart hook (.codex/hooks.json). A fresh Codex microVM / spoke may not have
# PyYAML installed — a hard `import yaml` would crash the startup hook. So we degrade to
# a tiny stdlib parser that reads the only two frontmatter fields we need (name,
# description). The static .codex/agents/*.toml are already shipped by the dressing sync,
# so the hook is a refresh, not a hard dependency.
try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    yaml = None  # type: ignore


def _parse_frontmatter(block: str) -> dict:
    """Parse a YAML frontmatter block. Uses PyYAML when present; otherwise a minimal
    stdlib fallback sufficient for agent frontmatter (top-level `key: value`, with
    quoted values and indented continuation lines)."""
    if yaml is not None:
        data = yaml.safe_load(block)  # type: ignore[union-attr]
        return data if isinstance(data, dict) else {}
    meta: dict = {}
    key = None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9_-]+):\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1]
            meta[key] = val
        elif key and line[:1] in (' ', '\t'):  # folded continuation of the previous value
            meta[key] = (str(meta.get(key, '')) + ' ' + line.strip()).strip()
    return meta


def parse_agent_file(file_path: Path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        meta = _parse_frontmatter(parts[1])
        instructions = parts[2].strip()

        return {
            'name': meta.get('name', ''),
            'description': meta.get('description', ''),
            'developer_instructions': instructions
        }
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None

def main():
    repo_root = Path(__file__).parent.parent
    agents_dir = repo_root / '.claude' / 'agents' / 'categories'
    codex_agents_dir = repo_root / '.codex' / 'agents'

    # Create destination directory if it doesn't exist
    codex_agents_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing generated agents to avoid stale profiles
    if codex_agents_dir.exists():
        for existing_file in codex_agents_dir.glob('*.toml'):
            try:
                existing_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete {existing_file}: {e}")

    # Scan and process agents
    count = 0
    for md_file in agents_dir.rglob('*.md'):
        if md_file.name in ['README.md', 'TAXONOMY.md', '.md']:
            continue

        agent_data = parse_agent_file(md_file)
        if not agent_data or not agent_data['name']:
            continue

        name = agent_data['name']
        description = agent_data['description']
        instructions = agent_data['developer_instructions']

        # Construct the TOML representation
        # Escape triple quotes inside the instructions to prevent syntax errors
        escaped_instructions = instructions.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
        
        toml_content = f"""# Auto-generated from {md_file.relative_to(repo_root).as_posix()}
# DO NOT EDIT DIRECTLY. Run scripts/sync_agents_to_codex.py to update.

name = {repr(name)}
description = {repr(description)}
developer_instructions = \"\"\"
{escaped_instructions}
\"\"\"
"""
        # Save as name.toml using a standardized safe filename
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', name).lower() + '.toml'
        dest_path = codex_agents_dir / safe_filename
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(toml_content)
        count += 1

    print(f"Successfully synced {count} agents to .codex/agents/")

if __name__ == '__main__':
    main()
