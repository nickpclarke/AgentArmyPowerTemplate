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
