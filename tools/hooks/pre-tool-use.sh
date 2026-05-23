#!/usr/bin/env bash
# AgentArmy PreToolUse hook
# Fires before Claude Code executes any tool call.
# Purpose: validate Write/Edit operations (issue naming, GitHub workflow files).
# Constraint: must exit 0 always (never block tool use), complete within 3s.

TOOL_NAME="${TOOL_NAME:-}"
TOOL_INPUT="${TOOL_INPUT:-}"

if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]]; then
  # Check if the file path references a GitHub workflow or issues directory
  if echo "$TOOL_INPUT" | grep -qE '\.github/workflows/|issues/'; then
    # Validate that issue references use the expected RT-X-FEAT-Y format if present
    if echo "$TOOL_INPUT" | grep -qE 'RT[0-9]+-FEAT-[0-9]+|rt[0-9]+-feat-[0-9]+'; then
      echo "PreToolUse: $TOOL_NAME — RT issue reference format looks valid"
    fi
  fi

  # Warn (to stderr, non-blocking) if editing .claude/settings.json directly
  if echo "$TOOL_INPUT" | grep -qE '\.claude/settings\.json'; then
    echo "PreToolUse: editing .claude/settings.json — ensure hooks are preserved" >&2
  fi
fi

echo "PreToolUse: ${TOOL_NAME:-unknown} validated"

exit 0
