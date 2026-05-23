#!/usr/bin/env bash
# AgentArmy SessionStart hook
# Fires when a Claude Code session begins.
# Purpose: load board state, version-check, print routing context.
# Constraint: must exit 0 always and complete within 3s.

set -euo pipefail

echo "AgentArmy SessionStart: loading board state..."

# Sanity-check: verify CLAUDE.md is present (repo is properly set up)
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [[ -z "$REPO_ROOT" ]]; then
  echo "SessionStart: not inside a git repo — skipping board state load"
  exit 0
fi

if [[ ! -f "$REPO_ROOT/CLAUDE.md" ]]; then
  echo "SessionStart: CLAUDE.md not found — repo may not be fully set up (see docs/setup.md)"
fi

BRANCH="$(git branch --show-current 2>/dev/null || echo "unknown")"

# Attempt board state query via gh CLI (graceful degradation if not available)
if command -v gh &>/dev/null; then
  RT1_COUNT="$(gh issue list --label rt-1 --state open --json number -q 'length' 2>/dev/null || echo "??")"
else
  RT1_COUNT="?? (gh CLI not available)"
fi

echo "RT1 open: ${RT1_COUNT} | Branch: ${BRANCH}"
echo "SessionStart: ready. See CLAUDE.md for routing table and agent roster."

exit 0
