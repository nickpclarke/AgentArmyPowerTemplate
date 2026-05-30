# Spoke lifecycle — how a spoke is born, dressed, and watched

The single front door for adding a new layer repo (a **spoke**) to the fleet. Every
spoke goes through the same four stages; this page is the canonical map and links the
detailed docs for each stage. If you only read one spoke doc, read this one.

> **The rule, in one line:** a spoke exists when it is listed in
> [`scripts/spoke_sync.config.json`](../scripts/spoke_sync.config.json). That file **is**
> the registry — the dressing sync reads it, and the fleet heartbeat reads it. Add a repo
> there and the rest of the fleet starts treating it as a spoke automatically.

## The four stages

```
  1. SCAFFOLD        2. REGISTER          3. DRESS / HYDRATE     4. WATCH
  new-spoke.sh   →   spoke_sync.config →  sync_helpers_to_spokes → fleet-heartbeat
  (skeleton)         .spokes += repo      (packs land in spoke)    (drift enforced)
```

### 1. Scaffold — `scripts/new-spoke.sh`

One command emits a complete spoke skeleton (the 4 manifests, a tier-correct
`image.json` + doctor, a README with the next-step checklist). Realises ARC-ADR-024's
golden path.

```bash
./scripts/new-spoke.sh --name worker-core --system agentarmy --layer worker
```

Then `git init` + `gh repo create` and push (the script prints the exact commands and
the GitHub Secrets to wire). See the script header for all flags. *Skip this stage* if
the repo already exists (e.g. a capability extracted to its own repo per an ADR, like
`agentarmy-forge` under ARC-ADR-029).

### 2. Register — `scripts/spoke_sync.config.json`

Add the repo name to the `spokes` array. **This is the one edit that makes the hub
"know the rule".** From this point:

- the **dressing sync** will hydrate it (stage 3), and
- the **heartbeat** will watch it for drift (stage 4).

No code changes anywhere else — both consumers read this list.

### 3. Dress / hydrate — `scripts/sync_helpers_to_spokes.py`

The **dressing routine** turns a bare repo into a fully-equipped AgentArmy template for
every supported agentic coder. It mirrors the hub-owned packs into the spoke and opens
(auto-merges) a PR. Full reference: **[spoke-sync.md](spoke-sync.md)**.

```bash
python scripts/sync_helpers_to_spokes.py --spoke <name> --dry-run   # preview
python scripts/sync_helpers_to_spokes.py --spoke <name>             # PR + auto-merge
```

What lands (grouped by coder — see [spoke-sync.md](spoke-sync.md) for the full list):

| Pack | Files | For |
|---|---|---|
| Shared law | `AGENTS.md`, `CONSTITUTION.md` | all coders (Codex reads `AGENTS.md` natively) |
| Claude Code | `.claude/agents`, `.claude/commands`, settings, hooks | Claude Code |
| OpenAI Codex | `.codex/agents` (TOML), `.codex/config.toml`, `.codex/hooks.json` | Codex |
| Gemini Antigravity | `.agents/plugins` | Antigravity |
| Review automation | `.github/workflows/claude.yml`, `copilot-review.yml`, `review-loop.yml` (hub-authoritative, portable) | all — needs each spoke's secrets to *run* |
| Helpers | `.mcp.json`, `tools/status.mjs`, `tools/fleet-heartbeat.mjs`, board scripts | all |

**How a spoke proves how it got hydrated:** every dressing run writes a provenance
stamp to **`.claude/.agentarmy-sync.json`** in the spoke — the hub commit SHA, the list
of synced paths, and the timestamp. Read that file in any spoke to see exactly when and
from what hub state it was dressed. The hub is always the source of truth; never
hand-edit a synced pack in a spoke (the next sync overwrites it).

**Repo-specific welcome pack:** the dressing **seeds a `CLAUDE.md` only if the spoke
has none** (it imports `@CONSTITUTION.md` + `@AGENTS.md` and leaves room for the layer's
own notes), and never touches an existing one. A spoke's own **`README.md`** is the
human-facing mission + file-structure orientation and is **repo-owned** — the sync never
writes it. So: fleet law is shared and synced; repo identity is local and owned.

### 4. Watch — `tools/fleet-heartbeat.mjs`

The heartbeat reads the same registry and, each cycle, asserts every spoke is fully
hydrated: it flags **`coder-pack-drift`** if any of the three coder packs falls below
50% of the hub's count (i.e. the dressing sync hasn't run, or a `.gitignore` dropped a
pack), plus contract-vendoring, PR-event-workflow, and container-tier drift. Default is
dry-run report; `--apply` dispatches gaps as issues. Full reference:
**[fleet-heartbeat.md](fleet-heartbeat.md)**.

## Adding a new spoke — checklist

1. **Scaffold** (or skip if the repo exists): `./scripts/new-spoke.sh --name … --system … --layer …`, then push.
2. **Register**: add the repo to `spokes` in [`scripts/spoke_sync.config.json`](../scripts/spoke_sync.config.json).
3. **Dress**: `python scripts/sync_helpers_to_spokes.py --spoke <name>` (dry-run first).
4. **Verify**: `node tools/fleet-heartbeat.mjs` — confirm the spoke appears with no `coder-pack-drift`.
5. **Wire secrets** on the new repo: `PROJECT_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, cloud OIDC (see `new-spoke.sh` output).

## Related docs

- **[spoke-sync.md](spoke-sync.md)** — the dressing routine in full (what syncs, adding a coder, CI).
- **[agent-onboarding.md](agent-onboarding.md)** — orientation for an agent *running inside* a spoke microVM.
- **[onboarding.md](onboarding.md)** — auth/token sanity check for a fresh fork or runner.
- **[n-layer-spoke-rules.md](n-layer-spoke-rules.md)** — contract-first / mock-first rules across layers.
- **[spoke-hub-callback.md](spoke-hub-callback.md)** — how spoke PRs report back to the hub board.
- **[fleet-heartbeat.md](fleet-heartbeat.md)** — the heartbeat's full check + dispatch reference.
