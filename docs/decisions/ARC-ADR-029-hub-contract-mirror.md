# ARC-ADR-029 — Central Hub Contract Mirror for Spoke-Produced Contracts

| Field | Value |
|---|---|
| ID | ARC-ADR-029 |
| Status | Proposed |
| Date | 2026-05-28 |
| Deciders | Hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | contracts, registry, mirror, sync, hub-spoke, design-tokens, fleet-heartbeat, tooling |

---

## Context

The hub registry ([`docs/contracts.md`](../contracts.md)) is an *index*: it records every inter-layer contract's producer, consumers, status, and governing ADR, but it does not hold the contract artifacts themselves. Producer spokes are the authoritative source: `frontend-core/contract/design-tokens.json` lives in the frontend-core repo; `backend-core/contracts/backend-core.openapi.json` lives in the backend-core repo; and so on. This is correct — "a producer layer publishes a versioned contract; consumers bind only to that" (docs/contracts.md).

Two converging pressures now expose a gap in this arrangement.

**Hub-side tooling that needs the contract bytes.** A "Claude Design" ingestion package being built in the hub must read `frontend-core/contract/design-tokens.json` (W3C DTCG format) as part of its ingestion pipeline. The design-token contract is the first concrete trigger; the same need will arise for component-API contracts (FE-2), theme contracts (FE-3), and any future artifact a hub agent or cross-cutting tool must parse. Running from a hub checkout, this tooling has no local copy of those files.

**Fleet-heartbeat fragility on cross-repo reads.** The heartbeat (`tools/fleet-heartbeat.mjs`) inventories contracts across spokes by calling `gh api repos/<owner>/<spoke>/git/trees/main?recursive=1` — a live GitHub API call. As documented in the heartbeat's own comments (referencing AgentArmy issue #207 from the 2026-05-26 cron run), this tree-fetch is transient-hiccup-prone: a rate-limit or momentary API error returns an empty tree, which causes every file-based gap check to either false-positive or silently skip. The heartbeat distinguishes this failure mode (`tree-fetch-failed` finding, `MIN_TREE_FILES = 10` guard), but the underlying cause is that cross-repo reads are inherently fragile as a primary data path.

The hub currently holds only four hub-*produced* contract artifacts in `contracts/`: `health.openapi.yaml`, `llm-gateway.openapi.yaml`, `problem-details.openapi.yaml`, and `webhook-receiver.openapi.yaml`. There is no stable local copy of any spoke-produced contract for hub tooling to read.

The decision to be made is: **should the hub maintain a read-only, auto-synced local mirror of producer-spoke contract artifacts, and if so, what mechanism manages that mirror?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **One stable local ingestion point.** Hub-side tooling and agents (Claude Design, fleet-heartbeat, hub-level code generators) need to read spoke contract files without issuing live cross-repo API calls on every invocation. |
| D2 | **Single source-of-truth integrity.** The producer spoke must remain the owner of the contract artifact. The mirror must be structurally incapable of becoming a place people edit. Ownership is the central tension: ARC-ADR-005 and docs/contracts.md both establish "producer owns source-of-truth"; this ADR must not create a second source. |
| D3 | **Drift is detectable and loud.** A stale or hand-edited mirror is worse than no mirror — it gives hub tooling false confidence. Any divergence between the mirror and the producer's HEAD must be surfaced, not silently tolerated. |
| D4 | **Heartbeat-friendly and low operational burden.** Consistent with the D3 driver in ARC-ADR-027: the mechanism must not add per-sprint manual toil or require a new shared service to operate. The heartbeat already runs on a scheduled cron and can own drift-detection at no extra cost. |
| D5 | **Works across the N-layer hub/spoke topology.** The solution must generalize to all spoke repos (frontend-core, backend-core, middle-core, future spokes) as each adds contracts, not just the first one. |
| D6 | **Provenance is machine-readable.** Every mirrored file must carry a record of its origin (source repo, commit SHA, copy timestamp) so hub tooling can cite provenance and CI can verify it, without having to re-fetch the file to check. |

