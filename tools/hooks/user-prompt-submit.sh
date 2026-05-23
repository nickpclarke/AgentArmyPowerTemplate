#!/usr/bin/env bash
# AgentArmy UserPromptSubmit hook
# Fires on every prompt the user submits.
# Purpose: detect routing-relevant keywords and emit a routing hint to stderr.
# Constraint: must exit 0 always, never block prompt, complete within 1s.

# Read the user prompt from stdin
PROMPT="$(cat)"

# Convert to lowercase for case-insensitive keyword matching
PROMPT_LOWER="$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')"

# Emit routing hints to stderr (shown as status messages, not injected into the response)
if echo "$PROMPT_LOWER" | grep -qE '\barchitecture\b|\badr\b'; then
  echo "AgentArmy hint: Consider architect-reviewer agent or /ea-adr skill" >&2
fi

if echo "$PROMPT_LOWER" | grep -qE '\bsecurity\b'; then
  echo "AgentArmy hint: Consider security-auditor agent or /security-review skill" >&2
fi

if echo "$PROMPT_LOWER" | grep -qE '\brouting\b'; then
  echo "AgentArmy hint: Consider routing-policy.yaml for deterministic routing" >&2
fi

if echo "$PROMPT_LOWER" | grep -qE '\bagent\b|\bdelegate\b'; then
  echo "AgentArmy hint: Check CLAUDE.md routing table for the right specialist" >&2
fi

exit 0
