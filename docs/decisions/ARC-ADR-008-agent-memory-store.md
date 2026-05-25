# ARC-ADR-008 — Agent Conversation-Memory / Thread-State Store and Per-User Isolation

| Field | Value |
|---|---|
| ID | ARC-ADR-008 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | memory, thread-state, langgraph, checkpointer, middle-core, isolation, copilotkit |

---

## Context and Problem Statement

The LangGraph agent in middle-core (`agent.py`, #21) is currently effectively stateless per request.
Multi-turn conversation, resumable threads, and the CopilotKit interrupt/resume flow
(`renderAndWaitForResponse`, [ARC-ADR-006](ARC-ADR-006-hitl-destructive-ops.md)) all require the
agent's **thread state** — message history, scratchpad, and the paused-run checkpoint — to persist
across HTTP requests. LangGraph models this with a **checkpointer** keyed by a `thread_id`.

Two things must be decided together:

1. **Where thread state lives** — an in-process checkpointer (lost on restart, single-replica only),
   a Redis/cache checkpointer, an ArcadeDB-backed store, or a managed LangGraph checkpointer backend.
2. **How threads are isolated** — middle-core forwards the user JWT but does not own identity
   (ARC-ADR-002). A `thread_id` chosen by the client is forgeable; without binding it to the
   authenticated subject, user A could resume user B's conversation (an IDOR-class leak of chat
   history that may contain RAG results from sources A can't access).

The decision to be made is: **what backs the LangGraph checkpointer for conversation memory, and how
is each thread bound to its owning principal so one user cannot read or resume another's thread?**

This gates real multi-turn UX (CopilotKit Phase 2+), middle-core #32 (agent runtime state) and #33
(thread/session handling), and any horizontal scaling of middle-core (more than one replica makes an
in-process store immediately wrong).

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | Conversation memory and paused-run checkpoints must survive across requests, and ideally across middle-core restarts/deploys. |
| D2 | middle-core will run >1 replica under ACA — the store must be shared across replicas (rules out a naive in-process map for prod). |
| D3 | **Isolation is non-negotiable:** a thread must be bound to its owning principal (the JWT `sub`); a forged or guessed `thread_id` from another user must be rejected. |
| D4 | Thread state may contain sensitive material (RAG snippets, the user's JWT must NOT be persisted into it per ARC-ADR-002). Storage must respect that. |
| D5 | Must integrate with LangGraph's checkpointer interface — prefer a supported backend over a bespoke one. |
| D6 | A retention/eviction policy is required — threads must not accumulate unboundedly (TTL or explicit deletion). |

---

## Considered Options

1. **Redis-backed LangGraph checkpointer + principal-scoped thread keys** (recommended baseline) —
   use a Redis checkpointer (or `langgraph-checkpoint-redis`); the effective thread key is
   `hash(sub) + ":" + thread_id`, derived server-side from the forwarded JWT subject, so a client
   cannot address another principal's thread. TTL handles eviction.
2. **In-process / SQLite checkpointer (dev only)** — LangGraph's in-memory or SQLite saver. Zero
   infrastructure; correct only for single-replica/local. Explicitly *not* a prod answer but a valid
   local-dev default.
3. **ArcadeDB-backed checkpointer** — persist thread state in the same ArcadeDB instance the platform
   already runs (RT7 MCR-F1), modeling threads as objects. Converges memory with the platform's
   canonical store; one fewer dependency than Redis.
4. **Managed LangGraph Platform / Postgres checkpointer** — use LangGraph's hosted/Postgres
   checkpointer as the durable backend, offloading the persistence and retention machinery.

---

## Decision Outcome

**Accepted 2026-05-25 — Option 3: ArcadeDB-backed checkpointer (reuse the platform ArcadeDB); the principal-scoped thread-key isolation rule (key derived server-side from JWT sub) applies regardless of backend.** The HITL framing that produced this choice: HITL — the Architecture Review must choose. The isolation mechanism (D3) is the
load-bearing part and is *common to every option*; the open question is the backend.

### Recommendation note (not a decision)

- **Adopt the isolation rule regardless of backend:** the checkpointer thread key is **derived
  server-side from the JWT `sub`** (read-only decode, permitted by the
  [ADR-002 read ≠ verify ≠ modify clarification](ARC-ADR-002-jwt-forwarding-auth-contract.md#read-vs-verify--clarification-2026-05-25)),
  never taken verbatim from a client-supplied field. The client may pass a `thread_id` for *its own*
  threads; the server namespaces it under the authenticated subject.
- **Backend:** lean **Option 1 (Redis)** for prod (mature LangGraph support, native TTL for D6,
  trivially shared across replicas for D2) with **Option 2 (in-process/SQLite)** as the local-dev
  default behind a config switch (mirrors the ARC-ADR-004 `LLM_PROVIDER` env pattern). Revisit
  **Option 3 (ArcadeDB)** if "one model, many projections" makes threads a first-class modeled object
  and the extra Redis dependency is judged not worth it — but only once ArcadeDB persistence
  (MCR-F1) is proven.
- **Never persist the JWT** into thread state (ARC-ADR-002 D2/secret-handling); it is request-scoped only.

A short spike to confirm `langgraph-checkpoint-redis` interop with the CopilotKit interrupt/resume
flow under ACA would de-risk Option 1.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | Checkpointer wiring in `agent.py`/`app.py`; principal-scoped thread keys; retention; #21, #22, #32, #33 |
| frontend-core | nickpclarke/frontend-core | Passes a per-conversation `thread_id`; must not assume it can choose arbitrary IDs across users; #14, #15 |
| backend-core | nickpclarke/backend-core | No impact — memory lives in middle-core; backend-core remains stateless behind tool calls |

---

## Pros and Cons of the Options

### Option 1 — Redis checkpointer + principal-scoped keys (recommended baseline)

**Pros:**
- Mature LangGraph support; shared across replicas (D2); native TTL for retention (D6).
- Isolation is a key-derivation concern, cleanly server-side (D3).
- Operationally familiar; horizontal scaling is straightforward.

**Cons:**
- Adds a Redis dependency (infra + Key Vault connection string + ACA wiring).
- Another store to secure and back up; memory durability depends on Redis persistence config.

### Option 2 — In-process / SQLite checkpointer

**Pros:** Zero infrastructure; perfect for local dev and tests; LangGraph ships it.

**Cons:** Wrong for >1 replica (D2 fail); lost on restart (D1 fail). Dev-only — must not reach prod.

### Option 3 — ArcadeDB-backed checkpointer

**Pros:** Converges with the platform's canonical store ("one model, many projections"); no new dependency beyond ArcadeDB; threads become modeled objects.

**Cons:** No off-the-shelf LangGraph ArcadeDB checkpointer — bespoke implementation + tests (against D5's "prefer supported backend"); couples agent memory to ArcadeDB availability; blocked on MCR-F1.

### Option 4 — Managed LangGraph Platform / Postgres checkpointer

**Pros:** Offloads persistence + retention; battle-tested Postgres saver.

**Cons:** New managed dependency / Postgres instance off the current Azure path; cost + data-residency review; heavier than the platform currently needs.

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding auth contract — the `sub` used for thread isolation comes from a read-only decode; the JWT itself must never be persisted into thread state.
- **ARC-ADR-006:** HITL for destructive ops — `renderAndWaitForResponse` pauses a run; that paused checkpoint is exactly what this store must persist and resume.
- **ARC-ADR-007** (proposed): Agent streaming protocol — resumable threads and mid-stream interrupts interact with the transport that carries them.
- **ARC-ADR-011** (backlog): Runtime secret-resolution — a Redis/Postgres connection string would resolve via the `akv:` + managed-identity scheme.
- **ARC-ADR-009** (proposed): Canonical data model — if Option 3 wins, threads become modeled objects under the canonical model.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
