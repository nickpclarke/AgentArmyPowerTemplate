#!/usr/bin/env python3
"""
Generate agent documentation pages from .claude/agents/categories definitions.

This script reads agent definition files and generates mkdocs-compatible markdown
pages in docs/agents/ directory. This is "documents as code" - documentation
is generated from source definitions to avoid duplication.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from collections import defaultdict


def parse_agent_file(file_path: Path) -> Optional[Dict]:
    """
    Parse an agent definition file and extract frontmatter + description.

    Returns: Dict with 'meta' (YAML frontmatter) and 'content' (markdown)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Split frontmatter and content
        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        # Parse YAML frontmatter
        meta = yaml.safe_load(parts[1])
        description_text = parts[2].strip()

        return {
            'name': meta.get('name', ''),
            'description': meta.get('description', ''),
            'tools': meta.get('tools', []),
            'model': meta.get('model', 'default'),
            'tools_list': [t.strip() for t in str(meta.get('tools', '')).split(',')],
            'file_path': str(file_path.relative_to(Path(__file__).parent.parent)),
            'content': description_text,
            'category': extract_category(file_path),
        }
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def extract_category(file_path: Path) -> str:
    """Extract the category from the file path."""
    parts = file_path.parts
    for part in parts:
        if part.startswith(('0', '1')) and '-' in part:
            # Extract the human-readable part (e.g., "01-core-development")
            return part.split('-', 1)[1].replace('-', ' ').title()
    return "Uncategorized"


def get_all_agents(agents_dir: Path) -> Dict[str, List[Dict]]:
    """
    Scan all agent definition files and group by category.

    Returns: Dict[category] -> List[agent_dict]
    """
    agents_by_category = defaultdict(list)

    # Find all .md files in .claude/agents/categories
    for md_file in agents_dir.rglob('*.md'):
        # Skip README and TAXONOMY files
        if md_file.name in ['README.md', 'TAXONOMY.md', '.md']:
            continue

        agent = parse_agent_file(md_file)
        if agent:
            agents_by_category[agent['category']].append(agent)

    # Sort agents within each category
    for category in agents_by_category:
        agents_by_category[category].sort(key=lambda a: a['name'])

    return agents_by_category


def generate_agent_index(agents_by_category: Dict[str, List[Dict]]) -> str:
    """Generate the main agents index page."""
    md = "# Agent Roster\n\n"
    md += "Complete glossary of 168+ AI specialist agents across 11 categories.\n\n"

    md += "!!! note \"About the Agent Roster\"\n"
    md += "    These agent definitions are generated from source files in `.claude/agents/categories/`.\n"
    md += "    This is \"documents as code\" — definitions and documentation stay in sync.\n\n"

    # Table of contents
    md += "## Categories\n\n"
    for category in sorted(agents_by_category.keys()):
        agent_count = len(agents_by_category[category])
        anchor = category.lower().replace(' ', '-')
        md += f"- [{category}](#{anchor}) ({agent_count} agents)\n"

    md += "\n---\n\n"

    # Detailed listing by category
    for category in sorted(agents_by_category.keys()):
        agents = agents_by_category[category]
        anchor = category.lower().replace(' ', '-')
        md += f"## {category}\n\n"

        for agent in agents:
            md += f"### {agent['name']}\n\n"
            md += f"**Description**: {agent['description']}\n\n"

            if agent['tools_list']:
                tools_str = ', '.join(agent['tools_list'])
                md += f"**Tools**: {tools_str}\n\n"

            if agent['model']:
                md += f"**Model**: {agent['model']}\n\n"

            md += f"[View Definition](../{agent['file_path']}) · [Invoke Now](#)\n\n"

    return md


def generate_agent_index_chart(agents_by_category: Dict[str, List[Dict]]) -> str:
    """Generate a mermaid chart showing agent categories and counts."""
    categories = sorted(agents_by_category.keys())

    mermaid = "```mermaid\npieLand\n"
    for category in categories:
        count = len(agents_by_category[category])
        safe_category = category.replace(' ', '_')
        mermaid += f'    "{category}": {count}\n'
    mermaid += "```\n\n"

    return mermaid


def main():
    """Main execution."""
    repo_root = Path(__file__).parent.parent
    agents_dir = repo_root / '.claude' / 'agents' / 'categories'
    docs_dir = repo_root / 'docs'
    agents_docs_dir = docs_dir / 'agents-glossary'

    # Create agents documentation directory
    agents_docs_dir.mkdir(exist_ok=True)

    # Get all agents
    agents_by_category = get_all_agents(agents_dir)

    if not agents_by_category:
        print("No agents found!")
        return

    # Generate index
    total_agents = sum(len(agents) for agents in agents_by_category.values())
    print(f"Found {total_agents} agents across {len(agents_by_category)} categories")

    # Create agents index page
    index_content = "# Agent Roster\n\n"
    index_content += f"Complete glossary of {total_agents} AI specialist agents organized by expertise.\n\n"

    index_content += "!!! note \"Documents as Code\"\n"
    index_content += "    These agent definitions are auto-generated from source files in `.claude/agents/categories/`.\n"
    index_content += "    The documentation stays in sync with actual agent definitions.\n\n"

    # Add category chart
    index_content += "## Distribution by Category\n\n"
    index_content += generate_agent_index_chart(agents_by_category)

    # Add detailed listing
    index_content += "## All Agents\n\n"
    for category in sorted(agents_by_category.keys()):
        agents = agents_by_category[category]
        md_anchor = category.lower().replace(' ', '-')
        index_content += f"\n### {category}\n\n"

        for agent in agents:
            index_content += f"- **{agent['name']}** — {agent['description']}\n"

    # Write index file
    index_file = agents_docs_dir / 'index.md'
    with open(index_file, 'w') as f:
        f.write(index_content)

    print(f"Generated {index_file}")
    print("✓ Agent documentation generated successfully")


if __name__ == '__main__':
    main()
