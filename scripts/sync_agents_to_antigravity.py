#!/usr/bin/env python3
"""
Sync Claude agent definitions (.claude/agents/categories/)
to Antigravity CLI plugins (~/.gemini/antigravity-cli/plugins/)
as native agent plugins.
"""

import os
import json
import shutil
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent
    categories_dir = repo_root / '.claude' / 'agents' / 'categories'
    
    home = Path.home()
    antigravity_plugins_dir = home / '.gemini' / 'antigravity-cli' / 'plugins'

    if not categories_dir.exists():
        print(f"Error: Categories directory not found at {categories_dir}")
        return

    # Find all categories with a .claude-plugin/plugin.json
    count_plugins = 0
    count_agents = 0

    for category_path in categories_dir.iterdir():
        if not category_path.is_dir():
            continue

        plugin_json_path = category_path / '.claude-plugin' / 'plugin.json'
        if not plugin_json_path.exists():
            continue

        try:
            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                plugin_meta = json.load(f)
        except Exception as e:
            print(f"Error reading plugin.json in {category_path.name}: {e}")
            continue

        plugin_name = plugin_meta.get('name')
        if not plugin_name:
            print(f"Warning: No plugin name defined in {plugin_json_path}")
            continue

        # Target directory for this plugin in Antigravity CLI
        target_dir = antigravity_plugins_dir / plugin_name

        # Clean existing plugin directory to avoid stale files
        if target_dir.exists():
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                print(f"Warning: Could not clean existing plugin directory {target_dir}: {e}")

        # Create target directory
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {target_dir}: {e}")
            continue

        # Copy plugin.json to target root
        try:
            shutil.copy2(plugin_json_path, target_dir / 'plugin.json')
        except Exception as e:
            print(f"Error copying plugin.json to {target_dir}: {e}")
            continue

        # Copy all agent files specified in the plugin
        agents_copied = 0
        agents_list = plugin_meta.get('agents', [])
        for agent_rel_path in agents_list:
            # Source path (original file is in the category folder, e.g. ./agent.md)
            src_agent_file = (category_path / agent_rel_path).resolve()
            if not src_agent_file.exists():
                print(f"Warning: Agent file {src_agent_file} listed in plugin {plugin_name} does not exist.")
                continue

            # Target path
            dest_agent_file = target_dir / src_agent_file.name
            try:
                shutil.copy2(src_agent_file, dest_agent_file)
                agents_copied += 1
            except Exception as e:
                print(f"Error copying agent {src_agent_file.name} to {target_dir}: {e}")

        print(f"Synced plugin '{plugin_name}' with {agents_copied} agents.")
        count_plugins += 1
        count_agents += agents_copied

    print(f"\nSuccessfully synced {count_plugins} plugins and {count_agents} total agents to Antigravity CLI!")

if __name__ == '__main__':
    main()
