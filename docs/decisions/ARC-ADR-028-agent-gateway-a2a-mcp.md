# ARC-ADR-028 — Agent Gateway (A2A + MCP)

| Field | Value |
|---|---|
| ID | ARC-ADR-028 |
| Status | Accepted (post-hoc — the implementation predates this record) |
| Date | 2026-05-27 |
| Deciders | Hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | agent-gateway, a2a, mcp, contracts, backend-core, integration |

---

## Context

The fleet integrates two external agent protocols and needs **one stable internal surface** that middle-core and frontend-core can codegen and contract-test against, decoupling them from protocol churn in either upstream:

- **A2A (Agent-to-Agent)** — IBM's open protocol with a canonical AgentCard, skills array, and a task lifecycle (`tasks/submit` → `tasks/get` polling).
- **MCP (Model Context Protocol)** — Anthropic's open protocol with a `tools/list` + `tools/call` shape and no native task lifecycle.

`backend-core/contracts/agent-gateway.openapi.yaml` (already shipped) defines this internal surface. Endpoints land under `/a2a/v1/`:

- `GET /a2a/v1/agents` (+ `?tag` / `?kind` filters) — list registered external agents.
- `GET /a2a/v1/agents/{slug}` — discover one agent's skills/tools, with descriptions **scrubbed for tool-card prompt-injection** by the guardrail layer.
- `POST /a2a/v1/agents/{slug}/invoke` — synchronous invocation against a named capability.
- `POST /a2a/v1/agents/{slug}/tasks` — submit a long-running task (returns `202 + Location`). For MCP agents the gateway **emulates** the A2A task lifecycle locally because MCP has no native one.
- `GET /a2a/v1/agents/{slug}/tasks/{task_id}` — poll task status.
- `GET /a2a/v1/tools` — cross-agent flat tool inventory: `{agent}:{capability}` rows; the "give me anything that can search" picker.

The spec's `info.description` originally cited "ARC-ADR-025" as its governing ADR. That number is taken by `ARC-ADR-025-gcp-scope-narrowing.md`. This ADR is the actual decision record.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Unified internal surface across two upstream protocols.** Consumers shouldn't need to know whether an agent is A2A or MCP — the `kind` field is informational, not a routing requirement. |
| D2 | **Vendored-as-a-dedicated-artifact.** Even though the gateway lives in backend-core, the spec is vendored as its own file (not inlined in `backend-core.openapi.json`) so middle-core / frontend-core can codegen + pact-test against the gateway as its own surface, rather than coupling to all of backend-core. |
| D3 | **Guardrail at the description boundary.** Agent and skill descriptions are tool-card injection vectors (a hostile upstream could embed prompt instructions). Descriptions are scrubbed by the guardrail layer before being returned; blocked entries arrive with `description=""` and `blocked=true` so consumers can render them honestly without trusting the upstream text. |
| D4 | **MCP-to-A2A task emulation.** The gateway emulates A2A's task lifecycle for MCP agents (which have no native task model) so consumers get one consistent polling shape regardless of upstream. |
| D5 | **Bearer JWT auth aligned with [ARC-ADR-002](ARC-ADR-002-jwt-forwarding-auth-contract.md).** The gateway forwards the user JWT; non-health routes require a role claim. No agent registration secrets leak through the gateway. |

## Decision Outcome

### 1. The vendored gateway spec is the contract surface.

`backend-core/contracts/agent-gateway.openapi.yaml` IS the producer artifact. Consumers (middle-core CopilotKit agent picker; frontend-core agent-listing UI) codegen against it directly and run consumer-pact tests on every PR. The backend-core source-of-truth FastAPI app that emits this spec stays in sync via a producer-conformance test (same machinery used for the data-platform contract per [ARC-ADR-005](ARC-ADR-005-backend-core-openapi-contract.md)).

### 2. Description scrubbing is non-negotiable.

Every agent + skill description returned by `GET /agents/{slug}` and `GET /tools` MUST be scrubbed by the guardrail layer. The scrubbing IS part of the contract — a future consumer reading the YAML doesn't need to know about the upstream, only that the surface is safe to render in a tool-card UI. Blocked entries are returned with empty description + `blocked: true`.

### 3. The `kind` field is informational, not a router.

Consumers MUST NOT branch on `kind: a2a` vs `kind: mcp`. The gateway hides the upstream difference — `POST /invoke` works the same way for both, and the task lifecycle is emulated where needed. Future protocols (e.g. A2A's evolution, OpenAI's assistant protocol) get added as new `kind` values without changing the surface shape.

### 4. The gateway is part of backend-core's application tier.

This is not a function-tier candidate today. Reasons (per [ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md) split rule):

- Same lifecycle as the rest of backend-core (no divergent release cadence).
- Same scale curve (gateway throughput tracks application request rate).
- No hardware-profile divergence.

If/when one of those changes — e.g. agent fan-out warrants its own scale curve, or the guardrail layer needs ML inference — extraction becomes warranted; until then, splitting would violate ADR-023's "don't pre-split" anti-rule.

### 5. Cross-agent tool inventory is a first-class endpoint.

`GET /a2a/v1/tools` exists because the "give me anything that can search" picker is a real consumer need (middle-core CopilotKit + the future agent-army planner both want it). The flat-list shape with `{agent}:{capability}` keys means callers can drive `/invoke` without a second lookup.

## Consequences

**Positive:**

- Middle-core + frontend-core can codegen against one stable surface.
- Adding a new agent protocol means an adapter on the gateway, not a consumer change.
- Description-scrubbing centralizes the prompt-injection defense rather than asking every UI to do it.

**Negative:**

- The gateway is a chokepoint — when it's down, no agent invocation works. Health/readiness probes (XC-1 in backlog) mitigate by making the failure observable; the long-term answer is HA via the same Container Apps revisioning that protects backend-core itself.
- MCP task emulation means MCP calls complete on the first poll but go through the polling shape anyway. Slight inefficiency vs direct invoke; accepted to preserve consumer-side uniformity.

**Neutral:**

- The agent registry (which agents exist + their base URLs) lives elsewhere — out of scope for this ADR. The gateway reads it; defining the registry shape is a separate concern.

## Related

- [`backend-core/contracts/agent-gateway.openapi.yaml`](https://github.com/nickpclarke/backend-core/blob/main/contracts/agent-gateway.openapi.yaml) — the producer artifact this ADR governs.
- [ARC-ADR-002 — JWT Forwarding Auth Contract](ARC-ADR-002-jwt-forwarding-auth-contract.md) — the auth model the gateway uses.
- [ARC-ADR-005 — Backend-core OpenAPI Contract](ARC-ADR-005-backend-core-openapi-contract.md) — establishes producer-conformance testing pattern this gateway adopts.
- [ARC-ADR-023 — Fleet Container Tiering Strategy](ARC-ADR-023-container-tiering-strategy.md) — the rule this ADR honors when keeping the gateway inside backend-core's application container.
- [ARC-ADR-027 — Contract Backlog Discipline](ARC-ADR-027-contract-backlog-discipline.md) — the registry+backlog discipline that surfaced this ADR's absence.
- [`docs/contracts.md`](../contracts.md) — the registry entry pointing here.
