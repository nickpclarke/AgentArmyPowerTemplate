# MemPalace Setup

MemPalace gives local AI assistants persistent, cross-session memory. Instead of starting every conversation cold, Claude Code and Codex can recall context from previous sessions: what you've worked on, decisions made, patterns discovered.

This repo ships with `mempalace.yaml` already configured, `.claude/settings.json` wired for Claude Code, and `.codex/hooks.json` wired for Codex. You just need to install MemPalace itself.

## How It Works

MemPalace intercepts three lifecycle events in both local assistants:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | When a new session begins | Loads relevant context from the palace |
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

MemPalace 3.x takes the **project directory as an argument** and stores the palace under
`~/.mempalace/palace` (override with `--palace` or `~/.mempalace/config.json`). Two steps:

```bash
# 1. Detect rooms from the folder structure (non-interactive, heuristics-only).
#    Drop --no-llm if you run a local Ollama and want LLM-assisted entity refinement.
mempalace init . --yes --no-llm

# 2. Mine code/docs into the palace. --wing must match `wing:` in mempalace.yaml.
mempalace mine . --wing agentarmy
```

Verify content was filed:

```bash
mempalace status
```

> `init` writes a machine-specific `entities.json` (gitignored) and will try to add
> `mempalace.yaml` to `.gitignore` too — but in this repo `mempalace.yaml` is a **curated,
> committed template artifact**, so it is intentionally kept out of `.gitignore`. If you
> re-run `init`, restore the curated `mempalace.yaml` (`git checkout -- mempalace.yaml`).

## Verify Hooks Are Wired

MemPalace only supports three lifecycle hooks: **`session-start`**, **`stop`**, and
**`precompact`**. The Claude Code hooks are already in `.claude/settings.json`, all routed
through `scripts/mempalace_hook.py` with an absolute `$CLAUDE_PROJECT_DIR` path:

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python \"$CLAUDE_PROJECT_DIR/scripts/mempalace_hook.py\" --hook session-start --harness claude-code",
        "timeout": 30
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python \"$CLAUDE_PROJECT_DIR/scripts/mempalace_hook.py\" --hook stop --harness claude-code",
        "timeout": 60
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "python \"$CLAUDE_PROJECT_DIR/scripts/mempalace_hook.py\" --hook precompact --harness claude-code",
        "timeout": 60
      }]
    }]
  }
}
```

> **Why the wrapper, and why an absolute path?** `scripts/mempalace_hook.py` returns success
> (exit 0) when `mempalace` is missing *and* for any hook MemPalace doesn't support, so a
> missing CLI or a stray hook name can never block a tool call. Do **not** wire
> `pre-tool-use`, `post-tool-use`, or `user-prompt-submit` to `mempalace hook run` directly —
> MemPalace rejects them with a non-zero exit, and on `PreToolUse` that exit code blocks every
> tool call (a hard session deadlock). The absolute `$CLAUDE_PROJECT_DIR` path avoids a second
> trap: a relative `scripts/...` path breaks if the working directory ever changes.

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
