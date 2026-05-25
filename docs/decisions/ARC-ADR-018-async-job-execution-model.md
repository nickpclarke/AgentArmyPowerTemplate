# ARC-ADR-018 — Async / Job-Execution & Long-Running-Tool Model (durable execution for ingest)

| Field | Value |
|---|---|
| ID | ARC-ADR-018 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — to be decided; evidence from spike backend-core #67) |
| Supersedes | — |
| Superseded by | — |
| Tags | async, jobs, durable-execution, dbos, ingest, worker, backend-core, middle-core, copilotkit, uda |

---

## Context and Problem Statement

Long-running tools — document ingest, large UDA queries, dlt pipeline runs — currently
execute inside a lightweight in-process worker. backend-core's `app/jobs.py:IngestWorker`
is an `asyncio.Queue` plus a per-process `_attempts` dict and a hand-rolled
exponential-backoff retry loop. It has two durability holes:

1. **Queued work is volatile** — the queue and retry counters live only in process memory;
   a container restart loses everything still queued.
2. **In-flight work is dropped and restarted from scratch** — on restart only jobs still
   marked `pending` in ArcadeDB are re-enqueued, and each re-runs `extract → chunk → index`
   from the beginning, repeating the expensive embedding call even if it had already
   finished.

This decision was foreseen in the ADR backlog as the **async/job-execution &
long-running-tool model**: how do long-running tools execute and report progress — in-request, a
background worker, a durable-execution library, an external orchestrator, or a dlt pipeline
+ job-status polling? It gates the CopilotKit Phase 2 ingest **progress card**, UDA dlt
pipelines, and backend-core job-status endpoints.

A time-boxed spike (**backend-core #67**, `docs/research/0003-dbos-durable-execution.md` +
a runnable, tested PoC under `spikes/dbos_spike/`) evaluated the durable-execution space
against this gap.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Durability** — queued and in-flight work must survive a crash/restart; completed steps must not be re-run (no re-embedding). |
| D2 | **Minimal ops footprint** — the platform is cost-conscious on ACA/ACI; prefer no new always-on orchestrator service. |
| D3 | **Python-native** — backend-core's provider is Python/FastAPI; the model should fit it without a language change. |
| D4 | **Reversibility** (ADR-001 "reversible bets") — the execution engine must sit behind the existing worker interface so it can be swapped/removed without touching routes. |
| D5 | **Progress reporting** — long-running tools must expose status/progress for the CopilotKit Phase 2 ingest card and a cockpit admin surface (list/cancel/resume). |
| D6 | **Idempotency / exactly-once** — step bodies run at-least-once until checkpointed, so the model must make idempotent steps natural. |
| D7 | **No Rust SDK lock-out awareness** — `rust-api-v2` cannot use a Python-only library; the choice fits the *current Python provider* and must not block a future Rust path. |

## Considered Options

1. **In-process durable-execution library — DBOS Transact (Python)** *(recommended seed)*.
   Decorate the ingest workflow as `@DBOS.workflow()`/`@DBOS.step()`; DBOS checkpoints each
   step to a system database and resumes unfinished workflows from the last completed step.
   No new service — runs in-process. System DB defaults to **SQLite** (dev, zero infra),
   **Postgres** for production/multi-instance. Brings durable queues, built-in step retries
   (replacing the hand-rolled backoff), scheduled workflows, and `list/cancel/resume/fork`
   management for the cockpit.
2. **External orchestrator** (Temporal / Hatchet / Restate / Inngest). Most mature at scale;
   heavy — re-architect into separate worker + a persistence/cluster dependency (or a managed
   external service). Right answer only when workflows fan out across ≥3 services.
3. **Status quo — in-memory queue + hand-rolled retries + re-enqueue `pending` on restart.**
   Zero new dependency; the two durability holes above remain (lost queued work, repeated
   expensive steps).
4. **dlt pipeline + job-status polling** for UDA *bulk* ingest. Complementary, not competing:
   the durable-execution choice governs per-job step durability; dlt governs bulk
   source→destination loads. Both can coexist behind the worker/job-status interface.

## Decision Outcome

**To be decided** by Architecture Review (HITL — per ADR-001, the hub owner decides; this is
a Proposed stub with options + a recommendation, not a unilateral call). Queued **Proposed**
so the direction is on record with the spike evidence attached.

### Evidence from the spike (backend-core #67)

The PoC re-expressed `extract → chunk → index` as a DBOS durable workflow + durable queue on
a throwaway SQLite system DB and proved three guarantees (green against DBOS 2.22.0, Python
3.11):

1. **Durable queue** runs the pipeline and returns the result via a handle.
2. **Replay-safe (completed steps not re-executed)** — replaying a workflow id re-runs *zero*
   already-completed steps. This is checkpoint/replay safety, *not* side-effect exactly-once:
   step bodies are at-least-once until checkpointed, so external side effects (embedding/API
   writes) must be idempotent (see D6).
