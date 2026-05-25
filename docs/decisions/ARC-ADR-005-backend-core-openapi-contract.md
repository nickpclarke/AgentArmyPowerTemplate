# ARC-ADR-005 — backend-core OpenAPI Contract Consumed by middle-core Tools (Contract-First; Generated Client)

| Field | Value |
|---|---|
| ID | ARC-ADR-005 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review |
| Supersedes | — |
| Superseded by | — |
| Tags | api, openapi, contract-first, middle-core, backend-core, generated-client |

---

## Context and Problem Statement

middle-core's `tools.py` contains seven LangGraph tools that call backend-core's `/api/v1/*` REST endpoints. Each tool must serialize request bodies, deserialize response payloads, and handle error codes correctly. Two implementation approaches are possible:

1. Hand-write the HTTP calls in `backend_client.py` using `httpx` with manually maintained request/response types.
2. Generate a typed Python client from `contracts/backend-core.openapi.json` (which is already maintained by backend-core and CI-drift-checked).

The decision to be made is: **should middle-core generate a typed client from the backend-core OpenAPI contract, or maintain hand-written HTTP calls?**

This decision also governs the contract stability guarantee: if middle-core depends on the OpenAPI spec, then backend-core must treat `contracts/backend-core.openapi.json` as a first-class published artifact — breaking changes require a versioning plan.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | middle-core tools must call backend-core endpoints correctly — type-safe request/response handling reduces integration bugs. |
| D2 | backend-core already maintains `contracts/backend-core.openapi.json` with a CI drift check — this artifact is the single source of truth for the REST contract. |
| D3 | The contract must be stable: middle-core must not silently break when backend-core evolves its API. |
| D4 | The generated client must be regeneratable in CI when the contract changes — not a one-time manual artifact. |
| D5 | The approach must not add unacceptable complexity to backend-core (no new versioning infrastructure if avoidable). |

---

## Considered Options

1. **Generate typed Python client from `contracts/backend-core.openapi.json`** (proposed) — use `openapi-python-client` or `datamodel-code-generator` to produce a typed async client; regenerate in CI on contract change; middle-core imports the generated client.
2. **Hand-written httpx client** — `backend_client.py` manually implements request/response types; no code generation; types maintained by convention.
3. **Shared Python package** — backend-core publishes a Python package containing its request/response types; middle-core depends on the package version.

---

## Decision Outcome

**To be decided.** The Architecture Review recommends Option 1 (generated client) as the contract-first approach consistent with CLAUDE.md's "contract-first everything" principle and the existing CI drift check in backend-core.

### Proposed decision: Option 1 — Generated typed client

- backend-core's `contracts/backend-core.openapi.json` is the **published contract artifact** consumed by middle-core.
- middle-core includes a `make generate-client` (or equivalent) step that runs `openapi-python-client generate --path contracts/backend-core.openapi.json` to produce the typed client in `backend_client/` (generated, gitignored or committed — to be decided by the implementing agent).
- The generated client is the only way middle-core calls backend-core — no ad-hoc `httpx` calls outside the generated client.
- backend-core's CI drift check (`scripts/export_openapi.py`) remains the authoritative gate; if the spec changes, middle-core's CI regenerates and runs tests against the new client.
- JWT injection: the generated client is wrapped with a thin `BackendClient` adapter that attaches `Authorization: Bearer <jwt>` (the generator does not know about JWT forwarding).

### Confirmation criteria

- `make generate-client` produces a typed async client from the current `contracts/backend-core.openapi.json` without errors.
- middle-core CI regenerates the client on every run (or detects drift) — no stale client in CI.
- All seven tool methods in `tools.py` use the generated client exclusively.
- Changing a backend-core route parameter causes a CI failure in middle-core (contract drift detected).

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | `contracts/backend-core.openapi.json` becomes a published artifact; drift check is already in place; issues #16, #17, #18, #19 |
| middle-core | nickpclarke/middle-core | `backend_client.py` wraps the generated client; CI adds a generation step; issues #17, #19 |
| frontend-core | nickpclarke/frontend-core | No impact |

---

## Pros and Cons of the Options

### Option 1 — Generated typed client (proposed)

**Pros:**
- Contract drift detected at CI time — not at runtime in production.
- Type-safe request/response — fewer integration bugs in `tools.py`.
- Consistent with "contract-first everything" principle in CLAUDE.md.
- Backend-core's existing drift check is the upstream gate; no new tooling required in backend-core.

**Cons:**
- CI setup required in middle-core (generator install, generation step, diff check).
- Generated code style may not match project conventions — requires a review pass after initial generation.
- If the contract changes frequently, middle-core CI will require frequent regeneration — acceptable overhead.

### Option 2 — Hand-written httpx client

**Pros:** No generator dependency; simpler CI.

**Cons:**
- Types diverge from the actual API silently — bugs only caught at runtime or in integration tests.
- Violates "contract-first everything" principle.
- Maintenance burden grows as the API evolves.

### Option 3 — Shared Python package

**Pros:** Strongly typed, versioned contract.

**Cons:**
- Requires package publishing infrastructure (PyPI or private registry).
- Overkill for a two-repo internal dependency.
- backend-core would need to maintain a separate Python types package alongside the FastAPI app.

---

## Positive Consequences (if Option 1 accepted)

- Contract-first discipline enforced mechanically (not by convention).
- middle-core tools are type-safe against backend-core's actual API surface.
- A backend-core breaking change is caught in middle-core CI before it reaches a running environment.

## Negative Consequences (if Option 1 accepted)

- Generator tooling (`openapi-python-client` or equivalent) must be pinned and maintained.
- Generated code is either committed (requires regeneration on every contract change) or gitignored (requires generation at build time — Dockerfile complexity increases).

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding auth contract — the generated client must be wrapped with JWT injection.
- **ARC-ADR-004:** LLM provider = Cerebras — the tools generated from this contract are what the LLM calls.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | Scrum Master (hub decomposition) | Initial proposed ADR stub |
