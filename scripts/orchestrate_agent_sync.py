#!/usr/bin/env python3
"""
Unified agent sync orchestrator for AgentArmy.

Coordinates synchronization of Claude Code agent definitions across:
- Codex (GitHub's custom agent platform)
- Antigravity CLI (Gemini's native CLI)
- Generates audit reports and sync status

Usage:
    python scripts/orchestrate_agent_sync.py              # Full sync
    python scripts/orchestrate_agent_sync.py --audit      # Audit only (no changes)
    python scripts/orchestrate_agent_sync.py --codex      # Codex sync only
    python scripts/orchestrate_agent_sync.py --antigravity # Antigravity sync only
    python scripts/orchestrate_agent_sync.py --global     # Sync Antigravity globally
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

class AgentSyncOrchestrator:
    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.codex_agents_dir = self.repo_root / '.codex' / 'agents'
        self.antigravity_plugins_dir = self.repo_root / '.agents' / 'plugins'
        self.claude_agents_dir = self.repo_root / '.claude' / 'agents' / 'categories'

    def count_agents(self, directory: Path) -> int:
        """Count agent files in a directory."""
        if not directory.exists():
            return 0
        if directory.name == 'agents':
            return len(list(directory.glob('*.toml')))
        elif directory.name == 'categories':
            return len(list(directory.rglob('*.md'))) - len(list(directory.rglob('README.md'))) - len(list(directory.rglob('TAXONOMY.md')))
        elif directory.name == 'plugins':
            return sum(len(list(p.glob('*.md'))) for p in directory.iterdir() if p.is_dir())
        return 0

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Execute a shell command and capture output."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
            return success, output
        except subprocess.TimeoutExpired:
            return False, f"Timeout executing: {description}"
        except Exception as e:
            return False, f"Error executing {description}: {e}"

    def sync_codex(self) -> Tuple[bool, Dict]:
        """Synchronize agents to Codex."""
        print("🔄 Syncing Claude agents → Codex...")
        success, output = self.run_command(
            [sys.executable, 'scripts/sync_agents_to_codex.py'],
            'Codex sync'
        )

        codex_count = self.count_agents(self.codex_agents_dir)

        result = {
            'platform': 'Codex',
            'success': success,
            'agent_count': codex_count,
            'output': output.strip()
        }

        if success:
            print(f"   ✅ Synced {codex_count} agents to .codex/agents/")
        else:
            print(f"   ❌ Failed: {output[:100]}")

        return success, result

    def sync_antigravity(self, use_global: bool = False) -> Tuple[bool, Dict]:
        """Synchronize agents to Antigravity CLI."""
        location = "global (~/.gemini/antigravity-cli/plugins)" if use_global else "workspace (.agents/plugins)"
        print(f"🔄 Syncing Claude agents → Antigravity CLI ({location})...")

        cmd = [sys.executable, 'scripts/sync_agents_to_antigravity.py']
        if use_global:
            cmd.append('--global')

        success, output = self.run_command(cmd, f'Antigravity sync ({location})')

        plugin_count = len(list(self.antigravity_plugins_dir.iterdir())) if self.antigravity_plugins_dir.exists() else 0
        agent_count = self.count_agents(self.antigravity_plugins_dir)

        result = {
            'platform': f'Antigravity ({location})',
            'success': success,
            'plugin_count': plugin_count,
            'agent_count': agent_count,
            'output': output.strip()
        }

        if success:
            print(f"   ✅ Synced {plugin_count} plugins with {agent_count} total agents")
        else:
            print(f"   ❌ Failed: {output[:100]}")

        return success, result

    def generate_audit(self) -> Dict:
        """Generate comprehensive audit report."""
        print("\n📊 AUDIT REPORT")
        print("=" * 60)

        # Count sources
        claude_count = self.count_agents(self.claude_agents_dir)
        codex_count = self.count_agents(self.codex_agents_dir) if self.codex_agents_dir.exists() else 0
        antigravity_count = self.count_agents(self.antigravity_plugins_dir) if self.antigravity_plugins_dir.exists() else 0
        plugin_groups = len(list(self.antigravity_plugins_dir.iterdir())) if self.antigravity_plugins_dir.exists() else 0

        # Check hooks
        hooks_file = self.repo_root / '.codex' / 'hooks.json'
        hooks_configured = hooks_file.exists()

        # Check MCP config
        mcp_file = self.repo_root / '.codex' / 'config.toml'
        mcp_count = 0
        if mcp_file.exists():
            with open(mcp_file) as f:
                mcp_count = f.read().count('[mcp_servers.')

        # Check sync scripts
        scripts_exist = {
            'sync_agents_to_codex.py': (self.repo_root / 'scripts' / 'sync_agents_to_codex.py').exists(),
            'sync_agents_to_antigravity.py': (self.repo_root / 'scripts' / 'sync_agents_to_antigravity.py').exists(),
        }

        # Build report
        audit = {
            'source_of_truth': {
                'location': '.claude/agents/categories/',
                'count': claude_count,
                'status': '✅ OK' if claude_count > 100 else '⚠️ Low count'
            },
            'codex_sync': {
                'location': '.codex/agents/',
                'count': codex_count,
                'status': '✅ OK' if codex_count >= claude_count * 0.9 else '❌ Out of sync'
            },
            'antigravity_sync': {
                'location': '.agents/plugins/',
                'plugins': plugin_groups,
                'agents': antigravity_count,
                'status': '✅ OK' if antigravity_count >= claude_count * 0.8 else '⚠️ Partial'
            },
            'mcp_servers': {
                'location': '.codex/config.toml',
                'count': mcp_count,
                'status': '✅ Configured' if mcp_count >= 3 else '⚠️ Minimal'
            },
            'hooks': {
                'location': '.codex/hooks.json',
                'session_start_hook': hooks_configured,
                'status': '✅ Active' if hooks_configured else '❌ Missing'
            },
            'scripts': {
                'sync_agents_to_codex.py': scripts_exist['sync_agents_to_codex.py'],
                'sync_agents_to_antigravity.py': scripts_exist['sync_agents_to_antigravity.py'],
                'status': '✅ All present' if all(scripts_exist.values()) else '❌ Missing scripts'
            }
        }

        # Print formatted report
        print(f"\n📌 SOURCE OF TRUTH")
        print(f"   Location: {audit['source_of_truth']['location']}")
        print(f"   Agents: {audit['source_of_truth']['count']}")
        print(f"   Status: {audit['source_of_truth']['status']}")

        print(f"\n📌 CODEX SYNC")
        print(f"   Location: {audit['codex_sync']['location']}")
        print(f"   Agents: {audit['codex_sync']['count']}")
        print(f"   Status: {audit['codex_sync']['status']}")
        print(f"   Sync ratio: {codex_count/claude_count*100 if claude_count > 0 else 0:.1f}%")

        print(f"\n📌 ANTIGRAVITY SYNC")
        print(f"   Location: {audit['antigravity_sync']['location']}")
        print(f"   Plugins: {audit['antigravity_sync']['plugins']}")
        print(f"   Agents: {audit['antigravity_sync']['agents']}")
        print(f"   Status: {audit['antigravity_sync']['status']}")
        print(f"   Sync ratio: {antigravity_count/claude_count*100 if claude_count > 0 else 0:.1f}%")

        print(f"\n📌 MCP SERVERS")
        print(f"   Location: {audit['mcp_servers']['location']}")
        print(f"   Configured: {audit['mcp_servers']['count']}")
        print(f"   Status: {audit['mcp_servers']['status']}")

        print(f"\n📌 CODEX HOOKS")
        print(f"   Location: {audit['hooks']['location']}")
        print(f"   SessionStart hook: {'✅ Yes' if audit['hooks']['session_start_hook'] else '❌ No'}")
        print(f"   Status: {audit['hooks']['status']}")

        print(f"\n📌 SYNC SCRIPTS")
        for script, exists in scripts_exist.items():
            print(f"   {script}: {'✅' if exists else '❌'}")
        print(f"   Status: {audit['scripts']['status']}")

        print("\n" + "=" * 60)

        return audit

    def full_sync(self, use_global: bool = False) -> bool:
        """Run full synchronization pipeline."""
        print("🚀 STARTING FULL AGENT SYNC")
        print("=" * 60)

        # Run syncs
        success_codex, _ = self.sync_codex()

        success_antigravity, _ = self.sync_antigravity(use_global=use_global)

        # Generate audit
        audit = self.generate_audit()

        # Summary
        print("\n" + "=" * 60)
        if success_codex and success_antigravity:
            print("✅ ALL SYNCS SUCCESSFUL")
            return True
        else:
            print("❌ SOME SYNCS FAILED - See details above")
            return False

    def audit_only(self) -> bool:
        """Run audit without making changes."""
        print("🔍 AUDIT MODE (Read-only)")
        print("=" * 60)
        self.generate_audit()
        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Orchestrate agent synchronization across platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python scripts/orchestrate_agent_sync.py              # Full sync
  python scripts/orchestrate_agent_sync.py --audit      # Audit only
  python scripts/orchestrate_agent_sync.py --codex      # Codex only
  python scripts/orchestrate_agent_sync.py --antigravity # Antigravity only
  python scripts/orchestrate_agent_sync.py --global     # Antigravity global sync
        '''
    )

    parser.add_argument('--audit', action='store_true', help='Audit mode (read-only)')
    parser.add_argument('--codex', action='store_true', help='Sync Codex only')
    parser.add_argument('--antigravity', action='store_true', help='Sync Antigravity only')
    parser.add_argument('--global', dest='use_global', action='store_true', help='Sync Antigravity globally')

    args = parser.parse_args()

    orchestrator = AgentSyncOrchestrator()

    # Determine what to run
    if args.audit:
        # Audit only
        return orchestrator.audit_only()
    elif args.codex:
        # Codex only
        success, _ = orchestrator.sync_codex()
        orchestrator.generate_audit()
        return success
    elif args.antigravity:
        # Antigravity only
        success, _ = orchestrator.sync_antigravity(use_global=args.use_global)
        orchestrator.generate_audit()
        return success
    else:
        # Full sync (default)
        return orchestrator.full_sync(use_global=args.use_global)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