3. **Crash + resume** — a crash inside `index()` (after `extract`/`chunk` checkpoint) resumes
   without re-running the earlier steps — exactly the work the current worker loses and redoes.

The PoC is reversible by construction: `dbos` is isolated in `spikes/dbos_spike/requirements.txt`
(not the repo root), and the test self-skips when `dbos` is absent, so main CI is unaffected.

### Recommendation note (not a decision)

Lean **Option 1** — pilot DBOS Transact as the durable-execution layer for **async ingest
only**, reversibly:

- **Adopt for the worker, not the world** (D1/D4): replace `IngestWorker`'s in-memory queue +
  hand-rolled retries with a DBOS durable workflow + durable queue; leave the API contract and
  ArcadeDB untouched.
- **SQLite in dev, Postgres in prod** (D2): zero new infra locally; provision a small Postgres
  for the DBOS *system DB only* when going multi-instance. Note this is a new datastore to
  operate *beside* ArcadeDB.
- **Keep the bet reversible** (D4): wire DBOS behind the existing worker interface + a config
  flag so it can be removed without touching routes — mirroring how the UDA keeps engine
  choices additive.
- **Promotion gate** (D5/D6): graduate from spike to a Story only with (a) a Postgres
  system-DB story for prod, (b) **idempotent step bodies** (steps are at-least-once), and (c)
  the cockpit wired to DBOS `list/cancel/fork` for operational visibility.
- **Don't over-reach** (D2): revisit **Option 2 / Temporal** only if ingest later coordinates
  across ≥3 services with heavy fan-out — not now. Keep **Option 4 / dlt** as the complementary
  bulk-load path, not a replacement.

Avoid **Option 3** (status quo): it leaves a real, present data-loss/rework hole on every
restart.

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | `app/jobs.py` ingest worker becomes a durable workflow; new Postgres system DB in prod; job-status endpoints expose `list/cancel/resume` |
| middle-core | nickpclarke/middle-core | consumes job-status/progress for agent-surfaced ingest progress |
| frontend-core | nickpclarke/frontend-core | CopilotKit Phase 2 ingest **progress card** binds to the job-status surface |
| (infra) | hub templates | optional small Postgres for the DBOS system DB in the prod deployment profile (ADR-015) |

## Pros and Cons of the Options

### Option 1 — DBOS Transact in-process (recommended)
**Pros:** closes the durability gap with no new service (D1/D2); Python-native, decorator-based
(D3); built-in durable queues + step retries + scheduling replace hand-rolled code;
`list/cancel/fork` give the cockpit real levers (D5); reversible behind the worker interface (D4).
**Cons:** a new system datastore to operate in prod (small Postgres, separate from ArcadeDB);
Python-only — would not carry to a Rust ingest path (D7); couples the ingest workflow to DBOS in
the hot path (mitigated by the interface); at-least-once step semantics to learn (D6).

### Option 2 — External orchestrator (Temporal/Hatchet/Restate/Inngest)
**Pros:** most mature at scale; cross-service fan-out, rich tooling/observability.
**Cons:** heavy ops (extra service(s) + persistence, or a managed external dependency);
over-engineered for a worker whose side effects are writes into its own datastore.

### Option 3 — Status quo (in-memory queue)
**Pros:** zero new dependency.
**Cons:** loses queued work on restart; repeats expensive steps (re-embedding); hand-rolled
retry to maintain — the gap this ADR exists to close.

### Option 4 — dlt pipeline + job-status polling
**Pros:** purpose-built for bulk source→destination loads; aligns with the UDA.
**Cons:** not a per-job step-durability mechanism; complementary to (not a substitute for)
Option 1.

## Related Decisions

- **ARC-ADR-001** — HITL decision pattern + reversible-bets / n-layer doctrine (this stays a
  reversible capability behind the worker interface).
- **ARC-ADR-009** — canonical data model: ingest normalizes into the CDM the durable steps write.
- **ARC-ADR-011** — runtime secret resolution: the DBOS Postgres system-DB DSN must resolve via
  the `akv:`/managed-identity scheme, never an env DSN in prod.
- **ARC-ADR-017** (backlog) — connector egress / SSRF: the ingest fetch step is the egress sink
  that policy governs.
- **ARC-ADR-015** (backlog) — deployment & promotion: where the optional Postgres system DB runs.
- Spike: backend-core #67 (`docs/research/0003-dbos-durable-execution.md`, `spikes/dbos_spike/`).

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | spike review (backend-core #67) | Initial Proposed draft — options + recommendation, grounded in the DBOS durable-execution spike; HITL decision pending |
