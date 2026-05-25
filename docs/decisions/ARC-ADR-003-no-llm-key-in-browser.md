# ARC-ADR-003 — No LLM Key in the Browser (CopilotKit Empty Adapter Security Boundary)

| Field | Value |
|---|---|
| ID | ARC-ADR-003 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | security, copilotkit, frontend-core, llm, browser, empty-adapter |

---

## Context and Problem Statement

CopilotKit's Next.js integration supports multiple runtime adapter configurations. The `CopilotRuntime` can be configured with a direct LLM adapter (e.g., `OpenAIAdapter`, `AnthropicAdapter`) that calls an LLM provider directly from the Next.js API route — requiring that the LLM API key be present in the Next.js server environment or, worse, embedded in the browser bundle if the route is misconfigured.

For the AgentArmy CopilotKit initiative, the LLM (Cerebras) runs exclusively in **middle-core** (a separate Python FastAPI service). The Next.js runtime route in frontend-core serves only as a thin proxy — it should never hold or forward an LLM API key.

The decision to be made is: **which CopilotKit adapter configuration must be used in frontend-core, and how is the no-LLM-key constraint enforced?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | LLM API keys (Cerebras) must never appear in the browser, in Next.js bundle analysis, or in any frontend-core environment variable. |
| D2 | The CopilotKit provider in frontend-core must route all LLM inference to middle-core — no direct LLM calls from the Next.js tier. |
| D3 | The constraint must be enforceable in CI (bundle analysis, environment variable audit) — not just a convention. |
| D4 | The configuration must be compatible with CopilotKit's standard App Router integration pattern. |

---

## Considered Options

1. **`ExperimentalEmptyAdapter` + `remoteEndpoints` pointing at middle-core** (proposed) — frontend-core uses CopilotKit's no-op adapter; all inference is handled by the remote middle-core endpoint.
2. **Direct LLM adapter in frontend-core** — frontend-core configures `OpenAIAdapter` or `AnthropicAdapter` with the Cerebras OpenAI-compatible base URL; middle-core is bypassed.
3. **Shared Next.js + Python runtime via LangChain.js** — collapse middle-core into a Next.js API route using LangChain.js; no separate Python service.

---

## Decision Outcome

**To be decided.** The Architecture Review recommends Option 1 as the only option consistent with the four-layer architecture decision (middle-core holds the LLM key; frontend-core holds only the user JWT).

### Proposed decision: Option 1 — ExperimentalEmptyAdapter + remoteEndpoints

- `app/api/copilotkit/route.ts` uses `CopilotRuntime({ remoteEndpoints: [{ url: process.env.MIDDLE_CORE_URL + '/copilotkit' }] })` with `ExperimentalEmptyAdapter`.
- `MIDDLE_CORE_URL` is the only new environment variable in frontend-core for this feature.
- No LLM API key environment variable (`CEREBRAS_API_KEY`, `OPENAI_API_KEY`, etc.) is present in frontend-core's `.env` or CI secrets.
- CI bundle analysis (or a grep of the built output) confirms no LLM key pattern appears in any JS bundle.

### Confirmation criteria

- `grep -r "CEREBRAS\|sk-\|llm.*key" .next/` returns no matches after build.
- No LLM API key appears in `process.env` at the Next.js API route level.
- The CopilotKit provider successfully routes inference to middle-core using only `MIDDLE_CORE_URL`.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| frontend-core | nickpclarke/frontend-core | Must use `ExperimentalEmptyAdapter`; must not add any LLM key to env; issues #12, #13 |
| middle-core | nickpclarke/middle-core | Holds `CEREBRAS_API_KEY`; exposes `/copilotkit` as the remote endpoint; issue #17 |
| backend-core | nickpclarke/backend-core | No impact |

---

## Pros and Cons of the Options

### Option 1 — ExperimentalEmptyAdapter (proposed)

**Pros:**
- No LLM key in frontend-core by construction — the adapter has no LLM call capability.
- Consistent with the four-layer architectural decision (LLM lives in middle-core).
- Auditable: bundle analysis and env audit are trivial checks.

**Cons:**
- `ExperimentalEmptyAdapter` is marked experimental — API may change in future CopilotKit versions; requires a version pin and upgrade tracking.
- If middle-core is unavailable, the copilot is completely non-functional (no graceful degradation to a browser-side LLM).

### Option 2 — Direct LLM adapter in frontend-core

**Pros:** Simpler deployment (one fewer service).

**Cons:**
- LLM API key must be present in frontend-core environment — violates D1.
- Collapses the security boundary between the presentation tier and the AI tier.
- Bypasses middle-core, making tool-calling and LangGraph agent logic impossible.

### Option 3 — Collapse middle-core into Next.js

**Pros:** Single deployment artifact.

**Cons:**
- LLM key in Next.js environment — violates D1.
- Requires LangGraph + LangChain.js (JavaScript port) — different ecosystem, different testing story.
- Violates the four-layer architecture decision made with the user.

---

## Positive Consequences (if Option 1 accepted)

- LLM key surface area is minimized to the middle-core service (one secret, one location).
- Frontend-core can be deployed as a fully public Next.js app without LLM key rotation risk.

## Negative Consequences (if Option 1 accepted)

- `ExperimentalEmptyAdapter` API stability must be monitored across CopilotKit upgrades.
- middle-core availability is a hard dependency for any copilot functionality.

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding auth contract — the companion security decision (user credential handling).
- **ARC-ADR-004:** LLM provider = Cerebras — governs which LLM key middle-core holds.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | Scrum Master (hub decomposition) | Initial proposed ADR stub |