---

## Considered Options

### Option 1 — Status quo: registry-only, cross-repo reads on demand

The hub continues to index contracts in `docs/contracts.md` without holding copies. Hub tooling (Claude Design, heartbeat) fetches from spokes live via `gh api` or the GitHub raw-content endpoint when it needs the bytes.

**Pros:**
- No new files or automation to maintain.
- Always reads the producer's current HEAD — no staleness window.
- Consistent with the "index, not store" model already in place.

**Cons:**
- Unreliable as a primary data path: the heartbeat's `tree-fetch-failed` finding (and issue #207) are real evidence of transient failure. An ingestion pipeline that fails on a GitHub API hiccup is not production-grade.
- Rate-limited: GitHub's REST API imposes per-hour and per-minute rate limits. A hub agent that reads 10 contract files per invocation, invoked frequently, will hit limits.
- Cross-repo reads require the calling process to have a valid GitHub token. Hub-local scripts and agents that run offline or in sandboxes cannot access spoke files at all.
- Does not address Claude Design's need to read design-tokens as a local file; that tool is not a `gh`-capable process.

This option becomes the **baseline** for comparison but is insufficient as-is for the stated triggers.

---

### Option 2 — Git submodules pointing at each producer's contract directory

Each spoke's contract directory is registered as a Git submodule inside the hub under `contracts/vendored/<spoke>/`.

**Pros:**
- Native Git mechanism; no custom automation.
- Submodule pinned to a specific commit SHA — provenance is exact.
- Standard tooling (`git submodule update --remote`) refreshes all mirrors at once.

**Cons:**
- Submodule UX is notoriously error-prone. A fresh `git clone` of the hub without `--recurse-submodules` yields empty `contracts/vendored/` directories, silently. Hub tooling that relies on the mirror will fail for anyone who didn't know to pass the flag.
- Submodule pointers are pinned at a commit, not a branch tip. Keeping them current requires explicit `git submodule update --remote` + a commit to the hub — a manual step or a cron that produces noisy "bump submodule pointer" commits.
- Submodule granularity is the entire submodule target: you cannot cheaply point a submodule at a subdirectory. Pointing at the spoke's root and navigating to `contract/` is workable but inelegant; filtering to only contract artifacts is not possible at the submodule layer.
- A spoke's `main` branch history appears inside the hub's `git log` in confusing ways.
- The `scripts/spoke_sync.config.json` already does not sync spoke-owned directories into the hub (per ARC-ADR-023 platform ownership). Adding submodules creates a second, divergent sync mechanism.

---

### Option 3 — Git subtree pulling producer contract directories into `contracts/vendored/<spoke>/`

`git subtree add` (and `git subtree pull`) imports a subdirectory from a remote repo into the hub tree as ordinary commits.

**Pros:**
- No special `--recurse-submodules` clone flag needed; the files are real hub files.
- History is imported, giving some audit trail.
- Works with standard `git clone`.

**Cons:**
- `git subtree pull` merges the foreign history into the hub's DAG, producing interleaved commit graphs that are confusing in `git log` and `git blame`.
- Subtrees are even less commonly understood by contributors than submodules; the "how do I update this?" question has a non-obvious answer.
- Updating requires remembering which subtree prefix maps to which remote + branch, and running the subtree pull manually or via a script — equivalent operational toil to a GitHub Action but without the scheduling and audit trail.
- Subtrees copy the files but carry no machine-readable provenance field in the file itself (no SHA header); drift detection requires `git diff` against the remote, not a simpler manifest check.
- Like submodules, this creates a second inbound sync path that sits outside the heartbeat's existing dispatch model.

---

### Option 4 — Sync GitHub Action (scheduled + `workflow_dispatch`) that copies producer contracts into `contracts/vendored/<spoke>/` and commits

