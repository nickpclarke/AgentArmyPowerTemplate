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
| **Data API** (`contracts/backend-core.openapi.json`, `agentarmy-platform.openapi.yaml`) | backend-core | frontend-core (copy + generated `src/lib/api/client.ts`); middle-core (CopilotKit tools, UDA) | **shipped** | [ADR-005](decisions/ARC-ADR-005-backend-core-openapi-contract.md) | `contract-provider.yml` (BE) ↔ `contract-consumer.yml` (FE) — Pact-style |
| **Model contracts** (`ProjectionContracts.g.cs`, `StateMachineContracts.g.cs`, `WorkflowContracts.g.cs`) | middle-core (factory) | middle-core runtime | **shipped** (generated) | — | drift gate (`check_drift.py`) |
| **Data-platform contract** (`data-platform-contract.g.json` — `schema_version` + `*Data` fields/types + state enums; `DataPlatformContracts.g.cs`, MCR-F4) | middle-core | **backend-core UDA** (RT6) | **producer shipped** — middle-core #47 (versioned artifact + drift gate + 11 provider conformance tests). Consumer side dormant until backend-core supplies pact expectations (#40/#44) | RT7 + [ADR-005](decisions/ARC-ADR-005-backend-core-openapi-contract.md), [ADR-009](decisions/ARC-ADR-009-canonical-data-model-arrow.md) | provider conformance tests + `check_drift.py --strict` schema-version gate (MC); consumer-pact hook pending backend #40 |
| **JWT-forwarding auth contract** (FE → MC → BE, verified once in BE) | cross-cutting | frontend-core, middle-core, backend-core | **ADR accepted** — contract to wire | [ADR-002](decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md) | _to wire (auth integration test)_ |
| **Agent endpoint** (`/copilotkit`) | middle-core (#22) | frontend-core (#13 runtime route) | **ADRs accepted** — code draft | [ADR-003](decisions/ARC-ADR-003-no-llm-key-in-browser.md), [ADR-004](decisions/ARC-ADR-004-llm-provider-cerebras.md) | _to wire_ |

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
