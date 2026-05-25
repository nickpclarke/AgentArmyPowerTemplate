# RT8 — Generative Platform Maturity: Agent Runtime + Generative UI

Durable Epic plan for taking the `nickpclarke/middle-core` and `nickpclarke/frontend-core` spokes from
working prototypes to a **production-grade generative platform**: streaming agent responses, persistent
conversation memory, a cockpit dashboard, observability, auth/session UX, and deployed runtimes on Azure
Container Apps (middle-core) and Vercel (frontend-core).

> **The spoke-repo boards are the source of truth for status and issue numbers.**
> Issues for this RT live in their respective repos:
> `https://github.com/nickpclarke/middle-core/issues` (MC-#)
> `https://github.com/nickpclarke/frontend-core/issues` (FE-#)
> Stable local IDs (`GPM-*`) below are the durable planning references until board population.

---

## Theme

**Generative Platform Maturity**: close the loop between the Python LangGraph agent runtime (middle-core)
and the Next.js + CopilotKit generative UI (frontend-core) by delivering streaming, memory, observability,
and deployment as a coherent, paired capability increment. Each cross-layer pair ships as a coordinated
Feature set so the platform is testable end-to-end at every stage.

This RT is a **spoke-implementation train** — it delivers running software inside the spoke repos, not
hub template artifacts. Hub RT1–RT4 provide the template scaffolding; RT8 uses it.

---

## Summary

| Epic | Features | Enablers | Spikes | PI | Sequencing |
|---|---|---|---|---|---|
| **GPM-E1** Agent Runtime Maturity (middle-core) | GPM-F1…F5 | GPM-EN1, GPM-EN2 | — | **PI-3 (candidate)** | GPM-F1 (streaming) keystone for FE pairing |
| **GPM-E2** Generative UI Maturity (frontend-core) | GPM-F6…F11 | GPM-EN3 | — | **PI-3 (candidate)** | GPM-F6 (cockpit) + GPM-F7 (streaming render) start concurrently after GPM-F1 |

**Total:** 2 Epics + 11 Features + 3 Enablers = 16 board items across two spokes.
**Session estimate:** ~5–7 sessions (implementation-heavy: streaming plumbing, real-time UI, ACA deploy,
analytics integration). Parallelism opportunity: GPM-F6 through GPM-F9 are largely independent of each
other after GPM-F1 ships; 4 agents can run them concurrently in a single session.

**Live issues:**
- middle-core: `https://github.com/nickpclarke/middle-core/issues` — #32–#39
- frontend-core: `https://github.com/nickpclarke/frontend-core/issues` — #32–#37

---

## Backlog items

> SAFE fields per item: `Type`, `PI`, `Size`, `Estimate` (Fibonacci pts), `Priority`. Definition of Ready =
> these set + acceptance criteria below. Definition of Done = PR merged with `Closes #N`, CI green,
> paired spoke issue referenced where applicable.

---

### GPM-E1 — Epic: Agent Runtime Maturity (middle-core)

- **Type:** Epic · **PI:** PI-3 (candidate) · **Priority:** P1
- **Spoke repo:** `nickpclarke/middle-core`
- **Outcome:** The LangGraph agent runtime streams responses, maintains conversation memory/thread state,
  exposes analytics tooling over the UDA query surface, passes provider contract tests (MCR-F4 seam),
  ships OpenTelemetry + Prometheus instrumentation, wires ArcadeDB persistence via the PIN-F4 adapter,
  extends the ontology with reification and hyperedges, and deploys to Azure Container Apps with a
  production-ready manifest.
- **Children:** GPM-F1, GPM-F2, GPM-F3, GPM-F4, GPM-F5, GPM-EN1, GPM-EN2.

---

### GPM-F1 — Feature: Agent response streaming (middle-core #32) — KEYSTONE

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P0 · **Depends on:** LangGraph runtime
  baseline; **blocks** GPM-F7 (FE streaming render)
- **Scope:** LangGraph streaming mode enabled; SSE or WebSocket transport from FastAPI; token-by-token
  yield from agent nodes; client-visible progress events (thinking / tool-calling / answer states);
  graceful stream teardown on disconnect; unit + integration tests with a mock LLM.
- **Acceptance:** first token visible at frontend within 500 ms of request; stream ends cleanly on both
  success and LLM error; existing non-streaming paths unaffected.
- **Cross-layer pairing:** GPM-F7 (FE streaming render, frontend-core #33) — must coordinate on the
  SSE event schema before either feature is final.

---

### GPM-F2 — Feature: Conversation memory / thread state (middle-core #33)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** GPM-F1 (streaming
  baseline); **parallel with** GPM-F3, GPM-F4 after GPM-F1
- **Scope:** Thread-scoped memory store (in-memory default, pluggable backend); LangGraph
  `MemorySaver` or equivalent wired per thread ID; conversation history trimming policy
  (max-tokens / max-turns); `GET /threads/{id}/history` endpoint; thread expiry / TTL.
- **Acceptance:** second turn in same thread receives condensed prior context; new thread ID starts
  fresh; history endpoint returns ordered message log; memory does not leak across threads.

---

### GPM-F3 — Feature: Analytics tools over UDA query (middle-core #34)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** RT6 UDA query
  endpoints (backend-core); **parallel with** GPM-F2, GPM-F4 after GPM-F1
- **Scope:** LangGraph tool nodes that call backend-core UDA query API (pagination-aware, RT6 #47);
  structured output formatting for analytics responses; tool-use telemetry spans; error handling for
  UDA unavailability.
- **Acceptance:** agent correctly selects analytics tool for data-retrieval intent; tool calls appear
  in OTel trace; UDA timeout returns graceful degradation message, not a 500.
- **Cross-RT dependency:** RT6 backend-core #47 (query pagination) must be stable before this feature
  can be fully integration-tested.

---

### GPM-F4 — Feature: MCR-F4 provider contract test (middle-core #35)

- **Type:** Feature · **Size:** S · **Estimate:** 3 · **Priority:** P1 · **Depends on:** RT7 MCR-F4
  (C# data-platform objects + `I{ObjectType}Projection` interfaces)
- **Scope:** Pact or schema-snapshot contract tests verifying that the Python LangGraph runtime's
  consumption of middle-core typed data contracts matches the published `DataPlatformContracts.g.cs`
  interfaces; CI gate fails on contract drift; test fixtures cover all 9 object types.
- **Acceptance:** CI runs contract tests on every PR touching middle-core runtime or model.yaml; drift
  detected within the same PR that introduces it; no manual coordination needed to detect breakage.
- **Rationale:** Enforces the contract-first principle between the C# model factory (RT7 MCR-F4) and
  the Python agent runtime's consumption of those contracts.

---

### GPM-F5 — Feature: OTel + Prometheus on agent runtime (middle-core #36)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** GPM-F1;
  **parallel with** GPM-F2, GPM-F3
- **Scope:** OpenTelemetry `ActivitySource` for agent invocations; spans for LangGraph node execution,
  tool calls, LLM completions; Prometheus counters `agent_invocations_total`, `agent_errors_total`,
  `llm_tokens_used_total`; histogram `agent_duration_seconds`; `/metrics` endpoint; OTLP exporter
  (console fallback in Development); correlation ID propagated from HTTP request to all child spans.
- **Acceptance:** full agent invocation produces an exportable trace; `/metrics` returns all counters;
  correlation ID visible in spans; OTLP disabled gracefully when env var absent.
- **Note:** Complements RT7 MCR-F3 (C# runtime OTel) — the two runtimes share the same OTLP
  collector; coordinate metric naming conventions.

---

### GPM-EN1 — Enabler: ArcadeDB pin backend wired to agent runtime (middle-core #37)

- **Type:** Enabler · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** RT5 PIN-F4
  (ArcadeDB adapter), RT7 MCR-F1 (ArcadeDB persistence for C# runtime)
- **Scope:** Wire `IPinStore` → `ArcadeDbPinBackend` in the Python runtime's persistence layer (via
  the REST API surface that MCR-F1 exposes, or a shared adapter); conversation thread state and agent
  scenario outputs pinned to ArcadeDB; `PIN_BACKEND=arcadedb` env var controls activation.
- **Acceptance:** agent run produces pinned records visible via `GET /pins/{identityHash}/history`;
  restart does not lose thread history; in-memory fallback activates when `PIN_BACKEND` is unset.
- **Note:** Local ID `ArcadeDbPinBackend behind PIN-F4` from the task brief maps here.

---

### GPM-EN2 — Enabler: Ontology reification + hyperedges (middle-core #38)

- **Type:** Enabler · **Size:** M · **Estimate:** 5 · **Priority:** P2 · **Depends on:** RT5 PIN-F2
  (reification + PinnedElement model)
- **Scope:** Python-side reification support: relator instances with role bindings emitted from
  LangGraph tool nodes; hyperedge serialization compatible with the ArcadeDB DDL from PIN-F4;
  `ingest-evidence` 4-role relator as the showcase pattern; schema validated against `middle-core.ttl`.
- **Acceptance:** tool node emits a `RelatorInstance` with correct role bindings; serialized form
  round-trips through the pin store without data loss; UFO stereotype fields populated correctly.

---

### GPM-F1b — Feature: Agent runtime ACA deploy (middle-core #39)

> Note: Assigned local ID GPM-F1b to avoid collision with GPM-F1; this is a separate shipping feature.

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** GPM-F1, GPM-F5
  (OTel wired), GPM-EN1 (pin backend configured)
- **Scope:** `deploy/aca-agent-runtime.yaml` Azure Container Apps manifest for the Python LangGraph
  runtime; Dockerfile with OTel + PIN_BACKEND env defaults; GitHub Actions workflow triggering on
  push to `main`; environment variables for ArcadeDB URL, OTLP endpoint, Foundry embed endpoint,
  Key Vault references (AKV akv01-agentarmy); health check endpoint.
- **Acceptance:** `az containerapp create` succeeds from manifest; `/health` returns 200 in ACA;
  CI workflow fails the PR if the Docker build breaks; rolling deployment leaves zero downtime.
- **Cross-layer pairing:** GPM-F11 (FE auth/session UX, frontend-core #36) — the ACA-deployed runtime
  URL is the backend endpoint the frontend authenticates against; coordinate env var naming.

---

### GPM-E2 — Epic: Generative UI Maturity (frontend-core)

- **Type:** Epic · **PI:** PI-3 (candidate) · **Priority:** P1
- **Spoke repo:** `nickpclarke/frontend-core`
- **Outcome:** The Next.js + CopilotKit frontend delivers a cockpit dashboard with real-time agent
  state, streaming token render, a coherent design system, a performance budget enforced in CI,
  authenticated sessions wired to the ACA-deployed runtime, and a Storybook component catalogue.
- **Children:** GPM-F6, GPM-F7, GPM-F8, GPM-F9, GPM-F10, GPM-F11, GPM-EN3.

---

### GPM-F6 — Feature: Cockpit dashboard (frontend-core #32)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** GPM-F7 (streaming
  render must exist to populate dashboard panels); **parallel with** GPM-F8, GPM-F9 after design
  system is stable
- **Scope:** Real-time dashboard surface: active agent threads panel, tool-call trace viewer, metric
  sparklines (invocations/errors from GPM-F5 `/metrics`), conversation history sidebar; CopilotKit
  `useCopilotAction` hooks wired to agent streaming endpoint; responsive layout.
- **Acceptance:** dashboard reflects live agent state within one streaming cycle; metric sparklines
  update on Prometheus scrape; thread history panel scrolls correctly; layout passes WCAG AA contrast.

---

### GPM-F7 — Feature: Streaming render (frontend-core #33)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P0 · **Depends on:** GPM-F1
  (MC streaming must exist); **keystone for** GPM-F6 (cockpit), GPM-F11 (auth wiring)
- **Scope:** CopilotKit `useCoAgent` or `useCopilotChat` consuming the SSE stream from GPM-F1;
  incremental token render with skeleton loading states; thinking/tool-calling/answer phase indicators;
  error boundary with retry UI; abort-stream button.
- **Acceptance:** first token renders within 750 ms of send; UI shows distinct states for
  thinking/tool-calling/answer; stream abort clears state cleanly; no memory leaks on repeated
  conversations (measured via browser heap snapshot).
- **Cross-layer pairing:** GPM-F1 (MC streaming, middle-core #32) — SSE event schema must be agreed
  before either feature is finalled.

---

### GPM-F8 — Feature: Design system / theming (frontend-core #34)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** —
  (independent; can start any time); **parallel with** GPM-F6, GPM-F7
- **Scope:** Tailwind CSS design tokens (color palette, typography scale, spacing); dark/light mode
  toggle with `next-themes`; shared component primitives (Button, Card, Badge, Skeleton, Toast)
  aligned to the token set; CopilotKit theme overrides; exported as a design-token JSON for Storybook.
- **Acceptance:** all existing pages pass the design token set without inline overrides; dark mode
  persists across page refresh (localStorage); design-token JSON consumed by Storybook (GPM-F11b).

---

### GPM-F9 — Feature: Performance budget CI (frontend-core #35)

- **Type:** Feature · **Size:** S · **Estimate:** 3 · **Priority:** P1 · **Depends on:** —
  (independent); **parallel with** GPM-F6, GPM-F7, GPM-F8
- **Scope:** Lighthouse CI or `bundlewatch` step in GitHub Actions; budgets: LCP ≤ 2.5 s, TBT ≤ 200 ms,
  JS bundle ≤ 250 kB (compressed); PR check fails if budgets are exceeded; baseline captured from
  current main.
- **Acceptance:** CI step runs on every PR; baseline snapshot committed; first budget breach blocks
  merge; report link posted as PR comment.

---

### GPM-F10 — Feature: Auth / session UX (frontend-core #36)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** GPM-F1b
  (ACA deploy must provide an authenticated endpoint); GPM-F7 (streaming render)
- **Scope:** NextAuth.js (or Entra ID MSAL) session provider; sign-in / sign-out pages; protected
  routes (middleware); session token propagated in Authorization header to ACA-deployed agent runtime;
  session expiry handled gracefully in streaming contexts (stream abort + re-auth prompt).
- **Acceptance:** unauthenticated user is redirected to sign-in; valid session reaches the runtime
  without 401; expired token during stream shows re-auth prompt (not a crash); sign-out clears
  conversation state.
- **Cross-layer pairing:** GPM-F1b (MC ACA deploy, middle-core #39) — runtime auth middleware must
  accept the token format the frontend sends; coordinate before implementation.

---

### GPM-F11b — Feature: Storybook component catalogue (frontend-core #37)

> Note: Assigned local ID GPM-F11b to keep the F10/F11 pairing with ACA deploy clear.

- **Type:** Feature · **Size:** S · **Estimate:** 3 · **Priority:** P2 · **Depends on:** GPM-F8
  (design system tokens); **parallel with** GPM-F9, GPM-F10
- **Scope:** Storybook 8 configured for Next.js + Tailwind; stories for all shared primitives from
  GPM-F8 (Button, Card, Badge, Skeleton, Toast); CopilotKit panel story with mocked streaming; design
  token addon; deployed to GitHub Pages on merge to main.
- **Acceptance:** `storybook build` succeeds in CI; all primitive components have at least one story;
  CopilotKit story renders with mock data without network calls; GitHub Pages deploy runs on merge.

---

### GPM-EN3 — Enabler: Frontend → ACA runtime wiring (frontend-core integration)

- **Type:** Enabler · **Size:** S · **Estimate:** 2 · **Priority:** P1 · **Depends on:** GPM-F1b
  (ACA deploy URL known), GPM-F10 (auth wired)
- **Scope:** `NEXT_PUBLIC_AGENT_RUNTIME_URL` env var wired through Vercel environment config and
  `.env.local` template; CopilotKit runtime URL config updated from localhost to ACA endpoint;
  smoke-test PR check hitting the staging ACA deployment.
- **Acceptance:** frontend on Vercel preview deployment successfully streams from ACA runtime;
  env var documented in repo README; smoke test runs on every PR touching runtime URL config.

---

## Cross-layer pairing map

The following features must be coordinated across spoke repos — schema, contract, or endpoint
agreement is required before either side can be finalled:

| Middle-core feature | Frontend-core feature | What to agree upfront |
|---|---|---|
| GPM-F1 — agent response streaming (MC #32) | GPM-F7 — streaming render (FE #33) | SSE event schema (event types, field names, error envelopes) |
| GPM-F1b — ACA deploy (MC #39) | GPM-F10 — auth/session UX (FE #36) | Auth token format + runtime middleware configuration |
| GPM-F5 — OTel + Prometheus (MC #36) | GPM-F6 — cockpit dashboard (FE #32) | `/metrics` label names + scrape endpoint path |
| GPM-EN1 — ArcadeDB pin backend (MC #37) | GPM-F10 — auth/session UX (FE #36) | Session-to-thread-ID mapping for conversation persistence |

---

## Dependency graph

```
GPM-F1 (MC streaming — MC #32)                       ← KEYSTONE; unblocks FE streaming
  │
  ├─ GPM-F2 (MC memory/thread state — MC #33)
  ├─ GPM-F3 (MC analytics tools over UDA — MC #34)    ← needs RT6 #47 stable
  ├─ GPM-F5 (MC OTel + Prometheus — MC #36)
  │
  └─ GPM-F7 (FE streaming render — FE #33)            ← FE KEYSTONE; unblocks cockpit
       │
       ├─ GPM-F6 (FE cockpit dashboard — FE #32)
       └─ GPM-F10 (FE auth/session UX — FE #36)       ← needs GPM-F1b (ACA deploy)

GPM-F4 (MC contract test — MC #35)                    ← needs RT7 MCR-F4 first
GPM-EN1 (MC ArcadeDB pin backend — MC #37)            ← needs RT5 PIN-F4 + RT7 MCR-F1
GPM-EN2 (MC reification/hyperedges — MC #38)          ← needs RT5 PIN-F2

GPM-F8 (FE design system — FE #34)                    ← independent; start any time
GPM-F9 (FE perf budget CI — FE #35)                   ← independent; start any time
GPM-F11b (FE Storybook — FE #37)                      ← needs GPM-F8

GPM-F1b (MC ACA deploy — MC #39)                      ← needs GPM-F1 + GPM-F5 + GPM-EN1
  └─ GPM-EN3 (FE → ACA wiring — FE integration)       ← needs GPM-F1b + GPM-F10
       └─ GPM-F10 (FE auth/session UX — FE #36)

GPM-EN3 (FE → ACA runtime wiring)                     ← last; needs both F1b and F10
```

**Keystone (MC side):** GPM-F1 — streaming from the agent runtime is the enabling contract for the
generative UI. Until it exists, GPM-F7 and downstream FE features cannot be integration-tested.

**Keystone (FE side):** GPM-F7 — once the frontend can render a stream, cockpit, auth, and Storybook
work can proceed in parallel.

**Parallelisation window:** After GPM-F1 + GPM-F7 ship: GPM-F2, GPM-F3, GPM-F5 (MC) and GPM-F6,
GPM-F8, GPM-F9 (FE) are all independent — up to 6 agents can run concurrently.

---

## Cross-RT dependencies

| This RT depends on | Reason |
|---|---|
| RT5 PIN-F2 (reification + PinnedElement) | Required by GPM-EN2 (hyperedges) |
| RT5 PIN-F4 (ArcadeDB adapter) | Required by GPM-EN1 (pin backend wiring) |
| RT6 UDA query endpoints (backend-core #47) | Required by GPM-F3 (analytics tools) |
| RT7 MCR-F1 (ArcadeDB persistence for C# runtime) | Required by GPM-EN1 (shared ArcadeDB instance) |
| RT7 MCR-F3 (OTel instrumentation) | Coordinate metric naming with GPM-F5 |
| RT7 MCR-F4 (C# data-platform objects) | Required by GPM-F4 (contract test) |

RT8 does **not** depend on RT1–RT4 hub template features — those are template scaffolding; RT8 is a
spoke-implementation train that delivers running software.

---

## Exit criteria

**GPM-E1 (middle-core) is done when:**
- Agent responses stream token-by-token to the frontend (GPM-F1)
- Conversation thread state persists across turns (GPM-F2)
- Analytics tool calls over UDA are exercised end-to-end (GPM-F3)
- MCR-F4 contract tests pass in CI with zero manual coordination (GPM-F4)
- OTel traces and Prometheus metrics exported from every agent invocation (GPM-F5)
- ArcadeDB pin backend wired and smoke-tested in ACA (GPM-EN1)
- Agent runtime deployed to Azure Container Apps with passing health check (GPM-F1b)

**GPM-E2 (frontend-core) is done when:**
- Streaming tokens render incrementally with phase indicators (GPM-F7)
- Cockpit dashboard reflects live agent state (GPM-F6)
- Design system tokens applied consistently; dark mode works (GPM-F8)
- Performance budgets enforced in CI with baseline committed (GPM-F9)
- Authenticated sessions propagate from Next.js to ACA runtime (GPM-F10)
- Storybook catalogue deployed to GitHub Pages (GPM-F11b)
- Frontend on Vercel connects to ACA runtime via GPM-EN3

**Full RT8 exit criterion:** An end-to-end flow — user signs in, sends a message, sees streaming
tokens render in the cockpit, and the conversation is pinned to ArcadeDB — runs without manual
intervention in the staging environment.

---

## PI assignment

**PI-3 (candidate).** RT8 is a spoke-implementation train scoped to the PI-3 planning horizon.
Confirm sprint assignment at PI planning by checking RT5 and RT7 delivery status — GPM-EN1
and GPM-F4 are blocked until those dependencies ship. If RT5 PIN-F4 slips, GPM-EN1 falls back
to `InMemoryPinBackend` for the sprint (same fallback as RT7 MCR-F1).

**Session estimate breakdown:**

| Session | Target features | Throughput | Notes |
|---|---|---|---|
| Session A | GPM-F1 (MC streaming), GPM-F8 (FE design system), GPM-F9 (FE perf budget) | 3 features | Keystone + independent FE features; 3 parallel agents |
| Session B | GPM-F7 (FE streaming render), GPM-F2 (MC memory), GPM-F5 (MC OTel) | 3 features | FE keystone unlocked; 3 parallel agents |
| Session C | GPM-F6 (FE cockpit), GPM-F3 (MC analytics), GPM-F4 (MC contract test) | 3 features | Post-keystone parallelism; RT6 #47 must be stable |
| Session D | GPM-F10 (FE auth), GPM-F1b (MC ACA deploy), GPM-F11b (FE Storybook) | 3 features | Deploy + auth layer |
| Session E | GPM-EN1 (MC ArcadeDB pin), GPM-EN2 (MC reification), GPM-EN3 (FE → ACA wiring) | 2–3 features | Depends on RT5/RT7 readiness; may slip to Session F |
| Session F (buffer) | Spillover, integration testing, revision passes | — | Hold in reserve |

---

## Notes

- **Spoke-implementation train.** All deliverables are in `nickpclarke/middle-core` and
  `nickpclarke/frontend-core`. No hub template files are modified.
- **Contract-first coordination.** The SSE event schema (GPM-F1 ↔ GPM-F7) and auth token format
  (GPM-F1b ↔ GPM-F10) must be agreed in a shared contract document before implementation starts.
  Use the backend-core OpenAPI pattern — define the schema first, generate clients.
- **Azure environment.** ACA deploy (GPM-F1b) targets Azure subscription AASub1, Key Vault
  akv01-agentarmy, Foundry fndry-01 (Cohere embed-v-4-0, 1536-d). Credentials via AKV references
  in the ACA manifest, not environment variable literals.
- **Board population.** When scheduling, create issues in the spoke repos (not the hub), set `Type`,
  `PI`, `Size`, `Estimate`, `Priority`, link children to their Epic, add to the spoke board.
  The live issue numbers are already assigned: middle-core #32–#39, frontend-core #32–#37.
