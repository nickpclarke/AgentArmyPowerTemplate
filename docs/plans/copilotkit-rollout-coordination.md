# CopilotKit Rollout Coordination Map

> Cross-repo coordination surface for the four-layer CopilotKit generative-UI initiative.
> Source plan: [copilotkit-generative-ui.md](copilotkit-generative-ui.md)
> Status: backlogs drafted — epics and features created as draft issues in each spoke repo.

---

## Per-Repo Epic and Feature Table

### nickpclarke/frontend-core

| Type | Issue | Title | Phase | Routing | ADR Gates |
|---|---|---|---|---|---|
| Epic | [#12](https://github.com/nickpclarke/frontend-core/issues/12) | CopilotKit generative UI | all | agent-army-task | ADR-002, ADR-003 |
| Feature | [#13](https://github.com/nickpclarke/frontend-core/issues/13) | `/api/copilotkit` runtime route (Empty adapter + JWT forward) | 0 | agent-army-task | ADR-002, ADR-003 |
| Feature | [#14](https://github.com/nickpclarke/frontend-core/issues/14) | `<CopilotKit>` provider in App Router layout | 0 | copilot-task | ADR-002 |
| Feature | [#15](https://github.com/nickpclarke/frontend-core/issues/15) | Phase 1 — RAG search citation generative UI | 1 | agent-army-task | — |
| Feature | [#16](https://github.com/nickpclarke/frontend-core/issues/16) | Phase 2 — Ingest assistant job-progress card | 2 | agent-army-task | — |
| Feature | [#17](https://github.com/nickpclarke/frontend-core/issues/17) | Phase 3 — Source management + HITL delete confirmation | 3 | agent-army-task | ADR-006 |
| Feature | [#18](https://github.com/nickpclarke/frontend-core/issues/18) | Phase 4 — Cockpit analytics, cross-modal gallery, suggestions, app-state | 4 | agent-army-task | — |

### nickpclarke/middle-core

| Type | Issue | Title | Phase | Routing | ADR Gates | Distinct from RT7? |
|---|---|---|---|---|---|---|
| Epic | [#17](https://github.com/nickpclarke/middle-core/issues/17) | CopilotKit agent runtime | all | agent-army-task | ADR-002, ADR-004, ADR-005 | Yes — Python/LangGraph; RT7 is C#/.NET |
| Feature | [#18](https://github.com/nickpclarke/middle-core/issues/18) | `llm.py` — ChatCerebras factory + OpenAI-compatible fallback | 0 | agent-army-task | ADR-004 | — |
| Feature | [#19](https://github.com/nickpclarke/middle-core/issues/19) | `backend_client.py` — async httpx client with JWT forwarding | 0 | agent-army-task | ADR-002, ADR-005 | — |
| Feature | [#20](https://github.com/nickpclarke/middle-core/issues/20) | `tools.py` — LangGraph tools delegating to backend-core | 0/1 | agent-army-task | ADR-005, ADR-006 | — |
| Feature | [#21](https://github.com/nickpclarke/middle-core/issues/21) | `agent.py` — create_react_agent (knowledge_copilot) | 0 | agent-army-task | ADR-004 | — |
| Feature | [#22](https://github.com/nickpclarke/middle-core/issues/22) | `app.py` — FastAPI `/copilotkit` endpoint + CORS + JWT injection | 0 | agent-army-task | ADR-002, ADR-003 | — |

### nickpclarke/backend-core

| Type | Issue | Title | Phase | Routing | ADR Gates |
|---|---|---|---|---|---|
| Epic | [#16](https://github.com/nickpclarke/backend-core/issues/16) | CopilotKit enablement (CORS + RBAC pass-through) | all | agent-army-task | ADR-002 |
| Enabler | [#17](https://github.com/nickpclarke/backend-core/issues/17) | Config-driven CORSMiddleware | 0 | copilot-task | ADR-002 |
| Enabler | [#18](https://github.com/nickpclarke/backend-core/issues/18) | `CORS_ORIGINS` config key in app/config.py + .env.example | 0 | copilot-task | — |
| Enabler | [#19](https://github.com/nickpclarke/backend-core/issues/19) | Verify `require_principal` accepts forwarded JWT | 0 | agent-army-task | ADR-002 |

---

## Cross-Repo Producer/Consumer Dependency Graph

```
backend-core (producer: /api/v1/* + CORS + RBAC)
    |
    |  HTTP + forwarded JWT (ADR-002, ADR-005)
    v
middle-core (producer: /copilotkit + LangGraph agent)
    |
    |  HTTPS + forwarded JWT + CopilotKit streaming (ADR-002, ADR-003)
    v
frontend-core (consumer: renders generative UI)
    |
    |  user JWT from session (ADR-002)
    v
  browser (no LLM key — ADR-003)
```

### Explicit cross-repo dependencies

| Dependency | Producer repo + issue | Consumer repo + issue | Blocking? |
|---|---|---|---|
| `contracts/backend-core.openapi.json` current | backend-core (maintained by CI drift check) | middle-core #19 (typed client generation) | Yes — middle-core client generated from this |
| `CORSMiddleware` live in backend-core | backend-core #17 | middle-core #19, #20 | Yes — tools need cross-origin access |
| `require_principal` JWT verification confirmed | backend-core #19 | middle-core #17 (all tools) | Yes — tools depend on RBAC working for forwarded JWTs |
| middle-core `/copilotkit` endpoint live | middle-core #22 | frontend-core #13 | Yes — Phase 0 smoke test |
| `knowledge_copilot` agent registered | middle-core #21, #22 | frontend-core #14 (provider `agent` prop) | Yes — provider must reference correct agent name |
| `search_knowledge` tool live | middle-core #20 | frontend-core #15 (Phase 1 citations) | Yes |
| `ingest_source` + `get_job_status` tools live | middle-core #20 | frontend-core #16 (Phase 2 progress card) | Yes |
| `delete_source` tool with HITL | middle-core #20 | frontend-core #17 (Phase 3 HITL card) | Yes |
| `cockpit_metrics` + `get_stats` tools live | middle-core #20 | frontend-core #18 (Phase 4) | Yes |

---

## ADR Gates: Which ADR Gates Which Work

| ADR | Title | Gates (must be Accepted before work starts) |
|---|---|---|
| [ARC-ADR-002](../decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md) | JWT-forwarding auth contract | middle-core `app.py` (#22), `backend_client.py` (#19); frontend-core runtime route (#13); backend-core JWT verification (#19) |
| [ARC-ADR-003](../decisions/ARC-ADR-003-no-llm-key-in-browser.md) | No LLM key in browser | frontend-core runtime route (#13) and layout provider (#14) |
| [ARC-ADR-004](../decisions/ARC-ADR-004-llm-provider-cerebras.md) | LLM provider = Cerebras | middle-core `llm.py` (#18) and `agent.py` (#21) |
| [ARC-ADR-005](../decisions/ARC-ADR-005-backend-core-openapi-contract.md) | backend-core OpenAPI contract consumed by middle-core | middle-core `backend_client.py` (#19) and `tools.py` (#20) |
| [ARC-ADR-006](../decisions/ARC-ADR-006-hitl-destructive-ops.md) | HITL for destructive ops | middle-core `delete_source` in `tools.py` (#20); frontend-core Phase 3 HITL card (#17) |

All five ADRs are currently **Proposed**. The Architecture Review must accept each before the gated work begins. Acceptance is recorded by changing Status from `Proposed` to `Accepted` in the ADR file and committing to main.

---

## Phase 0–4 Sequencing

### Phase 0 — End-to-end smoke test (foundation)

Sequencing constraint: **backend-core must complete before middle-core; middle-core must complete before frontend-core.**

| Step | Repo | Issues | ADR prerequisite |
|---|---|---|---|
| 0a | backend-core | #18 (config), #17 (CORS), #19 (JWT verify) | ADR-002 |
| 0b | middle-core | #18 (llm.py), #19 (backend_client), #21 (agent.py), #22 (app.py) + search tool in #20 | ADR-002, ADR-003, ADR-004, ADR-005 |
| 0c | frontend-core | #13 (runtime route), #14 (provider + sidebar) | ADR-002, ADR-003 |

Checkpoint 0: `POST /copilotkit` from frontend-core reaches middle-core, agent calls `search_knowledge`, tool calls `GET /api/v1/search` on backend-core with forwarded JWT, returns results to the chat sidebar.

### Phase 1 — RAG citation generative UI

| Step | Repo | Issues | Prerequisite |
|---|---|---|---|
| 1a | middle-core | `search_knowledge` full implementation in #20 | Phase 0 complete |
| 1b | frontend-core | #15 (citation cards) | Phase 1a complete |

Checkpoint 1: Citation cards render inline in the chat with source chips and image thumbnails.

### Phase 2 — Ingest assistant

| Step | Repo | Issues | Prerequisite |
|---|---|---|---|
| 2a | middle-core | `ingest_source` + `get_job_status` in #20 | Phase 1 complete |
| 2b | frontend-core | #16 (job-progress card) | Phase 2a complete |

Checkpoint 2: Asking the copilot to ingest a URL shows a live progress card.

### Phase 3 — Source management + HITL delete

| Step | Repo | Issues | ADR prerequisite |
|---|---|---|---|
| 3a | middle-core | `list_sources` + `delete_source` (with HITL guard) in #20 | ADR-006 |
| 3b | frontend-core | #17 (sources table + confirmation card) | ADR-006, Phase 3a complete |

Checkpoint 3: Admin user can list sources; delete triggers confirmation card; non-admin sees permission-denied; cancel preserves the source.

### Phase 4 — Cockpit + gallery + suggestions + app-state

| Step | Repo | Issues | Prerequisite |
|---|---|---|---|
| 4a | middle-core | `get_stats` + `cockpit_metrics` in #20 | Phase 3 complete |
| 4b | frontend-core | #18 (metrics cards, gallery, suggestions, app-state) | Phase 4a complete |

Checkpoint 4: Full generative-UI feature set live; all seven use cases functional.

---

## Cross-Layer "Come Together" Checkpoints

These are the moments where work from multiple repos must be integrated and verified together. Each checkpoint is a candidate for a local `docker-compose up` integration test.

| Checkpoint | Phase | What to test | Repos involved |
|---|---|---|---|
| **CP-0** | Phase 0 | E2E: question in sidebar → middle-core agent → `search` tool → backend-core → response with source citation | all three |
| **CP-1** | Phase 1 | Citation cards render from real search results; JWT role blocking verified | frontend-core + middle-core + backend-core |
| **CP-2** | Phase 2 | Ingest job-progress card updates live; job-status polling works | frontend-core + middle-core + backend-core |
| **CP-3** | Phase 3 | HITL delete flow: confirmation card → user confirms → backend-core delete called once; user cancels → no delete | all three |
| **CP-4** | Phase 4 | Cockpit metrics render; cross-modal gallery shows image hits; suggestions change per route | all three |

---

## RT7 Coordination Note (middle-core)

The CopilotKit agent runtime epic (middle-core #17) is **distinct** from RT7 (MCR-E, issue #7). RT7 is the C#/.NET model-driven factory + ArcadeDB admin/instrumentation platform. They share the same repo but are different services, different languages, different files, and different responsibilities. No file-level overlap is expected. If a shared config file or docker-compose service entry creates a conflict, open a coordination issue and tag both epics.

---

## Hub Notification Protocol

When each spoke epic reaches Definition of Done:

1. Close the epic Issue in the spoke repo.
2. Comment on this coordination map's tracking issue (or the hub Epic, once created) with: spoke repo, closed milestone link, one-line summary.
3. The hub scrum-master updates `planning/backlog/BACKLOG_ISSUES_INDEX.md` and `planning/release-trains/release-train-index.md` with actual velocity data.
