# Spoke dressing sync (multi-coder)

> Part of the spoke lifecycle — see **[spoke-lifecycle.md](spoke-lifecycle.md)** for the
> end-to-end map (scaffold → register → **dress** → watch). This page is stage 3 in detail.

One-way sync of the **multi-coder agent helper surface** from this hub to the spoke
repos. This is the **"dressing" routine**: it turns a bare spoke into a fully-dressed
AgentArmy template for *every* supported agentic coder — **Claude Code**, **OpenAI
Codex**, and **Gemini Antigravity** — so whichever coder opens the repo finds its
native agent roster, config, and the shared behavioral law already present. Spoke
microVM agents run in isolated environments and can't reach the hub, so without this
they're "blind". This pushes repo-local copies into each spoke.

**Hub is the source of truth.** Edit the helpers in the hub; never hand-edit the
synced copies in a spoke (they get overwritten on the next sync).

## What syncs

Declared in [`scripts/spoke_sync.config.json`](../scripts/spoke_sync.config.json),
grouped by coder:

**Shared (all coders)**
- `AGENTS.md` — the shared, fleet-wide agent guidance (roster, routing, skills,
  chaining). Authoritative; the spoke's `CLAUDE.md` imports it via `@AGENTS.md`. This
  is also **OpenAI Codex's primary instruction file**.
- `CONSTITUTION.md` — the supreme behavioral law; a seeded `CLAUDE.md` imports it via
  `@CONSTITUTION.md`.

**Claude Code**
- `.claude/agents/`, `.claude/commands/`, `.claude/agent-schema.json`
- `.claude/settings.json` + the scripts its hooks call (`scripts/mempalace_hook.py`
  and the `.ps1` variant). MicroVMs won't have MemPalace installed — those hooks
  fail gracefully, so syncing the settings is safe.

**OpenAI Codex**
- `.codex/agents/` (TOML agent profiles), `.codex/config.toml` (shell + MCP policy,
  env-var indirected — no secrets), `.codex/hooks.json` (session lifecycle).
- `scripts/sync_agents_to_codex.py` rides along so `.codex/hooks.json` is
  self-consistent and the spoke can regenerate its Codex pack from
  `.claude/agents/categories/`.

**Gemini Antigravity**
- `.agents/plugins/` (per-category agent plugins) + `scripts/sync_agents_to_antigravity.py`.

**PR-event automation (hub-authoritative)**
- `.github/workflows/claude.yml` (@claude responder), `copilot-review.yml`
  (auto-request Copilot review), `review-loop.yml` (autonomous review-fix loop). These
  are **portable** (`${{ github.repository }}` / `${{ github.repository_owner }}`), so the hub
  version runs verbatim in any spoke — every spoke gets the same review automation.
- Dressing also **seeds the `review-loop` bootstrap labels** (`review-loop`,
  `review-loop:done`, `review-loop:escalated`) in each spoke. The synced `review-loop.yml`
  only self-creates these from inside its own label-gated job, so a fresh spoke couldn't
  otherwise opt in (you can't add a label that doesn't exist). `sync_helpers_to_spokes.py`
  creates them up front (`ensure_review_loop_labels`).
- ⚠️ **Files synced ≠ functioning.** Each spoke still needs its own secrets set for
  these to run: `CLAUDE_CODE_OAUTH_TOKEN`, `PROJECT_TOKEN`, and (optional, for fleet MCP)
  `LOCAL_FLEET_MCP_URL` / `CF_ACCESS_CLIENT_ID` / `CF_ACCESS_CLIENT_SECRET`. The fleet
  heartbeat checks file *presence* (`pr-subscription-missing`), not secrets.

**Other helpers**
- `scripts/board_commands.py`, `scripts/onboarding-check.ps1`, `tools/status.mjs`,
  `tools/fleet-heartbeat.mjs`, `.mcp.json`, `.agent/*`, `notify-hub*.yml` (PR artifacts → hub).

Directories are **mirrored** (deletions in the hub propagate), and synced paths are
**force-added** so a spoke's `.gitignore` can never silently drop them. A provenance
stamp is written to `.claude/.agentarmy-sync.json` recording the hub commit.

**CLAUDE.md** is *seeded only if the spoke lacks one* (it imports `@AGENTS.md` and
leaves room for spoke-specific notes) and is on the **deny** list — the sync never
overwrites a spoke's own `CLAUDE.md`, since that is repo-specific.

**Never synced** (hard denylist, enforced even if added to the manifest):
`CLAUDE.md`, `settings.local.json`, `*.local.json`, `.claude/worktrees/`, `.env`, credentials.

## Adding a spoke

Add the repo name to `spokes` in [`scripts/spoke_sync.config.json`](../scripts/spoke_sync.config.json),
then run the sync. That's it — the next run clones the spoke, mirrors every pack, and
opens a dressing PR. The current spokes are `frontend-core`, `backend-core`,
`middle-core`, and `agentarmy-forge`.

## Adding a coder (dressing for a new agentic coder)

The routine is **config-driven and easy to extend** — no code changes needed for a
new coder:

1. Generate the coder's agent pack in the hub (e.g. a `sync_agents_to_<coder>.py`
   that renders `.claude/agents/categories/` into the coder's format), and run it so
   the pack dir exists.
2. Add the pack dir(s) — and any regenerator script the coder's hooks call — to
   `paths` in the config, under a new "coder" group (see the `$pack_note`).
3. Run the sync. Every spoke now ships that coder's dressing too.

`validate_paths()` refuses to run if any listed path is missing from the hub, so a
typo fails fast instead of half-dressing a spoke.

## Running it

**Locally** (uses your `gh` auth):

```bash
python scripts/sync_helpers_to_spokes.py --dry-run        # clone + diff, no push
python scripts/sync_helpers_to_spokes.py                  # PR per spoke + auto-merge into main
python scripts/sync_helpers_to_spokes.py --no-merge       # open the PR, leave it for review
python scripts/sync_helpers_to_spokes.py --spoke backend-core
```

By default the sync **auto-merges** (squash) the PR into each spoke's default branch —
an unmerged PR means the helpers never reach the spoke, which is the whole point. Use
`--no-merge` (or set `"auto_merge": false` in the config) to leave PRs open for review.

**In CI** — `.github/workflows/sync-helpers-to-spokes.yml`:

- `workflow_dispatch` (optional `spoke` / `dry_run` inputs), and
- automatically on push to `main` that touches any synced path.

**Auth:** the workflow uses `PROJECT_TOKEN` (classic PAT, already scoped for this
org's repos). The built-in `GITHUB_TOKEN` can't write to other repositories. If
`PROJECT_TOKEN` can't yet write to a spoke, grant the token access to that repo.
