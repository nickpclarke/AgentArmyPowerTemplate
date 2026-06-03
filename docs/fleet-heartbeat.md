# Fleet Heartbeat & Scheduled Audit

One script — `tools/fleet-heartbeat.mjs` — is the fleet's **"heart"**: each beat it inventories
contracts, detects drift, checks repo health across the hub + spokes, and (optionally) dispatches
the gaps as labelled issues so the two armies can fix them. This page documents what it checks,
its run modes, how it spawns follow-on work, and the **scheduled cloud routine** that runs it daily.

> TL;DR — by default the heartbeat only **looks and reports**. It only **files issues** with
> `--apply`, and only **auto-spawns Copilot workers** with `--apply --auto`. Pick the level of
> autonomy you're comfortable with.

## What it checks

| Check | Severity | Dispatched on `--apply`? |
|---|---|---|
| `unregistered-contract` — a spoke contract not listed in [docs/contracts.md](contracts.md) | `warn` | No (report only) |
| `unvendored-contract` — backend-core OpenAPI not vendored into a consumer (frontend/middle) | `gap` | **Yes** |
| `agent-pack-drift` — a spoke has <50% of the hub's `.claude/agents` files (sync is stale) | `warn` | No (report only) |
| `pr-subscription-missing` — a repo is missing a PR-event workflow (`copilot-review`/`review-loop`/`claude`) | `gap` | **Yes** |
| `secret-stale` — Key Vault secret metadata exceeds the rotation cadence + grace window (`--secrets`) | `warn` | No (report only) |
| `secret-local-stale` — Key Vault metadata is newer than the local derived target (`--secrets` / status JSON) | `warn` | No (report only) |
| Fleet health — open PRs + recent failed runs per repo (watch for the [minutes-cap startup-failure signature](setup.md)) | info | No |

**Severity is the safety dial:** only `gap` findings are ever auto-filed. `warn` findings always
stay in the report — you decide whether to act. The Postman spec+mock check can't run from the
heartbeat (it needs local Key Vault creds), so it's surfaced as a reminder, not a finding.

## Run modes

```bash
node tools/fleet-heartbeat.mjs            # dry-run: inventory + report only (default)
node tools/fleet-heartbeat.mjs --apply    # also file a deduped issue per gap as agent-army-task
node tools/fleet-heartbeat.mjs --apply --auto  # gaps filed as copilot-task → Copilot auto-spawns
node tools/fleet-heartbeat.mjs --json      # machine-readable findings (works with any of the above)
node tools/fleet-heartbeat.mjs --secrets   # include Key Vault secret age checks; metadata only
node tools/fleet-heartbeat.mjs --secrets-only --secrets-status status.json  # fixture/status check only
```

`--secrets` reads Key Vault secret metadata via `az keyvault secret show`; it
does not fetch or print secret values. For CI and offline checks, feed the
redacted output of `python scripts/secrets/status.py --json` through
`--secrets-status <json>`. `--secrets-only` skips GitHub fleet inventory and
evaluates only that redacted status payload.

The label a gap gets is the autonomy switch:

| Invocation | Gap label | What happens to the issue |
|---|---|---|
| `--apply` | `agent-army-task` | Filed and **waits** — `/loop` or a human picks it up. No worker spawns. |
| `--apply --auto` | `copilot-task` | Filed **and** the `copilot-coding-agent` workflow auto-spawns Copilot to implement it → opens a PR. |

`--apply` is **read-mostly**: it creates issues but never pushes code or runs an agent.
`--apply --auto` is the only mode that fans out into worker sessions.

## Dispatch is deduplicated

Before filing, `--apply` searches the target repo for an open issue titled `heartbeat: <kind>`.
If one exists, it **skips**. This is what makes a *daily* apply safe — a gap that takes a week to
fix produces **one** issue, not seven. Each filed issue is `[Enabler] heartbeat: <kind>` in the
repo that owns the gap, labelled with the routing label + `Enabler`.

