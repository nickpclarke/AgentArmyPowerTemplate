# Claude Code Hook System

AgentArmy wires Claude Code's lifecycle hooks to provide routing hints, context injection, board-state awareness, and event logging across every session.

## Hook Overview

| Hook | Fires when | AgentArmy purpose | Timeout | Blocking? |
|---|---|---|---|---|
| **SessionStart** | Session begins | Print board state, branch, open RT1 item count | 10s | No — always exits 0 |
| **UserPromptSubmit** | Every user prompt | Emit routing hints for architecture/security/agent keywords | 5s | No — always exits 0 |
| **PreToolUse** | Before any tool call | Validate Write/Edit on GitHub files; warn on settings.json edits | 3s | No — always exits 0 |
| **PostToolUse** | After any tool call | Detect commits → remind to push; detect new docs → remind to update index | 5s | No — always exits 0 |
| **Stop** | Session ends | Persist memories to MemPalace | 60s | No |
| **PreCompact** | Before context compaction | Emergency save to MemPalace | 60s | No |

All hooks exit 0 by default. **No hook ever blocks Claude Code operations.**

## Hook Scripts

The four AgentArmy-specific hooks live in `tools/hooks/`:

| Script | Hook | What it does |
|---|---|---|
| `session-start.sh` | SessionStart | Verifies CLAUDE.md is present, queries open RT1 items via `gh`, prints branch/status line |
| `user-prompt-submit.sh` | UserPromptSubmit | Reads prompt from stdin, emits routing hints to stderr for relevant keywords |
| `pre-tool-use.sh` | PreToolUse | Validates issue naming format in Write/Edit operations; warns on direct settings.json edits |
| `post-tool-use.sh` | PostToolUse | Detects `git commit` in Bash calls → reminds to push; detects new docs → reminds to update index |

The Stop and PreCompact hooks use the MemPalace CLI (`mempalace hook run`) — see [docs/mempalace.md](mempalace.md).

## Configuration

Hooks are configured in `.claude/settings.json`. Each hook event contains an array of hook entries:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /home/user/AgentArmy/tools/hooks/session-start.sh",
            "timeout": 10,
            "statusMessage": "AgentArmy: loading board state..."
          }
        ]
      }
    ]
  }
}
```

## Customising Hooks

**Add a new hint to UserPromptSubmit:**

Edit `tools/hooks/user-prompt-submit.sh` and add a pattern:

```bash
if echo "$PROMPT_LOWER" | grep -qE '\bperformance\b|\blatency\b'; then
  echo "AgentArmy hint: Consider performance-engineer agent" >&2
fi
```

**Add a new hook event:**

1. Create `tools/hooks/<event-name>.sh` (must exit 0, keep under the timeout)
2. Add an entry to `.claude/settings.json` under the relevant hook key
3. Test by triggering the event and checking session output

**Disable a hook temporarily:**

Remove or comment out the hook entry in `.claude/settings.json`. The hook scripts themselves remain on disk.

## Path Configuration

The hook commands in `.claude/settings.json` use absolute paths (`/home/user/AgentArmy/tools/hooks/`). For local installs where the repo is checked out to a different path, update the commands accordingly — or use a relative path via a wrapper:

```bash
# In settings.json — works from any repo root:
"command": "bash \"$(git rev-parse --show-toplevel)/tools/hooks/session-start.sh\""
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Hook doesn't fire | Timeout too low for slow operations | Increase `timeout` in settings.json |
| Routing hints not appearing | `user-prompt-submit.sh` not executable | `chmod +x tools/hooks/*.sh` |
| SessionStart shows `gh CLI not available` | `gh` not on PATH in remote session | Install `gh` or accept graceful degradation |
| MemPalace hooks fail | `mempalace` not installed | `pip install mempalace && mempalace init` |
| Hook blocks tool use | Hook script exits non-zero | All AgentArmy hooks must exit 0 — check for `set -e` + failing commands |
