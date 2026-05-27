# ARC-ADR-027 — Contract Backlog Discipline & Function-Tier Additions

| Field | Value |
|---|---|
| ID | ARC-ADR-027 |
| Status | Accepted |
| Date | 2026-05-27 |
| Deciders | Hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | contracts, registry, backlog, function-tier, container, image-standard, governance |

---

## Context

The fleet's contract registry ([`docs/contracts.md`](../contracts.md)) currently lists **11 shipped or in-flight inter-layer contracts**. The fleet-heartbeat tool ([`tools/fleet-heartbeat.mjs`](../../tools/fleet-heartbeat.mjs)) catches unregistered contracts and missing OTel init, but it can only see what's *already on disk* — it cannot see contracts the team has *agreed to need* but not yet authored.

This creates two visible failure modes:

1. **Latent contracts produce coupling.** Frontend-core has begun design-system work (CopilotKit deps in `package.json`; `app/theme/` seed; issue #71 Figma Code Connect pilot) but no formal design-tokens / component-API / theme contracts. Consumers — the iOS mirror per EPIC #62, future surface area — will couple to whatever frontend-core happens to expose unless the contract surface is published *before* the producer code stabilizes.
2. **Sub-container splits go uncoordinated.** [ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md) introduced the Platform / Application / Function tier rule and named several Function-tier candidates ("LLM gateway, local embedder, HMAC verifier, OTel collector, schema-migration init"), but only one (event-bridge) has been built. Each remaining candidate has been a judgment call from scratch.

A backlog mechanism — published rows the fleet's two armies can dispatch against — would convert both failure modes into routine work.

A complementary observation about the current container layout: backend-core issue #93 collapses Python + Rust into one Application-tier container, which is **the correct direction** under ADR-023 (one Application container per spoke). The user's stated desire for "microservices rapid build/deploy parallelism" is not in tension with #93 — it's a Function-tier observation. The two operate at different tiers and should not be conflated.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Make anticipated contracts a first-class artifact.** The registry should be readable as both "what we ship" and "what we know we'll need." A separate Backlog section captures the latter without polluting the operational rigor of the former. |
| D2 | **Preserve ADR-023's split discipline.** Every new Function-tier image must clear the split rule (one of: hardware profile, scale curve, release cadence, blast-radius diverges from its host spoke). The Backlog discipline must NOT erode that rule by listing speculative Function-tier images. |
| D3 | **Heartbeat-friendly.** Once a Backlog row is configured (spec + mock + registry promotion to Registry), the heartbeat picks it up automatically. The Backlog itself is text-only; no new automation. |
| D4 | **Two-army dispatch.** Each Backlog row corresponds to a future GitHub issue that goes to the producing spoke under `agent-army-task` (substantial) or `copilot-task` (mechanical). The Backlog is the source-of-truth for the dispatch fan-out. |
| D5 | **Contract-first / mock-first applies to function-tier images too.** A new Function-tier image is *also* a contract producer (its API surface, even if internal). The image scaffold must point at its governing contract row, the same way every Application-tier spoke does. |

## Decision Outcome

### 1. Add a `## Backlog (anticipated contracts)` section to `docs/contracts.md`.

Tight 5-column shape — **Contract · Producer → Consumers · Type · Horizon · Notes** — under five sub-tables organized by layer: design-system / frontend-core, middle-core, backend-core, cross-cutting, upstream vendored.

- **Horizon** ∈ {`near`, `mid`, `later`} signals priority. `near` means *blocking active work this PI*; `mid` means *next PI*; `later` means *research-grade, no commit*.
- **Type** captures the artifact shape: OpenAPI / AsyncAPI / GraphQL / JSON-Schema / TypeScript types / RDF/OWL / SKOS.
- Promotion from Backlog → Registry happens when a contract gains all four of: spec authored, ADR (if cross-cutting), test wired, mock published. That ceremony is what makes the Registry meaningful.

### 2. Add five Function-tier image scaffolds under `templates/*/`.

Each scaffold consists of `image.json` (conforming to [`templates/image-schema.json`](../../templates/image-schema.json)) + `README.md` + `setup.sh` placeholder. No Dockerfile, no scripts — the scaffolds are landing zones, not implementations. Each names its governing Backlog row.

The five chosen for this round, with the ADR-023 split-rule rationale:

| Image | Split-rule pass | Backlog anchor |
|---|---|---|
| `templates/otel-collector-image/` | Independent rollout (config changes ship without rebuilding spokes); different scale curve (telemetry volume ≠ request rate) | XC-2 (OTel trace-context), realizes ADR-024 OTel-init remediation |
| `templates/local-embedder-image/` | Different hardware profile (NPU / iGPU / GPU); different scale curve (embed throughput tracks ingest, not request rate) | BE-4 (Embeddings API), hub #184 |
| `templates/hmac-verify-image/` | Reusable composability (sidecar in front of any spoke that takes signed input); blast-radius isolation (audit security primitives in isolation) | None new — generalizes the verification half of `webhook-receiver.openapi.yaml` (already registered) |
| `templates/schema-migrator-image/` | Different lifecycle (run-to-completion init container vs. long-running app); different ownership (schema-migration-engineer agent) | None new — operationalizes the "init container" pattern named in ADR-023 |
| `templates/jwt-introspect-image/` | Cross-cutting (centralized JWKS caching + leeway); independent rollout (issuer changes ship without spoke rebuilds) | None new — realizes the verify-side of ADR-002 |

### 3. Explicitly **decline** to split today.

For the record, the following splits were considered and rejected as violations of ADR-023's "Don't pre-split" anti-rule:

- **Backend-core into `api / rag / ingest / search-index-builder`** — they deploy together today; none has a divergent scale curve; no evidence of blast-radius gain. Keep as one Application container. Backend-core #93 is the correct direction.
- **Middle-core into `runtime / uda / bridges`** — the generator-first model fights premature splits. Re-evaluate after the UDA exists and shows divergent load.
- **Frontend-core into `web / storybook / token-server`** — Storybook is a build artifact, not a runtime service; design tokens are a static contract, not a server. Don't manufacture services to look more microservice-y.

### 4. Process: a new contract follows the same five-step ritual already documented in `docs/contracts.md`.

The Backlog row IS step 0: documenting that the contract exists as a need. Promotion to Registry happens when steps 1–5 (design → ADR if cross-cutting → enforce → register → evolve) are complete.

## Consequences

**Positive:**

- The fleet's two armies have a published target set to dispatch against — every Backlog row becomes a candidate issue. About 30 issues will be filed in a follow-up dispatch wave.
- New Function-tier images have a documented justification trail. The scaffolds force the split-rule conversation into `image.json` review rather than letting it happen post-hoc.
- Heartbeat coverage improves automatically as Backlog rows promote to Registry.

**Negative:**

- The Backlog can grow stale. Mitigation: each row carries a Horizon, and items at `later` can be deleted without ceremony if they no longer apply. The Backlog is not a commitment.
- More files in `templates/` to maintain. Mitigation: scaffolds are intentionally minimal — `image.json` + README + setup.sh stub — until an implementation issue picks them up.

**Neutral:**

- Backlog rows don't get heartbeat enforcement (the heartbeat sees on-disk artifacts only). That's by design — the Backlog is a *plan*, not an *invariant*.

## Related

- [ARC-ADR-023 — Fleet Container Tiering Strategy](ARC-ADR-023-container-tiering-strategy.md) — the split rule this ADR honors.
- [ARC-ADR-024 — Platform Maturity Audit](ARC-ADR-024-platform-maturity-audit.md) — the OTel-init remediation track that the otel-collector scaffold serves.
- [ARC-ADR-002 — JWT Forwarding Auth Contract](ARC-ADR-002-jwt-forwarding-auth-contract.md) — the contract jwt-introspect-image realizes.
- [ARC-ADR-021 — LLM Gateway](ARC-ADR-021-llm-gateway.md) — the existing Function-tier precedent.
- [`docs/contracts.md`](../contracts.md) — the registry this ADR extends.
- [`templates/image-schema.json`](../../templates/image-schema.json) — the JSON Schema every new `image.json` conforms to.
