# ARC-ADR-034 — Fleet Cross-Repo Access + Contract Distribution (ending copy-in vendoring)

| Field | Value |
|---|---|
| ID | ARC-ADR-034 |
| Status | Proposed |
| Date | 2026-05-28 |
| Deciders | Hub owner (Nicky Clarke) — "solve the vending situation once and for all" |
| Supersedes | — |
| Superseded by | — |
| Tags | vendoring, contracts, cross-repo, cloud-agents, pat, github-app, packages, distribution, drift, fleet |

---

## Context and Problem Statement

The fleet is a hub + N spoke repos. Cloud agents (Copilot coding agent, the Claude GitHub App, claude.ai routines) run in **single-repo microVM sandboxes** with a token scoped to that one repo, so they are **blind to sibling repos**. Today the *only* way to deliver hub content — OpenAPI/AsyncAPI contracts, the ontology "discipline box", shared types, agent packs — into a spoke is **copy-in vendoring** (no submodule / symlink / web path survives the sandbox; established in the Labs *spoke-sandbox-linkage* note).

The result is chaos: **N drifting copies** of every shared artifact, the `fleet-heartbeat` perpetually detecting and dispatching "unvendored / stale" sync work, and agents unable to read the source-of-truth they need. **Root cause (hub owner):** the narrow per-repo token scope blinds agents cross-repo, which *forces* vendoring — and the vendoring is what's slowing progress.

**Decision: how does the fleet share contracts + shared artifacts across repos so that the source of truth exists once, agents can see it, and the drift class is eliminated — not just detected?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Single source of truth.** A contract should exist once, not as N copies that drift. |
| D2 | **Agents must *see* the truth.** Cross-repo blindness forces vendoring just to *read* — fix the visibility. |
| D3 | **Build-time presence.** Some artifacts (discipline box, shared types, the OpenAPI a client is generated from) must be physically *present* in the spoke at build time — reading isn't enough. |
| D4 | **Eliminate drift, don't just detect it.** The heartbeat *detects* stale copies; the goal is to remove the drift *class*. |
| D5 | **Trust model.** The fleet is private + trusted-only (Labs *threat-model-no-forks*), so a fleet-wide **read-only** token's marginal blast radius is low. |
| D6 | **Versioning.** Consumers should pin a version, not chase a moving copy. |
| D7 | **Polyglot.** Consumers are TS (frontend), Python (backend/middle), .NET (middle-core). The mechanism can't assume one language. |

---

## Considered Options

### Option 1 — Status quo: copy-in vendoring + heartbeat sync
Keep copying hub files into spokes; the heartbeat detects drift and dispatches sync. **This is the chaos.** Drift-prone, N copies, perpetual sync churn.

### Option 2 — Broaden cloud-agent READ access (fleet-wide read-only token)
Provision agents a token (GitHub App installation token or fine-grained PAT) scoped **read-only across all fleet repos**. Agents read the hub/sibling source-of-truth directly → no vendoring just to *reference*. **Doesn't** solve build-time presence or drift of the copies that must physically exist in a spoke.

### Option 3 — Versioned shared-artifact package
Publish the contracts + discipline box + shared types as a **versioned artifact** (GitHub Packages / a versioned Release). Spokes declare it as a pinned dependency. "Vendoring" becomes `depend on @fleet/contracts@x.y.z`. **Doesn't** by itself give agents general cross-repo *read*.

### Option 4 — **Both 2 + 3 (recommended)**
Broaden read access (kills blind vendoring-for-reference, D2) **and** publish versioned artifacts (kills drift + meets build-time presence, D1/D3/D4/D6). The "once and for all."

---

## Decision Outcome

**Proposed: Option 4.** Two levers, two owners:

