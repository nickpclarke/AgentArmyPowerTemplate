# MemPalace Setup

MemPalace gives local AI assistants persistent, cross-session memory. Instead of starting every conversation cold, Claude Code and Codex can recall context from previous sessions: what you've worked on, decisions made, patterns discovered.

This repo ships with `mempalace.yaml` already configured, `.claude/settings.json` wired for Claude Code, and `.codex/hooks.json` wired for Codex. You just need to install MemPalace itself.

## How It Works

MemPalace intercepts two lifecycle events in both local assistants:

| Hook | When it fires | What it does |
|---|---|---|
| `Stop` | After every response | Saves context snapshot to the palace |
| `PreCompact` | Before context window compression | Writes a diary entry preserving key facts |

Context is organized into "rooms" defined in `mempalace.yaml`. When Claude Code or Codex starts a new session, it can search its palace for relevant context from past work.

## Install

```bash
pip install mempalace
```

Verify:

```bash
mempalace --version
```

## Initialize the Palace

Run once in the repo directory:

```bash
mempalace init
```

This creates the local palace storage directory (`.mempalace/` by default, outside the repo).

## Verify Hooks Are Wired

The Claude Code hooks are already in `.claude/settings.json` and run through the cross-platform `scripts/mempalace_hook.py` helper:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python scripts/mempalace_hook.py --hook stop --harness claude-code",
        "timeout": 60
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "python scripts/mempalace_hook.py --hook precompact --harness claude-code",
        "timeout": 60
      }]
    }]
  }
}
```

Codex uses the same lifecycle hooks from `.codex/hooks.json`, routed through the cross-platform `scripts/mempalace_hook.py` helper:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python scripts/mempalace_hook.py --hook stop",
        "timeout": 60
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "python scripts/mempalace_hook.py --hook precompact",
        "timeout": 60
      }]
    }]
  }
}
```

The helper sets `PYTHONUTF8=1`, skips cleanly when `mempalace` is not installed, and no-ops Claude Code lifecycle events that the installed MemPalace CLI does not accept, such as `UserPromptSubmit`, `PreToolUse`, and `PostToolUse`. It currently uses the `claude-code` harness name for compatibility with MemPalace. If your installed MemPalace version exposes a Codex-specific harness, update `.codex/hooks.json` deliberately and keep this document in sync.

If you see hook errors in Claude Code, confirm `mempalace` is on your PATH:

```bash
which mempalace   # macOS/Linux
where mempalace   # Windows
```

## Configure the MCP Server (optional)

MemPalace also ships an MCP server that exposes palace tools directly inside Claude Code. To enable it, add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "mempalace": {
      "command": "mempalace",
      "args": ["mcp"]
    }
  }
}
```

Then restart Claude Code. You'll see `mempalace_*` tools become available. For Codex, use the Codex MCP configuration mechanism available in your install and point it at the same `mempalace mcp` command.

### MCP tools exposed

| Tool | What it does |
|---|---|
| `mempalace_search` | Search palace by keyword |
| `mempalace_get_drawer` | Read a specific memory drawer |
| `mempalace_list_rooms` | List all configured rooms |
| `mempalace_diary_read` | Read diary entries |
| `mempalace_kg_query` | Query the knowledge graph |

## Palace Structure (this repo)

`mempalace.yaml` defines four rooms:

| Room | What goes here |
|---|---|
| `agents` | Agent definitions, selection patterns, category knowledge |
| `github` | Board state, workflow decisions, SAFE planning context |
| `docs` | Setup notes, architecture decisions, config references |
| `general` | Everything else |

When Claude searches its palace, it matches your query against room keywords to find relevant context fast.

## Customize for Your Project

Edit `mempalace.yaml` to reflect your project's domain:

```yaml
wing: your-project-name
rooms:
- name: auth
  description: Authentication and authorization context
  keywords: [auth, login, jwt, oauth, permissions]
- name: api
  description: API design decisions and endpoint notes
  keywords: [api, endpoint, rest, graphql, schema]
- name: general
  description: Files that don't fit other rooms
  keywords: []
```

The `wing` field namespaces your palace so multiple projects don't collide.

## Troubleshooting

**Hook fires but nothing is saved:**
Run `mempalace status` to confirm the palace is initialized and the storage path is writable.

**`mempalace: command not found` in hooks:**
The hook runs in a non-interactive shell that may not have your PATH. Fix by using the full path:

```bash
# Find the path
which mempalace

# Update settings.json to use full path, e.g.:
# "command": "/home/user/.local/bin/mempalace hook run --hook stop --harness claude-code"
```

**OpenCode also uses MemPalace:**
`.opencode/opencode.json` has `{"plugin": ["mempalace"]}` — if you use OpenCode, the same palace is shared.