A dedicated workflow (`.github/workflows/sync-contract-mirror.yml`) runs on a schedule (e.g., daily at UTC 06:00) and on `workflow_dispatch`. For each spoke in the known list, it fetches every file under the spoke's `contract*/` paths via `gh api`, writes them to `contracts/vendored/<spoke>/`, prepends a YAML front-matter provenance block (or writes a sidecar `_provenance.json`), and commits the result to the hub with a message such as `chore(mirror): sync spoke contracts [frontend-core@<sha>]`. The mirror directory carries a top-level `contracts/vendored/MIRROR.md` that documents its read-only nature and forbids hand-edits.

**Pros:**
- Files are ordinary hub-checked-in files, fully accessible to any local tool, agent, or offline process without a GitHub token or live API call. Claude Design reads `contracts/vendored/frontend-core/design-tokens.json` as a local path — no cross-repo fetch required.
- The heartbeat gains a local fallback path: if a live tree-fetch fails, it can read the mirror instead of skipping the check. The `tree-fetch-failed` false-positive problem is eliminated for any contract that has been mirrored.
- Provenance is machine-readable (SHA + timestamp in `_provenance.json` alongside each mirrored file) and checkable by CI without re-fetching the spoke.
- Drift detection is cheap: the heartbeat (or a CI step) compares `_provenance.json`'s `commit_sha` against the spoke's current `main` HEAD via a single `gh api repos/<owner>/<spoke>/commits/main --jq .sha` call. A stale mirror emits a `mirror-stale` warning; a hand-edit would show as a local diff against the committed provenance content and can be caught by a pre-commit hook or CI file-hash check.
- The automation is a single YAML file and a small shell script — no new runtime service, no new CLI to learn, no special clone flags.
- Scheduling and dispatch align naturally with the heartbeat's existing cron pattern; the sync action can be triggered by the same daily cron or by a hub `workflow_dispatch` when a spoke opens a PR that changes a contract file (via a `repository_dispatch` event from the spoke).
- Adding a new spoke is a one-line change to the workflow's spoke list. The mechanism is topology-generic from day one (D5).
- The commit history of `contracts/vendored/` is a clean, linear record of when each contract version was mirrored and from what SHA — better provenance than submodule pointer bumps.

**Cons:**
- There is a staleness window: if a spoke merges a contract change and the sync has not yet run, the hub mirror lags. For design-token ingestion this is acceptable (daily sync is sufficient); for tight contract-test loops it is not — but those loops (Pact-style consumer tests) should run against the producer directly, not the mirror. The mirror is explicitly a *read replica for tooling and agents*, not a test surface.
- The workflow produces commit noise on a schedule. Mitigation: the commit step is conditional — if `git diff --quiet contracts/vendored/` after the fetch, the workflow exits without committing. Commits only land when there is a real change.
- If a spoke renames or moves its contract directory, the sync script silently collects nothing until its path list is updated. Mitigation: the heartbeat's existing `unregistered-contract` check catches spoke-side contract files that are not in the registry; a complementary `mirror-path-missing` check can fire when an expected spoke path yields zero files.
- GitHub Actions minutes usage: the sync is a lightweight shell operation (fetch + diff + conditional commit) and runs at most once daily. This is negligible against the cap and far cheaper than the `claude.yml` action that the team explicitly reserves for committed work.

**This is the recommended option.** The combination of local file availability, machine-readable provenance, cheap drift detection, schedule alignment with the heartbeat, and low operational burden addresses all six decision drivers without introducing a new shared service or an obscure Git mechanism.

---

### Option 4a — Published package or Postman collection as the distribution vehicle (mentioned for completeness)

Spokes could publish their contract artifacts to an npm package (for JSON-Schema and TypeScript types) or to the AgentArmy Postman workspace (for OpenAPI/AsyncAPI). Hub tooling would install or pull from there.

This is the right approach for *consumer spokes* that need generated clients (npm install + codegen); it is already the recommended path for Postman mocks. It is not a substitute for the hub-mirror use case because: (a) npm install requires a build step and does not produce a plain file tree readable by arbitrary agents; (b) Postman publish requires local Key Vault credentials and cannot be done from the sync workflow without secret provisioning (noted as a heartbeat limitation); (c) it adds a third distribution channel alongside the hub registry and spoke repos without eliminating the cross-repo-read problem for agents that need raw bytes. Treat this as complementary to Option 4, not a replacement.

