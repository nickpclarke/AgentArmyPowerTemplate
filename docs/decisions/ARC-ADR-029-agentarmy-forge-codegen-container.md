# ARC-ADR-029 — agentarmy-forge: Extract Code Generator into a Function-Tier Container with Ontology-Driven Multi-Target Emit

| Field | Value |
|---|---|
| ID | ARC-ADR-029 |
| Status | Accepted |
| Date | 2026-05-27 |
| Deciders | Hub owner (Nicky Clarke) — accepted 2026-05-28 |
| Supersedes | — |
| Superseded by | — |
| Tags | codegen, forge, function-tier, container, ontology, rdf, backend-core, middle-core, frontend-core, generator-first |

---

## Context and Problem Statement

The fleet already runs a code generator: `middle-core`'s `modelgen` reads `model/middle-core/model.yaml` and emits `DataPlatformContracts.g.cs` plus the `I{ObjectType}Projection` interfaces that `backend-core` UDA consumes (per [RT7 MCR-F4](../release-trains/RT7-middle-core-runtime.md)). The "generator-first" pattern is load-bearing — feedback memory has it as a fleet invariant ("keep the model→generator→output loop untouched; fix model/generator not generated files").

That generator currently has three structural problems:

1. **It lives inside the middle-core runtime image.** Generator changes force a middle-core runtime redeploy even when nothing about the runtime changed. Generation is bursty CPU/memory; the runtime is steady-state web — different scale curves under one roof.
2. **It only emits C# for middle-core.** Frontend-core's TS types and backend-core's Pydantic models are hand-maintained against the same conceptual model — every divergence is a contract drift bug waiting to happen.
3. **Its input is a single YAML.** The fleet is investing in **RDF / OWL** as the canonical knowledge representation ([ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md), [ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md)). The generator can't see that ontology — it can only see its YAML projection.

At the same time, **backend-core has no file-ingestion path for RDF.** Operators today hand-curate the model YAML; there's no way to feed in a Turtle / JSON-LD file from an external source and have it land in the RDF database (Fuseki per ADR-019) after shape validation. The generator can't consume what nobody is producing.

