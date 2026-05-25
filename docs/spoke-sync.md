# Spoke helper sync

One-way sync of the Claude Code **microVM helper surface** from this hub to the
spoke repos. Spoke microVM agents run in isolated environments and can't reach the
hub, so without this they have no agent roster, slash commands, or session hooks —
they're "blind". This pushes repo-local copies into each spoke.

**Hub is the source of truth.** Edit the helpers in the hub; never hand-edit the
synced copies in a spoke (they get overwritten on the next sync).

## What syncs

Declared in [`scripts/spoke_sync.config.json`](../scripts/spoke_sync.config.json):

- `.claude/agents/`, `.claude/commands/`, `.claude/agent-schema.json`
- `.claude/settings.json` + the scripts its hooks call (`scripts/mempalace_hook.py`
  and the `.ps1` variant). MicroVMs won't have MemPalace installed — those hooks
  fail gracefully, so syncing the settings is safe.
- `scripts/board_commands.py`, `scripts/onboarding-check.ps1`, `tools/status.mjs`

Directories are **mirrored** (deletions in the hub propagate). A provenance stamp is
written to `.claude/.agentarmy-sync.json` in each spoke recording the hub commit.

**Never synced** (hard denylist, enforced even if added to the manifest):
`settings.local.json`, `*.local.json`, `.claude/worktrees/`, `.env`, credentials.

## Adding a spoke

Add the repo name to `spokes` in the config (e.g. `middle-core` once that repo
exists — today middle-core lives as `templates/middle-core/` inside the hub).

## Running it

**Locally** (uses your `gh` auth):

```bash
python scripts/sync_helpers_to_spokes.py --dry-run        # clone + diff, no push
python scripts/sync_helpers_to_spokes.py                  # open/update a PR per spoke
python scripts/sync_helpers_to_spokes.py --spoke backend-core
```

**In CI** — `.github/workflows/sync-helpers-to-spokes.yml`:

- `workflow_dispatch` (optional `spoke` / `dry_run` inputs), and
- automatically on push to `main` that touches any synced path.

It opens/updates a PR in each spoke — it never merges automatically.

**Auth:** the workflow uses `PROJECT_TOKEN` (classic PAT, already scoped for this
org's repos). The built-in `GITHUB_TOKEN` can't write to other repositories. If
`PROJECT_TOKEN` can't yet write to a spoke, grant the token access to that repo.