---

## Decision Outcome

**Option 4 is adopted: a sync GitHub Action maintains a read-only, auto-committed mirror at `contracts/vendored/<spoke>/` in the hub.**

### Mirror layout

```
contracts/
  vendored/
    MIRROR.md                          ← Explains read-only nature; forbids hand-edits
    frontend-core/
      _provenance.json                 ← { "repo": "...", "commit_sha": "...", "synced_at": "..." }
      design-tokens.json               ← mirrored from frontend-core/contract/design-tokens.json
      frontend-bff.openapi.json        ← mirrored from frontend-core/contract/frontend-bff.openapi.json
      [other FE-* backlog contracts as they ship]
    backend-core/
      _provenance.json
      backend-core.openapi.json
      [other BE-* backlog contracts as they ship]
    middle-core/
      _provenance.json
      [MC-* backlog contracts as they ship]
```

The `contracts/` root continues to hold only hub-produced contracts (`health.openapi.yaml`, etc.). `contracts/vendored/` is a clearly separated subtree with its own `MIRROR.md` explaining its nature.

### Provenance format

Each spoke directory carries a `_provenance.json` sidecar:

```json
{
  "repo": "nickpclarke/frontend-core",
  "branch": "main",
  "commit_sha": "<40-char SHA>",
  "synced_at": "2026-05-28T06:00:00Z",
  "paths_mirrored": ["contract/design-tokens.json", "contract/frontend-bff.openapi.json"]
}
```

This makes provenance checkable by any process that can read a JSON file — no `git log`, no API call.

### Sync workflow behavior

- **Schedule:** daily at UTC 06:00 via `schedule: cron: '0 6 * * *'`.
- **On demand:** `workflow_dispatch` for immediate refresh (e.g., after a spoke merges a contract change).
- **Spoke-push trigger (optional, later):** spokes can emit a `repository_dispatch` event from their own `main` merge workflow to trigger the hub sync immediately. This eliminates the staleness window for high-priority contracts. Wire this when the daily cadence proves insufficient.
- **Conditional commit:** the workflow runs `git diff --quiet contracts/vendored/` after fetching; it commits only when something changed. No-op runs produce no commits.
- **Commit message format:** `chore(mirror): sync spoke contracts [<spoke>@<short-sha>]`
- **Spoke path registry:** the workflow reads a small config (either inline YAML or a `contracts/vendored/mirror-config.json`) that maps each spoke to the paths it should mirror. This is the single place to add a new spoke or a new contract path; it does not require editing the workflow YAML itself.

### Seeding order

`frontend-core` is the first spoke to be mirrored because the immediate trigger is the Claude Design ingestion package needing `design-tokens.json` (FE-1 in the backlog). The `backend-core.openapi.json` vendoring is already handled by consumer spokes via the established consumer-vendoring pattern (ARC-ADR-005); the mirror gives hub tooling a copy alongside that existing pattern.

### What the mirror is not

- It is **not a second source of truth.** Producers remain authoritative. A change to a mirrored file must be made in the producer spoke and will be overwritten on the next sync.
- It is **not a test surface.** Consumer Pact tests run against the producer's live or published artifact, not the mirror. The mirror is a read replica for tooling and agents, not a contract-enforcement boundary.
- It is **not a replacement for consumer vendoring.** Consumer spokes still vendor the contracts they bind to (per the rule in docs/contracts.md). The hub mirror serves hub-side tooling only.

---

## Consequences

**Positive:**

