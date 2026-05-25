# Spoke helper sync

One-way sync of the Claude Code **microVM helper surface** from this hub to the
spoke repos. Spoke microVM agents run in isolated environments and can't reach the
hub, so without this they have no agent roster, slash commands, or session hooks —
they're "blind". This pushes repo-local copies into each spoke.

**Hub is the source of truth.** Edit the helpers in the hub; never hand-edit the
synced copies in a spoke (they get overwritten on the next sync).

## What syncs

Declared in [`scripts/spoke_sync.config.json`](../scripts/spoke_sync.config.json):

- `AGENTS.md` — the shared, fleet-wide agent guidance (roster, routing, skills,
  chaining). Authoritative; the spoke's `CLAUDE.md` imports it via `@AGENTS.md`.
- `.claude/agents/`, `.claude/commands/`, `.claude/agent-schema.json`
- `.claude/settings.json` + the scripts its hooks call (`scripts/mempalace_hook.py`
  and the `.ps1` variant). MicroVMs won't have MemPalace installed — those hooks
  fail gracefully, so syncing the settings is safe.
- `scripts/board_commands.py`, `scripts/onboarding-check.ps1`, `tools/status.mjs`

Directories are **mirrored** (deletions in the hub propagate), and synced paths are
**force-added** so a spoke's `.gitignore` can never silently drop them. A provenance
stamp is written to `.claude/.agentarmy-sync.json` recording the hub commit.

**CLAUDE.md** is *seeded only if the spoke lacks one* (it imports `@AGENTS.md` and
leaves room for spoke-specific notes) and is on the **deny** list — the sync never
overwrites a spoke's own `CLAUDE.md`, since that is repo-specific.

**Never synced** (hard denylist, enforced even if added to the manifest):
`CLAUDE.md`, `settings.local.json`, `*.local.json`, `.claude/worktrees/`, `.env`, credentials.

## Adding a spoke

Add the repo name to `spokes` in the config (e.g. `middle-core` once that repo
exists — today middle-core lives as `templates/middle-core/` inside the hub).

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