## The spawn model (it's a finite chain, not a cascade)

```
cron / hook  ──>  1 heartbeat session
                       │  files deduped issues for gaps (--apply)
                       ▼
              ┌─ copilot-task ──> Copilot coding session ──> PR ──> review bots
              └─ agent-army-task ──> sits until /loop or a human
```

Key property: **only the heartbeat dispatches.** Worker sessions *do work* (open PRs) — they do
not file more heartbeat issues, so nothing re-triggers the heart. The graph is a shallow tree, not
a loop. The "others" that spawn are GitHub-event-driven and decoupled (a `copilot-task` issue wakes
Copilot; a PR wakes the review bots) — see [Autonomous Review Loop](pr-review-loop.md).

## What triggers the heartbeat

| Trigger | Mode | Where it runs | Notes |
|---|---|---|---|
| **SessionStart hook** (`.claude/settings.json`) | dry-run | Your local Claude Code session | "The mind hears the heart" — every session opens with a fresh pulse. |
| **Scheduled cloud routine** (cron) | configurable | Anthropic cloud (see below) | Unattended daily audit. **Off** the GitHub Actions minutes cap. |
| **`/loop`** (manual) | whatever you type | Your live session | Ad-hoc polling — see [the recurring-loop section in CLAUDE.md](../CLAUDE.md). |

## The scheduled cloud routine

A claude.ai **routine** ("Fleet sync & contract audit") runs the heartbeat on a cron without a
human present. Manage routines at **<https://claude.ai/code/routines>**.

| Field | Value |
|---|---|
| Name | `Fleet sync & contract audit` |
| Trigger ID | `trig_01M3Brd8dLR4U33iCr5zsW7w` |
| Schedule | cron `0 10 * * *` UTC = **06:00 America/New_York** daily |
| Environment | `HypergraphX` (Anthropic cloud) |
| Repo | clones `nickpclarke/AgentArmy` `main`, **fresh, each run** |
| Model / tools | `claude-sonnet-4-6` · Bash, Read, Glob, Grep |
| Mode | the prompt's step 1 (`--apply` / `--apply --auto` / dry-run) |

**How it differs from a GitHub Action — important for fleet management:**

- It is **not** GitHub Actions, so it does **not** consume the metered Actions minutes cap.
- It runs in an **isolated cloud sandbox** with a fresh `git` checkout + authenticated `gh`. It has
  **no access to your local machine, no Azure Key Vault, and no web** (the prompt forbids
  `WebSearch`/`WebFetch` — too heavy for a recurring job, and Postman publish needs Key Vault creds
  it doesn't have).
- The **starting prompt is a stored field** on the routine, set once (via the `/schedule` skill /
  RemoteTrigger API or the web UI) — you don't type it each run. Changing behaviour = updating that
  prompt.
- **Output lands in the routine's run log** (read it at the URL above). In `--apply` mode it also
  files issues; in dry-run it only reports.
- Because the routine clones `main`, **any change to `fleet-heartbeat.mjs` must be merged to `main`
  before the routine will use it.**

### Graduating autonomy

Start conservative and promote once you trust each level:

1. **dry-run** — daily read-out, files nothing. Watch a few runs.
2. **`--apply`** — files `agent-army-task` issues for hard gaps; no workers spawn. You triage.
3. **`--apply --auto`** — files `copilot-task` issues; Copilot auto-implements each. Full autonomy.

Flip a level by updating the routine's prompt step 1. No code change is needed to move between
levels — the `--auto` flag already gates the spawn behaviour.

## Related

- [Inter-Layer Contracts registry](contracts.md) — the single source the heartbeat audits against.
- [Spoke Helper Sync](spoke-sync.md) — the hub→spoke sync the `agent-pack-drift` check watches.
- [Autonomous Review Loop](pr-review-loop.md) — what happens to PRs the spawned workers open.
- [SessionStart hooks](hooks.md) — how the dry-run pulse is wired into every local session.