The decision: **What is the right architectural home and input model for the fleet's code generator?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Preserve "generator-first."** Whatever changes, the model→generator→output loop stays the single source of truth. We do not introduce hand-edits to generated files; we do not let consumers drift from the contract. |
| D2 | **Fit ARC-ADR-023 function-tier criteria explicitly.** Any extraction must clear one of: different hardware profile, different scale curve, different release cadence, different blast radius. |
| D3 | **Ontology-first inputs.** RDF / OWL is the canonical input format per ADR-016/019. The generator should consume an ontology (Turtle / JSON-LD / N-Triples), not a bespoke YAML. The YAML path can stay as a back-compat input for the existing middle-core model. |
| D4 | **Multiple input sources.** The generator must work from a live RDF endpoint (backend-core's Fuseki-backed snapshot API), from local files, AND from a blob store (Azure Blob). Dev workflows need files; production wants the live endpoint; archival flows want blobs. |
| D5 | **Multi-target emit.** TypeScript (frontend-core types + tool-call schemas), C# (middle-core contracts + LangGraph tool definitions), Python (backend-core Pydantic models + FastAPI route stubs) — one emitter pipeline, three language adapters. |
| D6 | **Source-only delivery in v1.** Forge emits source files and opens Pull Requests against consumer spokes. It does NOT build binaries, push artifacts, or deploy to running services — those responsibilities already have owners (`deployment-engineer`, `release-manager`, consumer CI). Bundling them in forge would inflate blast radius and duplicate existing pipelines. |
| D7 | **Direct-to-main PR convention.** Generated PRs target consumer `main` branches and auto-merge on green CI — matching the fleet's auto-merge-default culture and small-blast-radius momentum pattern. The defense is forge's own doctor + consumer CI, not a staged-branch human review gate. |
| D8 | **Triggered by webhook + CLI.** Backend-core notifies forge on ontology change (webhook); operators / agents can also invoke forge on demand (CLI / MCP control plane). No scheduled polling — wasteful and adds drift detection complexity. |

---

## Considered Options

### Option 1 — Extract into `agentarmy-forge` function-tier image hosted in the hub (`templates/forge-image/`); ontology input from backend-core HTTP / file / blob; multi-target source emit; direct-to-main PRs

A new function-tier image (`templates/forge-image/`, container `agentarmy-forge`) hosts the generator, with its source living in the hub repo. Inputs:

- **HTTP:** `GET /ontology/snapshot?version=…` on backend-core (new contract)
- **File:** local `.ttl` / `.jsonld` / `.nt` / `.yaml` (back-compat for existing middle-core model)
- **Blob:** Azure Blob storage URI (with managed-identity auth)

Outputs: source files for any combination of frontend-core / middle-core / backend-core, opened as PRs against each spoke's `main`. Generation and delivery are coupled in one container — forge holds write/PR access to every consumer spoke.

### Option 1b — `agentarmy-forge` as a standalone repo; generation isolated from delivery; flag-gated adoption (recommended)

Same function-tier container as Option 1, but the forge's source lives in its **own repository** (`nickpclarke/agentarmy-forge`) rather than `templates/forge-image/` in the hub. Two structural changes follow from the split:

1. **The repo's CI _is_ the generation loop.** Push → run goldens (byte-identical `.g.cs` / `.g.ts` / `.g.py` diffs) → multi-target smoke-compile (`tsc --noEmit`, Pydantic import, optional `dotnet build`). None of the hub's other gates (Codex/Antigravity sync, glossary regen, fleet-heartbeat) sit in the way, so the iterate-until-it-compiles loop is fast and focused. Input is verifiable (SHACL/ShEx shape validation on the ontology) and output is verifiable (compile + golden) — the forge is a pure function with both ends checkable in isolation.

2. **Generation is decoupled from delivery.** Forge **emits + publishes** verified generated source as a *versioned artifact* (tagged release / package keyed by `ontology@<sha>`) instead of opening direct-to-main PRs. Each app-tier spoke then **adopts** a pinned forge output version **behind a feature flag** — the flag gates "this spoke is on contract vN," giving independent per-spoke rollout and a one-flip rollback. The exact publish + adopt mechanism is an open question (see below); `feature-flag-engineer` owns the flag/rollout half once chosen.

This reverses Option 1's D6/D7 posture: forge no longer needs write access to consumer repos, and the blast radius of a bad emit is "an unadopted artifact version," not "a merged PR on `main`."

### Option 2 — Leave the generator inside middle-core, add ontology input + multi-target emit there

Same capability gains, no container extraction. Middle-core's runtime image absorbs the .NET + Python + Node toolchains needed for multi-language emit.

### Option 3 — Per-spoke generators (each spoke hosts its own emitter, all reading the same ontology)

Three small generators, one per consumer language, each living inside its consumer spoke. They subscribe to the same backend-core ontology snapshot.

### Option 4 — Status quo: keep YAML-driven C#-only generation in middle-core; do nothing

---

## Decision Outcome

**Accepted: Option 1b.** The HITL framing: the hub owner decides, because this is a fleet-wide architectural extraction touching all three application-tier spokes plus backend-core's contract surface.

**Hub owner decision (2026-05-28): Option 1b.** The forge moves to its own repo (`nickpclarke/agentarmy-forge`) so the generation loop can be iterated in isolation against verifiable input/output, and delivery into the app tier is flag-gated rather than direct-PR. The v0/v1/v2 implementation already merged on the hub (`templates/forge-image/`, PR #295) becomes the seed that relocates into the standalone repo; the hub retains the ADR + tiering governance. The architectural home is **decided** — the v2.5 repo extraction and the publish/adopt delivery mechanism (Open Question 6) are tracked implementation follow-ups, not blockers to the decision.

### Recommendation note (not a decision)

Lean **Option 1b**, phased so the cost is paid incrementally:

| Phase | Scope | Risk |
|---|---|---|
| **v0** | Lift-and-shift middle-core `modelgen` into the new container unchanged. Same YAML in, same C# out. Doctor proves byte-identical output vs current generated files. *(Done on hub in PR #295 against a frozen golden; relocates to the standalone repo.)* | Low — pure relocation. |
| **v1** | Add ontology input adapters (backend-core HTTP / file / blob). Webhook trigger from backend-core. CLI / MCP-control-plane on-demand. Still C#-only emit. | Medium — new contract on backend-core (see Open Questions). |
| **v2** | Add TypeScript emitter (frontend-core types) + Python emitter (backend-core Pydantic models). Multi-language smoke-compile inside the container. | Medium — multi-toolchain image, version-pinning discipline. |
| **v2.5** | **Repo extraction + delivery seam.** Move forge source into `nickpclarke/agentarmy-forge`; its CI runs the golden + smoke-compile loop. Replace direct-to-main PRs with publish-a-versioned-artifact, and stand up flag-gated adoption in each consumer spoke (`feature-flag-engineer`). | Medium — cross-repo coordination + delivery-mechanism choice (Open Question 6). |
| **v3** *(deferred, may never)* | Binary builds / artifact publishing / deployment orchestration. **Default = don't.** Only revisit if cross-language version coherence requires a single build-time chokepoint. | High — swallows existing owners' responsibilities. |

Avoid **Option 1** (hub-hosted, direct-PR) — it couples the generation loop to the hub's full CI gate set and forces forge to hold write access to every spoke; the iterate-until-compiles loop and the rollout-control loop both get slower and riskier than the split buys.

Avoid **Option 2** — it violates D2 (no scale-curve / release-cadence separation) and forces middle-core's runtime image to ship .NET + Python + Node toolchains it doesn't otherwise need.

Avoid **Option 3** — three generators × one ontology = three places to keep aligned. Drift is inevitable. The whole point of generator-first is *one* source of truth.

Avoid **Option 4** — frontend-core and backend-core already hand-maintain types against the same conceptual model. Every PR there is a contract-drift bug risk.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| (infra) | hub | ADR-029 + contracts.md backlog rows + tiering governance stay here. The v0/v1/v2 seed in `templates/forge-image/` (PR #295) relocates to the standalone repo at v2.5; a thin pointer/README stub may remain |
| forge | nickpclarke/agentarmy-forge *(new)* | Standalone repo home for the generator. Owns the generation loop CI (goldens + multi-target smoke-compile) and publishes versioned generated-source artifacts keyed by `ontology@<sha>` |
| backend-core | nickpclarke/backend-core | New `GET /ontology/snapshot` endpoint (forge upstream); new `POST /ontology/ingest` endpoint (file → SHACL/ShEx shape → validate → Fuseki); two new OpenAPI contracts; webhook emitter on ontology change |
| middle-core | nickpclarke/middle-core | `modelgen` lifted into forge; the in-repo generator code remains until v0 proves byte-identical output, then deleted. Generated `*.g.cs` files keep their existing on-disk locations — only the producer changes. Adopts forge artifacts behind a feature flag (v2.5) |
| frontend-core | nickpclarke/frontend-core | New generated TS types directory (v2); type imports replace hand-maintained types. Adopts forge artifacts behind a feature flag (v2.5) |
| (cross-cutting) | docs/contracts.md | Two new backlog rows (`ontology-snapshot`, `ontology-ingest`) promoted to Registry as endpoints land; a third (`forge-artifact` publish surface) added if the delivery seam needs a contract |

---

## Pros and Cons of the Options

### Option 1 — Extract into `agentarmy-forge` (recommended)

**Pros:**
- D2 clearly cleared on all four split criteria — generator burst vs runtime steady-state, generator cadence ≠ runtime cadence, multi-language toolchain isolation, blast radius confined.
- One generator → many consumers → coherence guaranteed by construction (no per-language drift).
- Ontology-first input aligns with ADR-016/019's chosen knowledge representation.
- File / HTTP / blob input model means forge works in dev (files), prod (HTTP), and archival (blob) without code changes.
- Direct-to-main PR convention matches fleet auto-merge-default culture.

**Cons:**
- Adds a new container to the fleet (operational surface).
- v0 extraction has migration cost — coordinated middle-core PR (delete in-repo generator) + forge PR (host it) need to land together to avoid a generation-gap window.
- Multi-toolchain image (v2) is heavy — .NET SDK + Node + Python all in one Dockerfile is a maintenance commitment.

### Option 2 — Stay inside middle-core

**Pros:** No extraction cost; existing generator-first loop untouched mechanically.

**Cons:** Fails D2 (no tier separation); pollutes middle-core runtime image with .NET + Python + Node toolchains; couples generator release cadence to runtime release cadence.

### Option 3 — Per-spoke generators

**Pros:** Each consumer owns its emit; no central choke-point.

**Cons:** Drift is structural — three implementations of "interpret this ontology" will diverge. Eliminates the single-source-of-truth property that makes generator-first valuable.

### Option 4 — Status quo

**Pros:** Zero cost today.

**Cons:** Frontend-core and backend-core continue hand-maintaining types against the conceptual model — contract drift is inevitable; ontology investment (ADR-016/019) has no consumer.

---

## Open Questions

1. **Webhook security between backend-core and forge.** HMAC signature (lifted from `agentarmy-hmac-verify`, just merged in PR #288)? Or JWT introspection via `agentarmy-jwt-introspect` (PR #287)? Lean HMAC — webhook payloads are small and the secret is shared bilaterally; JWT is overkill for service-to-service notifications.
2. **Snapshot determinism.** Does `GET /ontology/snapshot` return a deterministic serialization (canonical N-Triples sort) for caching? Forge needs an etag / content-hash to short-circuit re-generation when the ontology hasn't changed. Probably yes — punt to the contract design issue.
3. **Generated-file location convention.** Does forge own a top-level `generated/` directory per spoke, or does each generated file live next to its consumer? Lean per-spoke `generated/` dir — easy to gitignore patterns, easy to grep "what does forge produce here?"
4. **PR titling convention.** `chore(generated): forge sync — ontology@<sha>`? Need to be greppable + auto-mergeable but distinguishable from human PRs in PR history.
5. **What happens when the ontology shrinks?** If an object type is removed from the ontology, forge has to delete the corresponding `.g.cs` / `.g.ts` / `.g.py` — that's a destructive PR. Acceptable, but the doctor / consumer CI must catch downstream callers of the removed type before merge.
6. **Delivery seam — publish + adopt mechanism (Option 1b).** What is the artifact and how does a spoke pin + adopt it? Candidates: (a) tagged GitHub release per spoke with generated source attached; (b) language-native packages (NuGet for C#, npm for TS, PyPI/index for Python); (c) a generated-contracts branch/repo each spoke vendors. And which flag system gates adoption — `feature-flag-engineer`'s existing setup, or a simple pinned-version env var per spoke? The publish side may itself need a `forge-artifact` contract row. Pick the smallest mechanism that gives independent per-spoke rollout + one-flip rollback before building v2.5.
7. **Upstream of forge — data → ontology pipeline (out of scope here, but adjacent).** Forge assumes a validated ontology already exists. *Producing* that ontology from structured (DB rows, CSV, OpenAPI) and unstructured (docs, prose, transcripts) sources is a separate, larger problem — ingestion → extraction/lifting → identity resolution → SHACL/ShEx shape validation → Fuseki population. That belongs to the knowledge/ontology + data-engineering clusters (`dlt-engineer` / `data-engineer` ingestion → `knowledge-engineer` population → `ontologist-ufo`/`ontologist-bfo` shaping), and likely warrants its own ADR. `POST /ontology/ingest` (above) is only the file-drop entry point, not the full pipeline.

---

## Related Decisions

- **[ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md):** Container tiering — forge is a function-tier image per the split-rule discipline.
- **[ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md):** Reification + hyperedges — defines the shape of what forge consumes.
- **[ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md):** Ontology reasoning layer (Fuseki + gUFO) — backend-core's RDF store that forge reads from.
- **[ARC-ADR-027](ARC-ADR-027-contract-backlog-discipline.md):** Contract backlog discipline — the two new ontology contracts go in the backlog section first, promote to Registry when shipped.
- **[ARC-ADR-005](ARC-ADR-005-backend-core-openapi-contract.md):** Backend-core OpenAPI contract — the new `/ontology/snapshot` and `/ontology/ingest` endpoints extend that surface.
- **RT7 MCR-F4** — the existing generator that v0 lifts unchanged.
- **PR #287, #288** (recent fn-tier merges) — `jwt-introspect-image` and `hmac-verify-image` are candidate webhook-auth primitives for the backend-core → forge notification path.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-27 | Claude Code (assisted) | Initial Proposed stub from interactive design session with hub owner |
| 0.2 | 2026-05-28 | Claude Code (assisted) | Added Option 1b (standalone `agentarmy-forge` repo + generation/delivery decoupling + flag-gated adoption) per hub owner direction; recommendation moved Option 1 → 1b; added v2.5 phase; updated Affected Layers; added Open Questions 6 (delivery seam) and 7 (data→ontology pipeline as adjacent out-of-scope challenge) |
