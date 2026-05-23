#!/usr/bin/env bash
# AgentArmy PostToolUse hook
# Fires after Claude Code completes any tool call.
# Purpose: emit board-sync events, detect new docs, log provenance.
# Constraint: must exit 0 always, complete within 5s.

TOOL_NAME="${TOOL_NAME:-}"
TOOL_INPUT="${TOOL_INPUT:-}"

if [[ "$TOOL_NAME" == "Bash" ]]; then
  # Detect git commit operations — remind to push so CI is triggered
  if echo "$TOOL_INPUT" | grep -qE 'git commit'; then
    echo "PostToolUse: commit detected — consider pushing to trigger CI"
  fi
fi

if [[ "$TOOL_NAME" == "Write" ]]; then
  # Detect new docs being created under docs/
  if echo "$TOOL_INPUT" | grep -qE '"path"\s*:\s*"[^"]*docs/[^"]*\.md"' || \
     echo "$TOOL_INPUT" | grep -qE "docs/[^ ']*.md"; then
    echo "PostToolUse: new doc created — consider updating docs/index.md"
  fi
fi

echo "PostToolUse: ${TOOL_NAME:-unknown} logged"

exit 0
