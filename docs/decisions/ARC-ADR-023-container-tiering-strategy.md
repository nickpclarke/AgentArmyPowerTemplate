# ARC-ADR-023 — Fleet Container Tiering Strategy

| Field | Value |
|---|---|
| ID | ARC-ADR-023 |
| Status | Accepted |
| Date | 2026-05-26 |
| Deciders | Hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | containers, deploy, architecture, image-standard, microservices, sidecar, init |

---

## Context

The fleet has accumulated containerized pieces without a written rule for **what
belongs in one container vs. another**:

- The hub's `templates/*-image/` directory holds prebuilt platform images
  (ArcadeDB, Fuseki, event-bridge).
- `templates/local-stack/` ([PR #210](https://github.com/nickpclarke/AgentArmy/pull/210))
  now composes those plus Postgres and NATS into one platform up-stack.
- `backend-core/image.json` is a *multi-service* manifest bundling
  backend-core + Postgres + ArcadeDB into a "fusion image" (despite the
  `image.json` name implying one container).
- Open issue `backend-core#93` proposes **collapsing** backend-core into one
  monolithic Python+Rust image — the opposite direction of separation.
- A future micro-service (local embedder per hub #184; LLM gateway per
  [ARC-ADR-021](ARC-ADR-021-llm-gateway.md)) and several sidecar candidates
  (HMAC verifier, OTel collector, schema-migration init) are emerging
  without a placement rule.

Without a tiering rule, each new container is a one-off judgement call:
some end up bundled (slowing deploys), some end up over-split (taxing the
small team with distributed-system coordination it doesn't need yet).

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Independent deploy & failure** — a container is the unit of *independent rollout and isolated failure*. Pieces with linked lifecycles belong together. |
| D2 | **State boundaries** — anything that owns data on disk needs slow, careful upgrades; mixing it with fast-rolling app code is bad. |
| D3 | **Small-team cost of microservices** — distributed tracing, deploy coordination, schema versioning across N services has a real ongoing cost. A 1–2 person team eats it twice. |
| D4 | **Conformance to the Image Standard** — `image.json` is one container's manifest. Multi-service manifests collide with that meaning. |
| D5 | **Granular rollout where it matters** — features whose hardware/scaling/release cadence diverge from their spoke deserve their own container; features that don't, don't. |
| D6 | **Reuse patterns over re-inventing them** — sidecar, init container, and DinD are existing Kubernetes/Compose patterns; this ADR adopts them rather than inventing local equivalents. |

## Decision Outcome

**Three runtime tiers + two composition patterns.** Every container in the
fleet must answer "which tier am I?" — and that answer determines its
lifecycle expectations, manifest shape, and rollout cadence.

### The three tiers

| Tier | Lifecycle | What's in it | Examples (current) | Manifest |
|---|---|---|---|---|
| **Platform** | Slow (days–months); careful upgrades; **has state** | Databases, brokers, ontology stores, persistent caches | ArcadeDB, Postgres, NATS, Fuseki | Hub `templates/*-image/image.json` + composed via `templates/local-stack/docker-compose.yml` |
| **Application** | Medium (hours–days); rolling deploys; **stateless** | Each spoke's main service image | backend-core, middle-core, frontend-core | Spoke-root `image.json` (one container only) |
| **Function** | Fast (minutes); **independently rolled out**; stateless or run-to-completion | Single-purpose workers, sidecars, one-shots, future micros | event-bridge (live); LLM gateway (planned, [ADR-021](ARC-ADR-021-llm-gateway.md)); local embedder (#184) | Per-function `image.json` inside the owning spoke or as a hub template |

**Rule of thumb:** *Two pieces belong in the same container iff (a) they always deploy
together AND (b) one failing must take the other down anyway.* Otherwise
split them.

### Composition patterns (not new tiers)

| Pattern | When | Concrete fleet use |
|---|---|---|
| **Sidecar** (companion container, same network namespace) | Cross-cutting concern that shouldn't pollute the app — proxies, auth, telemetry | HMAC-verification sidecar in front of backend-core; OpenTelemetry collector per spoke (sets up [ADR-010](ARC-ADR-010-observability-standard.md)) |
| **Init container** (run-to-completion before main) | Pre-start work: migrations, schema seeds, secret fetch | Postgres schema migration before backend-core starts; ArcadeDB schema bootstrap |
| **Docker-in-Docker / nested** | Container's *job* is running other containers | The `aca-github-runner` + `docker-local` pool. **Don't use this anywhere else.** |

### Anti-rules

- **Don't pre-split.** A spoke should not be 12 micro-containers on day one.
  Inside a spoke, feature flags and internal modules beat micro-containers
  until something pulls a feature into its own tier (different hardware,
  different scale curve, different release cadence).
- **Don't bundle tiers.** A spoke's `image.json` must describe only the
  spoke's own application container. Platform databases live in the
  platform tier; deferring to `templates/local-stack/` for dev or to
  separate IaC for prod.
- **Don't put state in the application or function tiers.** If a function
  needs persistence, it depends on a platform container.

## Where each existing piece lands

| Piece | Tier | Notes |
|---|---|---|
| ArcadeDB | Platform | Existing `templates/arcadedb-image/` |
| Postgres | Platform | Stock image, composed into `local-stack` |
| NATS JetStream | Platform | Stock image, composed into `local-stack` |
| Fuseki | Platform | Existing `templates/fuseki-ontology-image/` |
| event-bridge | Function | Already micro; reference pattern |
| backend-core | Application | One container (FastAPI + DBOS lib + any Rust extensions). **Will be reshaped by follow-up (b).** |
| middle-core | Application | One container per spoke |
| frontend-core | Application | One container per spoke |
| LLM gateway | Function (planned) | Currently inside backend-core per [ADR-021](ARC-ADR-021-llm-gateway.md); extraction tracked in follow-up (c). Same repo ownership, separate runtime. |
| Local embedder | Function (planned) | Hub #184 — different hardware profile (NPU/iGPU), must be its own container |
| HMAC verifier | Sidecar (planned) | Companion to event-bridge or any future ingress receiver |

## Platform Image Ownership (amendment, 2026-05-26)

The tiering above answers *what* a container is. This subsection answers *who
owns it*: which repo builds it, publishes it, deploys it, and rolls upgrades.

**The hub owns all Platform-tier deployables, end-to-end.** That means:

- The **Dockerfile and the `image.json` manifest** live in `templates/*-image/`
  in the hub. Spokes do **NOT** vendor those directories — they consume the
  running platform instance via env (`ARCADEDB_URL`, `POSTGRES_URL`,
  `NATS_URL`, `FUSEKI_URL`).
- The **deploy lane** (Bicep / Terraform / workflows) lives in the hub. Each
  platform image has its `.bicep` + bootstrap under
  `templates/<name>-image/deploy/`, and the **runnable workflow** lives at
  `.github/workflows/<name>-aca-deploy.yml` (or equivalent) in the hub.
- **One instance per environment.** There is one shared dev ArcadeDB, one
  shared dev Postgres, etc. — not one per spoke. The whole fleet writes to
  the same database in dev, the same in staging, the same in prod (separate
  resource groups per env, single platform instance per env).
- The **`scripts/spoke_sync.config.json` does NOT sync `templates/*-image/`**.
  Hub-owned platform manifests stay in the hub; spoke-owned application
  `image.json` files stay in the spoke.

Why centralized over per-spoke platforms:

1. **Cost** — one ArcadeDB / one Postgres in ACA per env, not N (one per spoke).
2. **Single source of truth** — graph data isn't fragmented across N
   database instances each spoke imported into independently.
3. **Slow lifecycle by definition** — Platform tier upgrades are careful;
   doing them in one place beats coordinating N.
4. **Clear blast radius** — when ArcadeDB has a problem, there's one place to
   look + one place to fix.

Spokes still get to choose:

- **For local dev** — run the hub's [`templates/local-stack`](../../templates/local-stack/)
  to bring up the full platform in one `docker compose up`.
- **For CI** — pull the published image (`agentarmy.azurecr.io/agentarmy-arcadedb:<tag>`)
  and point at it via env.
- **For prod** — connect to the hub-deployed ACA instance via env.

The same rule applies to future Platform images (`fuseki-ontology-image`,
`event-bridge-image`, future `postgres-platform-image`, etc.): hub owns the
Dockerfile, deploy lane, and operations; spokes consume via env.

Backend-core issue [#41](https://github.com/nickpclarke/backend-core/issues/41)
("Deploy ArcadeDB to ACA") is closed by this amendment + the hub-side deploy
lane; the work was always cross-spoke, and a spoke is the wrong home for it.

## Consequences

- **+** Every new container has a clear tier question with a clear answer;
  drift across PRs is reduced.
- **+** `backend-core#93` is now answered: collapse to **one application
  container** (good — single spoke image), but **don't bundle platform
  services into it** (the current "fusion" name is misleading). The follow-up
  in (b) operationalizes this.
- **+** The "fusion manifest" pattern in `backend-core/image.json` is
  formally retired in favor of `image.json` (per-container, per spec) +
  spoke-side compose reference to the platform tier.
- **+** Future micros (gateway, embedder) have a placement rule and don't
  re-litigate the question.
- **−** Some pieces (LLM gateway) move from one container to two for the
  same code; net process count rises. Acceptable cost given the rollout-cadence
  + scaling profile gain.
- **−** Discipline overhead: PR reviewers must check "is this in the right
  tier?" — codified in CLAUDE.md.

## Implementation

This ADR is the strategy. Two follow-up PRs operationalize it:

- **(b)** `backend-core/image.json` refactor — strip multi-service to single
  application container; comment on `backend-core#93` redirecting from
  "collapse Python+Rust" (do) to "bundle platform databases" (don't).
- **(c)** LLM gateway extraction — function-tier reference; updates
  [ADR-021](ARC-ADR-021-llm-gateway.md) with the runtime decoupling.

Other ongoing work that should reference this ADR:

- New `image.json` instances must declare their tier in a top-level field
  (schema update — separate PR).
- The fleet-heartbeat should warn on cross-tier bundling (e.g. an
  `image.json` declaring both `databases: [postgres]` and `services: [api]`).
- CLAUDE.md gets a short "container tiering" section pointing here.

## Out of scope / explicit non-goals

- **Kubernetes adoption.** This ADR is platform-neutral. Compose for dev,
  ACA / Cloud Run / Vercel for prod. K8s sidecar/init patterns are reused
  conceptually; we don't require a K8s cluster.
- **Service mesh.** Premature for current scale.
- **API gateway selection.** Tracked separately in the `api-gateway-engineer`
  cluster.

## References

- [ARC-ADR-010 — Observability Standard](ARC-ADR-010-observability-standard.md)
- [ARC-ADR-021 — LLM Gateway in backend-core](ARC-ADR-021-llm-gateway.md)
- [ARC-ADR-022 — Event Bus Bridges](ARC-ADR-022-event-bus-bridges.md)
- [Image Standard](../image-standard.md)
- `templates/local-stack/README.md` — the live platform-tier composition
- backend-core issue [#93](https://github.com/nickpclarke/backend-core/issues/93) — superseded by follow-up (b)
- hub issue [#184](https://github.com/nickpclarke/AgentArmy/issues/184) — local embedder; function tier