- Claude Design and any hub agent can read spoke contract files as ordinary local paths — no live GitHub API dependency, no token requirement, no rate-limit exposure.
- The heartbeat's `tree-fetch-failed` false-positive risk is reduced: for mirrored contracts, the heartbeat can fall back to the local mirror rather than skipping the gap check entirely.
- Provenance is machine-readable and CI-checkable. A hand-edit to a mirrored file shows immediately as a local-vs-provenance-hash divergence, and can be caught before merge.
- Adding a new spoke to the mirror is a one-line config change; the mechanism is already generic.
- The sync commit log provides a clean, dated record of when each contract version entered the hub — useful for incident investigation ("what version of design-tokens was the hub running on date X?").

**Negative:**

- The mirror introduces a staleness window (up to 24 hours on a daily schedule) between a spoke contract change and hub tooling seeing it. This is acceptable for Claude Design ingestion and heartbeat inventory but must be documented as a known limitation so engineers do not mistake the mirror for the producer's live HEAD.
- The `contracts/vendored/` subtree adds file count to the hub. As the fleet grows to more spokes and more contract artifacts, this grows proportionally. Mitigation: the mirror-config can exclude large or infrequently-needed artifacts; the default should be conservative (only contracts with known hub-side consumers).
- The sync workflow produces GitHub Actions minutes usage. Volume is low (once daily, lightweight operation) but is nonzero. Log the sync duration and alert if it exceeds a threshold.

**Neutral:**

- The mirror does not change the ownership model at all — producers own, consumers vendor, the hub indexes. This ADR adds a *hub-side read replica* as a new category of artifact in the hub, sitting alongside but distinct from the hub's own produced contracts.
- Consumer spokes (frontend-core, middle-core) still vendor the contracts they bind to in their own repos. The hub mirror is parallel, not a replacement.

---

## Confirmation

The implementation is correct when all of the following hold:

1. `contracts/vendored/` exists in the hub and contains at minimum `frontend-core/_provenance.json` and `frontend-core/design-tokens.json` (the seed case).
2. `contracts/vendored/MIRROR.md` is present and explicitly states the directory is read-only and auto-generated.
3. `.github/workflows/sync-contract-mirror.yml` exists, runs on `schedule` and `workflow_dispatch`, and passes on the first triggered run.
4. The sync workflow's commit step is conditional: a second consecutive run with no upstream changes produces no new commit.
5. Each `_provenance.json` contains `repo`, `branch`, `commit_sha`, and `synced_at` fields with a valid ISO-8601 timestamp and a 40-character SHA.
6. The fleet-heartbeat emits a `mirror-stale` warning (severity `warn`, kind `mirror-stale`) when the `commit_sha` in a spoke's `_provenance.json` does not match the spoke's current `main` HEAD, and this warning is visible in a dry-run output.
7. A CI step (pre-commit hook or workflow check) detects hand-edits to files under `contracts/vendored/` by comparing each file's hash against the value recorded in `_provenance.json`, and fails the check if they diverge.
8. A hub-side ingestion script or agent (e.g., Claude Design) reads `contracts/vendored/frontend-core/design-tokens.json` as a local path with no `gh api` call in the hot path.

---

## Related

- [ARC-ADR-027 — Contract Backlog Discipline](ARC-ADR-027-contract-backlog-discipline.md) — the backlog rows (FE-1 through FE-8, MC-1 through MC-5, etc.) define which contracts will be mirrored as they ship; the mirror-config is driven by backlog promotion to Registry.
- [ARC-ADR-005 — backend-core OpenAPI Contract](ARC-ADR-005-backend-core-openapi-contract.md) — establishes "producer owns source-of-truth" and the consumer-vendoring pattern; this ADR adds a hub-side read replica alongside that pattern without altering it.
- [ARC-ADR-023 — Fleet Container Tiering Strategy](ARC-ADR-023-container-tiering-strategy.md) — the hub-owns-platform precedent informs the pattern of hub-owned automation managing cross-spoke artifacts without those artifacts being spoke-authored.
- [`docs/contracts.md`](../contracts.md) — the registry this ADR extends; `contracts/vendored/` does not replace it. The registry continues to be the single source for producer/consumer/status/ADR/test; the mirror provides the file bytes that the registry indexes.