1. **Access (operator's lever).** A **GitHub App installation token** (preferred over a long-lived PAT — auto-scoped, rotating) granting cloud agents **read-only** access across the fleet repos. An agent in a spoke can then `gh api` / shallow-clone the hub or a sibling to read the source-of-truth. Vendoring-for-reference ends. (Per D5 the marginal risk is low on a private, trusted fleet.)

2. **Distribution (built here).** Publish the **language-agnostic contract artifacts** — the OpenAPI/AsyncAPI specs, the ontology discipline box (IR JSON-Schema + gUFO/BFO ttls + SHACL shapes), and shared schemas — as **one versioned, cosign-signed OCI artifact** pushed to **GHCR** via **ORAS** (`ghcr.io/nickpclarke/contracts:vX.Y.Z`). Each spoke **pins a version** (or digest) and its existing codegen (forge, the F# projections per [ARC-ADR-033](ARC-ADR-033-fsharp-ontology-compiler-core.md), `openapi` client-gen) generates its *typed* client from the pulled artifact. One source, per-language generation — no hand-copied, drifting files.

   **Distribution mechanism — decided 2026-05-29 (research-backed).** Use **OCI artifacts via ORAS → GHCR**, not a bespoke tarball, per-ecosystem packages, or a schema registry. ORAS is the CNCF standard for shipping *non-image* versioned artifacts (Helm/Notation/Zarf/OpenTofu); it is **format-agnostic**, so the mixed payload — OpenAPI **and** `.ttl`/SHACL/IR-JSON-Schema — rides as one bundle (a `mediaType` per layer), with semver tags + digest pinning + the manifest *for free*, native **cosign keyless** signing (GH-OIDC), and **GHCR reuse** (zero new infra). Rejected: **Apicurio/Buf/Confluent** registries have **no OWL/SHACL/RDF** type (~40% of our artifacts would need a webhook-sidecar hack) + a JVM+DB service; **per-ecosystem npm/PyPI/NuGet** = 3 pipelines + GitHub Packages has no native PyPI; **git submodule** = commit-pinned drift; **GitHub Release tarball** = the bespoke baseline ORAS supersedes. Built as `tools/contracts-package.mjs` (manifest `tools/contracts.bundle.json`; repo-aware gather across hub + spokes → stage → `oras push` → `cosign sign`). The bundle is the producer's *source-of-truth* per contract, replacing today's copies (e.g. `backend-core.openapi.json` duplicated into frontend-core, `agui-stream` in two spokes, `fleet-interface/` vendored 3×).

The `fleet-heartbeat` vendoring check **flips**: from "is this copy stale?" (fuzzy, always-firing) to "is the spoke pinned to the latest `contracts` version?" (a crisp dependency-freshness check). Drift becomes a visible, reviewable version bump, not silent rot.

### Migration (incremental, vendoring stays working until each cutover)

1. Publish the first `contracts vX.Y.Z` release from the hub (the OpenAPI/ttl/JSON-Schema bundle + a manifest of hashes).
2. Cut **one** spoke's vendored copy over to the pinned artifact + generated client; prove its build/tests pass against the pulled artifact.
3. Flip that spoke's heartbeat check to version-freshness; roll to the rest.
4. Retire copy-in vendoring once all consumers are on the package.

### Why a language-agnostic artifact (not N per-ecosystem packages)

The contracts are *specs* (OpenAPI, ttl, JSON-Schema), not code. Publishing **one** versioned spec bundle and letting each spoke's codegen produce its typed client (a) keeps a single source, (b) reuses the codegen the fleet already has (forge's emitters, the F# projections, `openapi` generators), and (c) avoids maintaining parallel npm + PyPI + NuGet publishes of the same thing. This is the same "one IR → many projections" shape as the compiler core — applied to distribution.

---

## Confirmation

- A spoke builds with its client **generated from the pinned `contracts` artifact**, with **no vendored copy** of the spec in its tree.
- The `fleet-heartbeat` "unvendored / stale contract" finding is **replaced** by a dependency-version-freshness finding.
- A cloud agent in a spoke can **read a sibling/hub repo** (e.g. `gh api repos/<owner>/AgentArmy/contents/...`) with the broadened read token.

---

## Pros and Cons of the Options

- **Option 1 (status quo):** + zero new infra. − the drift/chaos we're trying to kill; perpetual sync churn.
- **Option 2 (read access only):** + directly fixes the cause the hub owner named; cheap. − build-time copies still drift.
- **Option 3 (package only):** + kills drift + build-time presence, versioned. − agents still can't read sibling repos generally; needs a publish pipeline.
- **Option 4 (both, recommended):** + solves visibility *and* drift; versioned; reuses existing codegen. − two mechanisms to stand up (one is the operator's token, one is the pipeline).

---

## Open Questions

1. **Registry/format.** A GitHub **Release** asset (spec bundle + hash manifest) vs a generic GitHub Packages artifact. Lean: a tagged Release with the bundle — simplest, native, versioned, no per-ecosystem publish.
2. **Token mechanism.** GitHub **App installation token** (rotating, auto-scoped) vs a fine-grained PAT (manual rotation). Lean: GitHub App.
3. **Pull-at-build vs commit-the-generated-client.** Generate the client into the spoke at build (ephemeral) vs commit it (reviewable diffs). Lean: commit the *generated client* (reviewable, ARC-ADR-029 forge style) but never the raw vendored spec.
4. **Postman mocks** (Contract-first & mock-first) ride the same version — a published `contracts vX` should also refresh the Postman spec + mock.

---

## More Information

- **Labs:** *spoke-sandbox-linkage* (why copy-in is the only path today), *threat-model-no-forks* (private/trusted → low token risk), *Contract Backlog*.
- **[ARC-ADR-027](ARC-ADR-027-contract-backlog-discipline.md):** contract backlog discipline — the registry this distributes.
- **[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md) / [ARC-ADR-033](ARC-ADR-033-fsharp-ontology-compiler-core.md):** the codegen/projections that turn the pinned spec into typed clients.
- **`tools/fleet-heartbeat.mjs`:** the vendoring check that flips to version-freshness.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-28 | Claude Code (assisted) | Initial Proposed — broaden cloud-agent cross-repo read access + publish versioned contract artifacts to end copy-in vendoring; root cause = narrow per-repo token scope (hub owner) |
