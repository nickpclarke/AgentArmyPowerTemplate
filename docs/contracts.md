# Inter-Layer Contracts (registry)

The **hub owns the inter-layer surface.** Layers integrate **contract-first** — never by
importing each other's private code. This page is the single registry of every contract
between layers: who produces it, who consumes it, whether it's shipped, the ADR that governs
it, and the test that enforces it.

> **Rule:** a producer layer publishes a versioned contract; consumers bind only to that. A
> cross-cutting decision about a contract becomes an [ADR](architecture-decisions.md). The
> contract is enforced by a provider/consumer test, and listed here.

## Registry

| Contract | Producer | Consumers | Status | Governing ADR | Test |
|---|---|---|---|---|---|
| **Data API** (`contracts/backend-core.openapi.json`, `agentarmy-platform.openapi.yaml`) | backend-core | frontend-core (copy + generated `src/lib/api/client.ts`); middle-core (CopilotKit tools, UDA) | **shipped** — Postman mocks live: backend-core (`37e883b2…`), platform (`918365a6…`) | [ADR-005](decisions/ARC-ADR-005-backend-core-openapi-contract.md) | `contract-provider.yml` (BE) ↔ `contract-consumer.yml` (FE) — Pact-style |
| **Model contracts** (`ProjectionContracts.g.cs`, `StateMachineContracts.g.cs`, `WorkflowContracts.g.cs`) | middle-core (factory) | middle-core runtime | **shipped** (generated) | — | drift gate (`check_drift.py`) |
| **Data-platform contract** (`data-platform-contract.g.json` — `schema_version` + `*Data` fields/types + state enums; `DataPlatformContracts.g.cs`, MCR-F4) | middle-core | **backend-core UDA** (RT6) | **producer shipped** — middle-core #47 (versioned artifact + drift gate + 11 provider conformance tests). Consumer side dormant until backend-core supplies pact expectations (#40/#44) | RT7 + [ADR-005](decisions/ARC-ADR-005-backend-core-openapi-contract.md), [ADR-009](decisions/ARC-ADR-009-canonical-data-model-arrow.md) | provider conformance tests + `check_drift.py --strict` schema-version gate (MC); consumer-pact hook pending backend #40 |
| **JWT-forwarding auth contract** (FE → MC → BE, verified once in BE) | cross-cutting | frontend-core, middle-core, backend-core | **ADR accepted** — contract to wire | [ADR-002](decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md) | _to wire (auth integration test)_ |
| **Agent endpoint** (`/copilotkit`) | middle-core (#22) | frontend-core (#13 runtime route) | **ADRs accepted** — code draft | [ADR-003](decisions/ARC-ADR-003-no-llm-key-in-browser.md), [ADR-004](decisions/ARC-ADR-004-llm-provider-cerebras.md) | _to wire_ |
| **MCR-F4 projection-read API** (`mcr-f4-projection.openapi.yaml`) | middle-core (`contracts/proposed/`, #62) | backend-core UDA `ProjectionCapable` (Phase 2) | **producer shipped** — spec + mock (`de0aa40f…`); consumer pending **backend-core #76** | [ADR-005](decisions/ARC-ADR-005-backend-core-openapi-contract.md), [ADR-009](decisions/ARC-ADR-009-canonical-data-model-arrow.md), [ADR-016](decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) | _to wire (connector, #76)_ |
| **Frontend BFF** (browser↔UI, `frontend-bff.openapi.json`) | frontend-core (`contract/`, #47) | the browser (generated `openapi-fetch` client) | **shipped** — vendored + spec + mock (`f1ecc977…`); 3 feature-flagged auth schemes (`AUTH_MODE`); client-gen + `/api/cockpit/*` route handlers pending **frontend-core #48** | [ADR-002](decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md) (cookie-in → JWT-out) | _to wire (#48)_ |
| **AG-UI agent stream** (SSE, `agui-stream.asyncapi.yaml`) | middle-core (CopilotKit/LangGraph) | frontend-core (`contract/`, #47) | **contract drafted** (AsyncAPI 3.0 — not Postman-mockable); producer vendor + event-name verify pending **middle-core #66** | [ADR-007](decisions/ARC-ADR-007-agent-streaming-protocol.md) | _doc/governance (SSE)_ |
| **LLM gateway** (OpenAI-compatible, `contracts/llm-gateway.openapi.yaml`) | **backend-core** (gateway + guardrails) | middle-core, frontend-core (browser → BFF → backend; no key in browser) | **proposed** — spec + Postman mock **published** (`173bda37…`, non-stream shape); backend-core impl + guardrail middleware pending | [ADR-021](decisions/ARC-ADR-021-llm-gateway.md), [ADR-003](decisions/ARC-ADR-003-no-llm-key-in-browser.md) | _to wire (provider verification; SSE not mockable)_ |
| **Agent gateway** (A2A + MCP, `backend-core/contracts/agent-gateway.openapi.yaml`) | **backend-core** (gateway, extracted from generated contract) | middle-core (CopilotKit agent picker), frontend-core (agent listing UI) | **producer shipped** — vendored as dedicated artifact so consumers can codegen/contract-test against the gateway as its own surface; consumer codegen + tests pending | [ADR-028](decisions/ARC-ADR-028-agent-gateway-a2a-mcp.md) (spec's stale `info.description` cites "ARC-ADR-025" — backend-core follow-up to re-link in the YAML) | _to wire (consumer pact in MC + FE)_ |
| **Event bus** (NATS JetStream + CloudEvents v1.0) | the fleet (middle-core hosts the broker per its `ARC-ADR-001` / PR #73; bridges per ARC-ADR-022) | any subscriber across spokes (consumer per subject) | **broker live locally** (`nats:2.10-alpine -js`, `localhost:4222`); compose impl in middle-core #74 (`copilot-task`); HTTP↔NATS bridges in proposed `templates/event-bridge-image/` | [ADR-022](decisions/ARC-ADR-022-event-bus-bridges.md) | _to wire (push-consumer + GH-Actions publisher + DLQ)_ |
| **Webhook receiver** (event-bridge inbound, `contracts/webhook-receiver.openapi.yaml`) | hub `templates/event-bridge-image/` (per ARC-ADR-022) | GitHub webhooks → HMAC verify → CloudEvents → NATS `fleet.gh.*` | **proposed** — spec + Postman mock **published** (`27f2561e…`); image doctor 3/3 PASS on a running stack | [ADR-022](decisions/ARC-ADR-022-event-bus-bridges.md) | _doctor (HMAC verify + JetStream replay)_ |

### Upstream contracts (external producers we depend on)

External SaaS we call from inside the fleet earn the same vendoring rigor as
internal contracts: we capture the slice we actually consume, mock it in
Postman so contract-tests don't bill the vendor, and detect upstream drift via
provider verification. Producer here is the *vendor*; consumer is our spoke.

| Contract | Producer | Consumers | Status | Governing ADR | Test |
|---|---|---|---|---|---|
| **Tavily Search & Extract** (`backend-core/contracts/tavily-upstream.openapi.yaml`) | Tavily (external SaaS) | backend-core llm-gateway (`app/llm/providers.py` `_atavily_search` / `_atavily_extract`) | **vendored** — spec captures the slice consumed (POST `/search`, POST `/extract`); Postman mock + provider-verification test pending | [ADR-021](decisions/ARC-ADR-021-llm-gateway.md) | _to wire (provider verification against vendored schema)_ |

## Backlog (anticipated contracts)

Contracts the fleet logically needs but hasn't shipped yet. Each row becomes a dispatched issue against the producing spoke (`agent-army-task` label) so the armies pick them up over time. **Type** = OpenAPI / AsyncAPI / GraphQL / JSON-Schema / TypeScript types / RDF/OWL / SKOS. **Horizon** = near (this PI), mid (next PI), later (research-grade, no commit).

### Design system & frontend-core

| # | Contract | Producer → Consumers | Type | Horizon | Notes |
|---|---|---|---|---|---|
| FE-1 | **Design tokens** (`frontend-core/contract/design-tokens.json`) | frontend-core → every component + iOS mirror | JSON-Schema (W3C DTCG) | **near** | Skeleton + JSON-Schema validation in this PR; populated by FE design-system team |
| FE-2 | **Component API contracts registry** (`frontend-core/contract/components/`) | frontend-core → Figma Code Connect + consumers | TypeScript declarations | **near** | One `<Component>.api.ts` per shipped component. Operationalizes issue #71 |
| FE-3 | **Theme contract** (`frontend-core/contract/theme.json`) | frontend-core → all UIs (web + iOS) | JSON-Schema | mid | Light / dark / branded variants. Builds on FE-1 |
| FE-4 | **Icon set contract** (`frontend-core/contract/icons.json`) | frontend-core → web + iOS + design system | JSON | mid | SVG sprite + name registry |
| FE-5 | **i18n message keys** (`frontend-core/contract/i18n.json`) | frontend-core → consumers + translation pipeline | JSON-Schema | mid | Key registry + locale fallback policy |
| FE-6 | **A11y contract** (ADR-only, no API spec) | cross-cutting (FE primary) | ADR | mid | Keyboard nav, ARIA roles, contrast targets. Governance, not codegen |
| FE-7 | **iOS-shared models** (`frontend-core/contract/ios-shared.openapi.yaml`) | frontend-core → SwiftUI iOS app (EPIC #62) | OpenAPI | later | Type defs consumed by web and SwiftUI together |
| FE-8 | **Figma Code Connect mappings registry** (`frontend-core/.figma/`) | frontend-core (#71) → Figma Dev Mode | `*.figma.tsx` files | **near** | Operationalizes #71; this is the *registry* row for what the pilot creates |

### Middle-core

| # | Contract | Producer → Consumers | Type | Horizon | Notes |
|---|---|---|---|---|---|
| MC-1 | **Tool catalog schema** (`middle-core/contracts/tool-catalog.json`) | middle-core → cloud agents (MCP-style discovery) | JSON-Schema | mid | Today lives in `_meta.tools` ad-hoc; formalize for cross-agent discovery |
| MC-2 | **Agent capability/health** (`middle-core/contracts/agent-capability.openapi.yaml`) | middle-core → frontend agent picker | OpenAPI | mid | What an agent advertises (capabilities, readiness, model identity) |
| MC-3 | **NATS subject taxonomy** (`middle-core/contracts/nats-subjects.json`) | the fleet → any subscriber | JSON | **near** | Naming convention + payload schemas for `fleet.*` subjects (per ADR-022) |
| MC-4 | **Model-spec contract** (`middle-core/contracts/model-spec.schema.json`) | middle-core (factory) → factory consumers | JSON-Schema | mid | Schema of the source-of-truth model file the generator reads |
| MC-5 | **Generator-output schema** (`middle-core/contracts/generator-output.schema.json`) | middle-core (factory) → consumer codegen tools | JSON-Schema | mid | Shape of every `*.g.*` artifact the factory emits |

### Backend-core

| # | Contract | Producer → Consumers | Type | Horizon | Notes |
|---|---|---|---|---|---|
| BE-1 | **LLM gateway SSE stream** (extend `contracts/llm-gateway.openapi.yaml`) | backend-core → middle-core + frontend BFF | OpenAPI (text/event-stream) | **near** | Add SSE event shape; provider-verification only (SSE isn't Postman-mockable) |
| BE-2 | **RBAC policy contract** (`backend-core/contracts/rbac.json`) | backend-core → all consumers via JWT claims | JSON | mid | Role → permission mapping; enforced once in BE per ADR-002 |
| BE-3 | **Audit-event contract** (`backend-core/contracts/audit-events.asyncapi.yaml`) | backend-core → NATS subscribers | AsyncAPI | mid | What BE emits to `fleet.audit.*` subjects |
| BE-4 | **Embeddings API** (`backend-core/contracts/embeddings.openapi.yaml`) | backend-core (or local-embedder fn-tier) → consumers | OpenAPI | mid | Vector dim, model name, retrieval params. Pairs with local-embedder image (#184) |
| BE-5 | **Ingest contract clarification** (extend `backend-core.openapi.json`) | backend-core → middle-core agents | OpenAPI | **near** | Resolves MC#44 (URI-ingest vs multipart). Decision artifact needed first |
| BE-6 | **Pagination contract** (`contracts/pagination.openapi.yaml`) | cross-cutting | OpenAPI | mid | Cursor vs offset, page-size limits; referenced by every list endpoint |
| BE-7 | **Ontology snapshot read API** (`backend-core/contracts/ontology-snapshot.openapi.yaml`) | backend-core (Fuseki-backed) → `agentarmy-forge` | OpenAPI | **near** | `GET /ontology/snapshot?version=…` returning deterministic RDF (Turtle / JSON-LD / N-Triples) with etag/version headers so forge can short-circuit re-gen. Governed by [ADR-029](decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md); upstream consumer of [ADR-019](decisions/ARC-ADR-019-ontology-reasoning-layer.md) Fuseki store |
| BE-8 | **Ontology ingest API** (`backend-core/contracts/ontology-ingest.openapi.yaml`) | backend-core → operators + agents | OpenAPI (multipart + JSON) | **near** | `POST /ontology/ingest` — accept RDF file → SHACL/ShEx shape validation → write to Fuseki + emit `fleet.ontology.changed` event (forge webhook fires off this). Completes the ingest → store → snapshot → generate loop. **Input seam decided 2026-05-28: BE-8 accepts BOTH multipart file upload AND JSON `{uri}` by-reference (resolves #44 / #61).** Governed by [ADR-029](decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md), [ADR-019](decisions/ARC-ADR-019-ontology-reasoning-layer.md) |

### Cross-cutting

| # | Contract | Producer → Consumers | Type | Horizon | Notes |
|---|---|---|---|---|---|
| XC-1 | **Health / readiness** (`contracts/health.openapi.yaml`) | every spoke → orchestrator + LB + probes | OpenAPI | **near** | Standard `/healthz` `/readyz` `/livez` shape. Authored in this PR |
| XC-2 | **OTel trace-context** (ADR formalization) | every spoke → OTel collector sidecar | ADR + W3C trace-context | **near** | Formalizes ADR-010/ADR-024; OTel collector function-tier image scaffolded in this PR |
| XC-3 | **Error envelope** (`contracts/problem-details.openapi.yaml`) | every spoke → every consumer | OpenAPI (RFC 7807) | **near** | Authored in this PR; referenced by every other spec via $ref |
| XC-4 | **Rate-limiting** (`contracts/rate-limit.openapi.yaml`) | api-gateway-engineer → every spoke | OpenAPI | mid | `X-RateLimit-*` headers + 429 problem-details shape |
| XC-5 | **CI workflow signatures** (`contracts/ci-workflows.schema.json`) | hub `.github/workflows/_*.yml` → spoke callers | JSON-Schema for `workflow_call` | mid | What inputs/outputs reusable workflows expect |
| XC-6 | **Booster pack** (per docs PR #190) | hub → spoke installers | JSON | later | Booster-pack manifest format |
| XC-7 | **MCP server contract pattern** (generalize untool fleet) | hub → any spoke MCP server | OpenAPI + MCP discovery | mid | Reusable MCP-server scaffold derived from `tools/mcp-local-fleet/` |
| XC-8 | **Image-standard schema** (`templates/image-schema.json`) | hub → every image author | JSON-Schema | **near** | Already exists; just *register* it as a contract |
| XC-9 | **Spoke-layer manifest** (`templates/spoke-layer-manifest.example.json`) | hub → every spoke | JSON-Schema | mid | Spoke-level manifest format; schema not yet published |
| XC-10 | **Business-object catalog** (`templates/business-object-catalog.example.json`) | producing spoke → consumer spokes | JSON | later | Shared business-object registry (existing example, no schema yet) |
| XC-11 | **Forge control API** (`contracts/forge-control.openapi.yaml`) | hub `templates/forge-image/` → backend-core (webhook source), operators (on-demand) | OpenAPI | **producer-shipped** | `POST /webhook` (HMAC `X-Hub-Signature-256`), `POST /generate` (on-demand `{source, target, out, consumer_repo, branch, if_none_match}`), `GET /healthz`. Endpoints shipped in PR #295; OpenAPI spec landed; **spec + Postman mock live** (`66487fcc…`). Governed by [ADR-029](decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md) |

### Upstream vendored

| # | Contract | Producer → Consumers | Type | Horizon | Notes |
|---|---|---|---|---|---|
| UP-1 | **OpenAI** (`backend-core/contracts/openai-upstream.openapi.yaml`) | OpenAI (SaaS) → backend-core llm-gateway | OpenAPI (vendored slice) | mid | Capture only the endpoints used; mock in Postman; provider-verification |
| UP-2 | **Anthropic** (`backend-core/contracts/anthropic-upstream.openapi.yaml`) | Anthropic (SaaS) → backend-core llm-gateway | OpenAPI (vendored slice) | mid | Same pattern as Tavily/UP-1 |
| UP-3 | **Cerebras** (`backend-core/contracts/cerebras-upstream.openapi.yaml`) | Cerebras (SaaS) → backend-core llm-gateway | OpenAPI (vendored slice) | mid | Per ADR-004 |
| UP-4 | **GitHub REST/GraphQL** (`hub/contracts/github-upstream.openapi.yaml`) | GitHub (SaaS) → claude.yml + hub automations | OpenAPI (vendored slice) | later | Capture only what claude.yml + heartbeat actually use |
| UP-5 | **ArcadeDB management API** (`hub/contracts/arcadedb-upstream.openapi.yaml`) | ArcadeDB → hub provisioning | OpenAPI (vendored slice) | later | The mgmt surface for the platform-tier ArcadeDB image |
| UP-6 | **Cloudflare Zero Trust Access** (`hub/contracts/cloudflare-access-upstream.openapi.yaml`) | Cloudflare → hub MCP-fleet provisioning | OpenAPI (vendored slice) | later | The slice used by `tools/mcp-local-fleet/AUTOMATION.md` for app + service-token provisioning |

## Who's waiting on whom

- **backend-core UDA (RT6) ← middle-core (MCR-F4):** producer contract **shipped** (middle-core #47 —
  versioned `data-platform-contract.g.json` + drift gate + provider conformance tests). The wait is
  now on **backend-core**: bind the UDA to it (#40) and supply consumer pact expectations
  (`PACT_FILE`/`PACT_BROKER_URL`) so MC's dormant consumer-pact hook activates.
- **Ingest contract gap (MC agent ↔ backend-core `/api/v1/ingest`):** middle-core #44 found the
  agent assumed JSON `{uri}` ingest but backend-core's endpoint is **multipart file upload**. Open
  cross-layer decision (URI-ingest endpoint vs agent file-upload flow) — see the governing ADR/issue.
- **CopilotKit middle-core runtime → backend-core OpenAPI:** the contract is **already shipped**,
  so middle-core's tools aren't blocked on it — only on their own draft code (#18–#22).
- **Auth (ADR-002): settled — accepted 2026-05-25.** Forward the user JWT unchanged across all
  three hops; RBAC enforced once in backend-core. Wire the auth integration test as the
  FE→MC→BE chain is built.

## Drift management

frontend-core holds a **copy** of `backend-core.openapi.json` (currently in sync, byte-for-byte).
The Pact-style `contract-provider`/`contract-consumer` tests catch behavioral drift; the file
copy should be re-pulled from the backend-core source on each change (or generated in CI) so it
can't silently age. **middle-core is not yet in the contract-test loop** — wire a consumer test
(against backend's OpenAPI) and a provider verification (for MCR-F4) when that code lands.

## How to add or change a contract

1. **Design** with `api-designer` (the spec: OpenAPI / GraphQL / AsyncAPI / shared types).
2. If it's a **cross-cutting decision**, write an [ADR](architecture-decisions.md) (`/ea-adr`).
3. **Enforce** with `contract-test-engineer` — a provider verification in the producer repo + a
   consumer test in each consumer repo.
4. **Register** it in the table above (producer, consumers, status, ADR, test).
5. Evolve it safely with `schema-migration-engineer` (versioned, backward-compatible).

The hub owns this registry + the governing ADRs; the producing/consuming spokes own their side
of each contract and its tests.

## Vendoring external upstream contracts

When a spoke calls an external SaaS (Tavily, OpenAI, Anthropic, etc.) treat it
as a contract too — same vendoring rigor as internal layers:

1. **Capture the slice you consume** in `<spoke>/contracts/<vendor>-upstream.openapi.yaml`.
   Do NOT vendor the vendor's entire API — only the endpoints and fields you
   actually send/read today. A future feature that needs more extends the spec
   first, then the code.
2. **Mock it in Postman** (AgentArmy workspace) so contract tests can run
   without billing the vendor or needing a live key.
3. **Register it under "Upstream contracts"** above — producer is the vendor,
   consumer is your spoke.
4. **Add a provider-verification test** — periodically validate that the live
   upstream still matches the vendored schema. When it drifts, the test fails
   *before* the field starts mattering in production.

Why bother: when a vendor silently changes a response field, the only place
that breaks is the live integration — usually noticed by users, not engineers.
A vendored contract turns that into a CI signal, and makes the dependency
surface visible to anyone reading the registry.
