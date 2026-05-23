# Using Codex

Codex can work in this template as a local implementation, review, and documentation partner alongside Claude Code and GitHub Copilot. Treat Codex as another way to operate the AgentArmy repository, not as a fourth product surface.

## What Codex Should Work On

AgentArmy is a starter template, not an application. Codex work should stay in the template layer:

| Area | Codex should edit |
|---|---|
| GitHub automation | `.github/workflows/` |
| Agent guidance | `AGENTS.md`, `CLAUDE.md`, `.claude/agents/categories/` |
| Codex configuration | `.codex/` |
| Documentation | `docs/`, `README.md` |
| Helper tooling | `scripts/`, `.claude/tools/`, `extensions/` |

There is no `index.html` or app runtime to implement against.

## Source of Truth for Codex

Codex should read files in this order:

1. `AGENTS.md` for repository-specific operating rules.
2. Active issue, project board item, or ExecPlan when one exists.
3. `CLAUDE.md` for shared AgentArmy routing concepts that also apply to local AI assistants.
4. The relevant docs under `docs/`.
5. Existing file conventions.

If instructions conflict, prefer `AGENTS.md` and the active task artifact over Claude-specific convenience commands.

## Agent Synchronization

Claude agents (`.claude/agents/categories/`) are **automatically synchronized** to Codex at session start via the `SessionStart` hook. Codex reads the converted agents from `.codex/agents/*.toml`.

For full details on agent sync across platforms (Codex, Antigravity CLI, MCP servers), see **[Agent Synchronization](agent-sync.md)**.

**Quick audit:**
```bash
python scripts/orchestrate_agent_sync.py --audit
```

## Reusing Claude Code Helpers

Most Claude Code assets are useful to Codex as reference material:

| Claude Code asset | How Codex should use it |
|---|---|
| `.claude/agents/categories/` | Source of truth for all agent definitions (auto-synced to `.codex/agents/`) |
| `.claude/commands/` | Prompt templates and workflow patterns to translate into Codex steps |
| `.claude/tools/` | Helper docs and scripts to inspect or adapt when useful |
| `CLAUDE.md` | Shared routing, SAFE, and board operating model |

Claude Code slash commands such as `/review-pr`, `/wardley`, and `/commit-push-pr` are not Codex commands. In Codex, perform the same workflow directly with repo files, GitHub CLI, and Codex tools.

## Subagent Guidance

The `.claude/agents/categories/` files are Claude Code agent definitions. Codex should treat them as named lenses unless a Codex-native subagent tool is available and the user explicitly asks for delegated or parallel agent work.

When using Codex subagents, keep the same discipline as the AgentArmy template:

- one owner per edited file or artifact
- reviewers are read-only unless assigned edits
- narrow handoff packets
- synthesis back into one coherent plan or change

## Hooks and Memory

This repo includes `.codex/hooks.json` so Codex can run the same MemPalace lifecycle saves as Claude Code:

| Hook | Purpose |
|---|---|
| `Stop` | Save a context snapshot after a response |
| `PreCompact` | Save key facts before context compaction |

The hook commands currently call the cross-platform Python helper:

```bash
python scripts/mempalace_hook.py --hook stop
python scripts/mempalace_hook.py --hook precompact
```

The helper sets `PYTHONUTF8=1`, skips cleanly when `mempalace` is not installed, and uses the `claude-code` harness name for compatibility with the current MemPalace configuration. If MemPalace adds a Codex-specific harness in your environment, update `.codex/hooks.json` and this document intentionally.

Do not commit personal API keys or provider choices in `.codex/config.toml`. Keep local secrets in your environment, user-level Codex config, or an untracked `.codex/config.local.toml`.

## Practical Codex Workflow

1. Prefer the Codex desktop **New worktree** flow for task work when Claude Code or another agent may also be active.
2. Start with `AGENTS.md`, then inspect the relevant docs and file structure.
3. Classify the work: docs, workflow, agent definition, setup, review, or helper tooling.
4. For non-trivial scope, create or update an ExecPlan under `.agent/plans/`.
5. Make the smallest template-level change.
6. Run docs or script validation when available.
7. Summarize changed files, validation, and residual risks.

When Codex is running in a worktree, keep changes on that worktree's branch and merge them back through the main repository checkout or a PR. If Codex needs the latest Claude Code work, that work must be committed and available through `main` or another branch first.

For GitHub-board-backed work, use the same board conventions as Claude Code: create issues for non-trivial changes, apply `copilot-task` or `agent-army-task`, and include `Closes #N` in PR bodies.
