# ARC-ADR-038 — Unified Process & Time Architecture: an HLC temporal envelope + DBOS-durable BPMN/CACAO over the event bus

| Field | Value |
|---|---|
| ID | ARC-ADR-038 |
| Status | Proposed |
| Date | 2026-05-30 |
| Deciders | Hub owner (Nicky Clarke) — direction chosen 2026-05-30 (capstone scope; DBOS-as-process-runtime + HLC envelope). Graduation to Accepted gated on ARC-ADR-018 adoption + the Confirmation checks below. |
| Supersedes | — |
| Superseded by | — |
| Tags | process, time, bitemporal, hlc, clock-sync, ntp, chrony, ptp, mesh, multi-region, horizontal-scaling, supercluster, leaf-node, skew-sli, aca, dbos, durable-execution, bpmn, cacao, bpel, event-bus, cloudevents, nats, agent-gateway, ontology, saga, scheduling, cron, capstone |

---

## Context and Problem Statement

The fleet has, as **separate accepted/proposed decisions**, every substrate of an event-driven, model-driven, durable process architecture — but nothing binds them into one system:

- **Durable execution** — [ARC-ADR-018](ARC-ADR-018-async-job-execution-model.md) pilots **DBOS Transact** (durable workflows, durable queues, step checkpoint/replay, **scheduled workflows**, `list/cancel/resume/fork`) — but **scoped to async ingest only**.
- **Event bus + webhooks** — [ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md): **NATS JetStream + CloudEvents v1.0** with HTTP↔bus bridges (`webhook-receiver.py` in, `nats-relay.py` out, HMAC + DLQ).
- **Process execution** — [ARC-ADR-031](ARC-ADR-031-automated-runbook-orchestration.md) **(Accepted)**: **BPMN 2.0 + OASIS CACAO 2.0** parsed to one IR, run by one ~400-line kernel, NATS-triggered, function-tier.
- **Bitemporal object store** — [RT5 "Ontology-Grade Persistence"](../release-trains/RT5-ontology-grade-persistence.md): objects pinned as immutable, content-addressed, **bitemporal** records (`valid_from/valid_to/recorded_at/superseded_at`) with an injected `ISerializationClock`; plus analytics-side load-dates in [ARC-ADR-026](ARC-ADR-026-data-vault-2-1-methodology.md).
- **The agentic API** — [ARC-ADR-028](ARC-ADR-028-agent-gateway-a2a-mcp.md): the **Agent Gateway** normalizing **A2A + MCP** behind one REST/OpenAPI surface, with an async task lifecycle (`POST …/tasks` → `202 + Location` → poll).
- **Process-aware ontology** — the [ontology IR](../../templates/ontology-project/ontology.ir.schema.json) already carries UFO `event` and `situation` **perdurant** stereotypes and a `urn:agentarmy:mc:event:{stateMachine}/{objectId}/{trigger}` IRI scheme ([ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md), [ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md), [ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md)).

Four binding gaps remain:

1. **No cross-container clock discipline.** Four time axes exist in pieces, but **causal order across containers does not**. Under wall-clock skew and out-of-order bus delivery, the time the frontend stamps, the CloudEvent `time`, the pin's `recorded_at`, and the Data Vault load-date can disagree and even invert causally. This is the operator's stated unease — *"ensure data time records and object time and frontend everything is synched."*
2. **No durable home for process state.** ARC-ADR-031 **explicitly defers** durable long-running waits (Open Q1) and timer-driven scheduling — so a runbook timer or a multi-day `intermediateCatchEvent` cannot survive a restart today.
3. **The ontology's process knowledge compiles to nothing executable.** ARC-ADR-031 Open Q5 asks whether the model's process/playbook artifacts should *compile to* BPMN/CACAO the kernel runs. Unanswered.
4. **Nothing names how a process step invokes the agentic API.** The operator's *"BPEL webhook driver for orchestrating across our generalized agentic API"* has no defined seam.

**Decision: define the binding layer — a single temporal contract and a single durable process runtime — that fuses these substrates and answers ARC-ADR-031's open questions.**

> **Terminology — BPEL → BPMN.** WS-BPEL 2.0 is the SOAP/WS-\* era process language (`invoke`/`receive`/`reply`/`wait`/`pick`/`flow`); its open-source tooling is effectively dormant. Its modern executable successor is **BPMN 2.0**, already chosen in ARC-ADR-031. A BPMN **service task** over the event bus/Agent Gateway *is* a BPEL `<invoke>`; a **message catch event** *is* `<receive>`; a **timer event** *is* `<wait>`. This ADR adopts no BPEL; it points the accepted BPMN/CACAO kernel at the existing agentic API and makes its waits durable.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **One temporal contract** across frontend, bus, durable runtime, and store — the four time axes plus a causal-order axis, carried in one envelope. |
| D2 | **Durable, resumable processes** — waits, timers, cron, and nested sub-processes survive crash/restart; completed steps never re-run (idempotent, at-least-once until checkpointed — inherits ARC-ADR-018 D1/D6). |
| D3 | **Reuse, don't reinvent** — bind existing decisions; no new heavyweight engine (honors ARC-ADR-018 D2 minimal-ops and ARC-ADR-031 D7 supply-chain minimalism). |
| D4 | **Model-driven** — process is first-class in the ontology IR and compiles to the executable format; the object model is process-aware (answers ARC-ADR-031 Q5). |
| D5 | **Reversibility** (ARC-ADR-001) — clock behind `ISerializationClock`, durable runtime behind the worker/kernel interface; either swappable without touching routes. |
| D6 | **Standards over bespoke** — BPMN 2.0 + CACAO 2.0, CloudEvents v1.0, PROV-O + OWL-Time, and HLC (a published algorithm) — not a proprietary clock or DSL. |
| D7 | **Observable** (ARC-ADR-010) — a process instance **is** an OTel trace; span order derives from the HLC; `correlation_id`/`causation_id` thread the saga across nesting. |
| D8 | **Security posture preserved** — server-authoritative time (clients never order events, mirroring ARC-ADR-008 thread-key handling); the safe-executor + HITL gates (ARC-ADR-031 D5, ARC-ADR-006) stay in force when processes drive real actions. |

## Considered Options

### Option A — Unified spine: HLC temporal envelope + DBOS-durable BPMN/CACAO kernel invoking the Agent Gateway, with process compiled from the ontology IR *(recommended; chosen)*

Bind the existing substrates with two new contracts and one new seam:
- a **canonical temporal envelope** (four time axes + HLC) on every CloudEvent, pin, and workflow step;
- **DBOS as the durable process runtime** the ARC-ADR-031 kernel executes inside;
- a **process projection** in the ontology IR that the forge compiles to BPMN/CACAO, whose **service tasks invoke the Agent Gateway**.

No new engine, no new language — every part is an existing ADR plus the glue.

### Option B — Point solutions, left unbound

Keep each ADR independent: add timer state via JetStream KV inside the kernel; keep per-container wall-clock timestamps; reference BPMN files loosely from the model. **Cheapest, but the four gaps remain** — causal order is still undefined, process state is bespoke per-image, and the ontology stays disconnected from execution.

### Option C — Heavyweight external orchestrator + clock service

Adopt Temporal/Zeebe for processes and a PTP/NTP appliance for time. Rejected on the same grounds ARC-ADR-018 (D2) and ARC-ADR-031 (Option C, D7) already rejected heavyweight orchestration: a Raft broker cluster and a managed time service are the opposite of the small, isolated, cost-conscious posture.

### Option D — Vector clocks / CRDTs + a custom saga engine

Maximum rigor for concurrent multi-writer conflict resolution. Over-built for the current single-writer-per-object reality; revisit only if true concurrent cross-container edits to the same object emerge.

## Decision Outcome

**Chosen: Option A.** Three sub-decisions, made by the hub owner 2026-05-30:

### 1. Time — Hybrid Logical Clock + a canonical temporal envelope

Wall clocks are **never** synchronized to zero skew; instead **NTP/chrony is the physical baseline and an HLC is the ordering contract.** Five axes, each with a home:

| Axis | Field | Home | Status |
|---|---|---|---|
| Valid time (true in the world) | `valid_from` / `valid_to` | pin store / IR relator `temporal` | have |
| Transaction time (system recorded it) | `recorded_at` / `superseded_at` | pin store ledger | have |
| Event/occurrence time (happened at source) | `event_time` (CloudEvents `time`) | bus | partial |
| Processing time (consumer handled it) | `processed_at` | consumer span | new |
| **Causal order (happens-before)** | **`hlc`** | **all of the above** | **new — the gap** |

The **canonical temporal envelope** travels on every CloudEvent (as CloudEvents v1.0 **extension attributes**), lands on every `PinnedElement`, and tags every DBOS workflow step:

```
{ event_time, recorded_at, hlc, valid_from?, valid_to?,
  correlation_id,   // root process-instance id (the saga key)
  causation_id }    // the immediate parent event/step id
```

- **HLC** = `(physical_time, logical_counter)`; merge on receive as `hlc = max(local, received_physical, local_physical) (+1 to the counter on ties)`. Stays within NTP-distance of wall time, guarantees monotonicity, encodes causality across containers without tight sync.
- **Seam:** replace `SystemSerializationClock` with an `HlcSerializationClock` behind the existing `ISerializationClock` (RT5 PIN-F1) — reversible per D5. `recorded_at` stays human/transaction time; the `hlc` is the orderable causal stamp.
- **Frontend is never authoritative for order** (D8): the BFF/middle-core stamps the envelope on the browser's behalf; the client clock is display-only (user timezone), mirroring ARC-ADR-008's server-derived keys.

### 2. Runtime — promote DBOS to the platform durable process runtime

Extend ARC-ADR-018 from *ingest-only* to *the durable spine the ARC-ADR-031 kernel runs inside* — **answering ARC-ADR-031 Open Q1**:

- BPMN **timer / `intermediateCatchEvent`** → DBOS durable `sleep` / `recv` (survives restart).
- BPMN **call-activity** / CACAO **`playbook-action`** → kernel `CALL` node → **DBOS child workflow** (the *recursive nesting*).
- BPMN **loop / multi-instance** → DBOS step loops.
- **Durable cron** = DBOS **scheduled workflows** (exactly once per tick across restart) — kept distinct from *infra cron* (GitHub Actions / `fleet-heartbeat`), which stays for repo/contract upkeep.
- Cost (per ARC-ADR-018): a small **Postgres system DB** beside ArcadeDB; its DSN resolves via the `akv:`/workload-identity scheme ([ARC-ADR-011](ARC-ADR-011-runtime-secret-resolution-workload-identity.md)), never a plain env DSN.

### 3. Model — a process projection in the ontology IR that compiles to BPMN/CACAO

**Answering ARC-ADR-031 Open Q5.** Add a process dimension to the [ontology IR](../../templates/ontology-project/ontology.ir.schema.json) using the already-present `event` / `situation` perdurant stereotypes plus an explicit state-machine relating the **endurants** (objects) a process transforms — so the object model is *process-aware*. The forge emits a `bpmn` / `cacao` projection (alongside `gufo`/`shacl`/`csharp`/`arcadedb`); process **instances** are pinned as bitemporal **perdurant** records (RT5), carrying the same temporal envelope as everything else.

### 4. Invoke — BPMN service-task → Agent Gateway adapter

The seam for *"orchestrating across the generalized agentic API"*: a BPMN **service task** (or CACAO `http-api` command) calls the **Agent Gateway** (ARC-ADR-028) — `POST /a2a/v1/agents/{slug}/tasks` (async + poll) for long-running, `/invoke` for synchronous. Message start/catch events bind to the event bus (ARC-ADR-022). The Gateway's existing async task lifecycle *is* the durable invoke primitive; the kernel correlates the result by `correlation_id`.

### 5. Mesh — physical time-sync across a horizontally-scaling topology

The HLC (decision 1) supplies *order*; it rests on a *physical* baseline that must hold as the fleet scales from a few containers to a mesh of Azure Container Apps (ACA) replicas, a heterogeneous edge (the local **OmniDesk** Docker fleet), and — on the horizon — multiple Azure regions ([HEADLESS_FOUNDRY vision](../../planning/ideas/HEADLESS_FOUNDRY_ORCHESTRATOR.md)). The physical layer is **platform-managed and monitored, not self-run**, and the topology is a **tiered tree, not a flat fabric**. Compute is Azure-only ([ARC-ADR-025](ARC-ADR-025-gcp-scope-narrowing.md)); there is no multi-cloud compute mesh.

**Posture by tier:**

| Tier | Time source | Who runs it | Expected ε (skew) |
|---|---|---|---|
| Azure Container Apps (compute) | Azure host clock (PTP `/dev/ptp_hyperv` → host chrony → MS GPS stratum-1) | Azure — **you cannot run `chronyd` in ACA** | sub-ms to host; low-ms region-wide |
| Azure VMs / AKS (if/when owned) | chrony → Azure PTP refclock | us, where we own the host | sub-ms |
| OmniDesk / local edge | Windows W32Time | the operator's host | tens of ms — the loosest link |
| Cross-region (future) | each region to its own stratum, bridged by the bus | Azure per region | gateway-latency bound |

**Rules:**

- **Consume, don't run** (managed compute): ACA inherits an already-disciplined host clock; we never ship a time daemon in an app container. We *measure* skew rather than *enforce* it.
- **Skew is an SLI** ([ARC-ADR-010](ARC-ADR-010-observability-standard.md)): on every bus receive, compare the envelope HLC's physical component to the local wall clock and export the delta (`tools/temporal/hlc.py::skew_ms`). ε exceeding the tier's bound is the alert — the only operational "time sync" signal we need. The drift-guard is the runtime backstop that refuses an implausible clock.
- **ε is region/link-aware:** intra-region tight, edge (W32Time) and cross-region loose. `update()` takes a per-link `max_drift_ms` so the OmniDesk leaf and future gateway links carry a looser bound than the intra-region default.
- **The bus is the causality mesh** ([ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md)): horizontal scale = NATS **JetStream cluster** within a region, **leaf nodes** for the edge (OmniDesk attaches as a leaf), **gateway/supercluster** across regions later. HLC is **gossip-free**, so adding replicas / leaves / regions extends the causal mesh with **zero clock-coordination overhead** — no central authority (a SPOF + latency tax), no O(N²) gossip.
- **Durable execution is regional; causal order is global:** a DBOS process instance lives in one region's Postgres system-DB; cross-region/edge coordination is via envelope-bearing CloudEvents, never cross-region Postgres consensus.

**Horizon (chosen):** build **single-region + the OmniDesk leaf now**, and keep the envelope, HLC bounds, and NATS leaf/gateway design **multi-region-ready** — nothing precludes superclusters later. Multi-region is *designed-for, not built-yet*; it re-opens as a concrete decision when a second region earns its cost (per ADR-025's single-cloud discipline).

### v1 scope

**In:** the temporal-envelope spec + `HlcSerializationClock` seam; the CloudEvents extension attributes; run-kernel-inside-DBOS for durable waits/timers/cron/nesting; the BPMN-service-task→Agent-Gateway adapter (async task + poll); pinning process instances as perdurants; OTel trace = process instance with HLC-ordered spans; a forge `bpmn`/`cacao` projection from an IR process section; the per-tier time posture (platform-managed on ACA) with a **skew SLI** + **region/link-aware drift bound**, and the OmniDesk **leaf node** on the bus; `docs/contracts.md` rows + mkdocs nav.

**Out (deferred):** real `ssh`/`bash` execution (stays ARC-ADR-031 safe-posture + ARC-ADR-006 HITL); full FEEL (BPMN) / STIX-pattern (CACAO) condition grammars (inherit ARC-ADR-031 Q4); vector-clock concurrent-write conflict resolution; PTP/GPS hardware time + TrueTime-style commit-wait; the **multi-region mesh build** (NATS superclusters/gateways, per-region DBOS stores) — designed-for, not built; UUIDv7/ULID event IDs (see Open Questions).

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| (cross-cutting) | hub | This ADR; temporal-envelope contract; `docs/contracts.md` rows ("temporal envelope", "process runtime"); mkdocs nav. |
| Function tier | hub `templates/runbook-orchestrator-image/` | Kernel gains a DBOS execution mode + a service-task→Agent-Gateway executor; CloudEvents carry the envelope. |
| Function tier | hub `templates/event-bridge-image/` | Bridges propagate the temporal envelope (extension attrs) inbound and outbound. |
| Function tier | hub `templates/forge-image/` | New `bpmn`/`cacao` projection from the IR process section. |
| Application | nickpclarke/middle-core | `HlcSerializationClock` behind `ISerializationClock`; pins carry `hlc`; process instances pinned as perdurants; CopilotKit surfaces process/saga status. |
| Application | nickpclarke/backend-core | DBOS promoted from ingest to general process runtime; Agent Gateway is the service-task target. |
| Application | nickpclarke/frontend-core | Time display in user TZ only; never client-ordered; process/saga progress card binds to status. |
| Platform | hub deployment profile | Small Postgres for the DBOS system DB (ARC-ADR-011 secrets, ARC-ADR-015 placement); time is **platform-managed** (ACA inherits the Azure host clock — no in-container chronyd), with skew exported as an SLI and a region/link-aware drift bound. |
| Edge / mesh | OmniDesk + NATS | The local Docker fleet attaches as a NATS **leaf node**; an intra-region JetStream cluster + (future) gateway/supercluster carry the temporal envelope. The W32Time edge gets a looser drift bound. |

## Pros and Cons of the Options

### Option A — unified spine (chosen)
**Pros:** binds six existing decisions with two contracts + one seam, no new engine (D3); HLC gives causal order despite skew (D1); DBOS closes the durable-wait gap and gives durable cron + nesting (D2, answers ADR-031 Q1); ontology becomes executable (D4, answers ADR-031 Q5); everything reversible behind seams (D5); one envelope = one OTel/saga story (D7).
**Cons:** promotes DBOS (a new prod datastore to operate, per ADR-018) ahead of its own graduation; we own HLC correctness and the envelope's propagation discipline; touches all three spokes.

### Option B — point solutions, unbound
**Pros:** cheapest; nothing new to operate.
**Cons:** the four gaps persist — no causal order, bespoke per-image wait state, ontology disconnected from execution; technical debt compounds as more processes appear.

### Option C — heavyweight orchestrator + clock service
**Pros:** mature durable orchestration; tight physical time.
**Cons:** fails the isolation/footprint/supply-chain drivers already settled in ARC-ADR-018 and ARC-ADR-031.

### Option D — vector clocks / CRDT + custom saga engine
**Pros:** strongest concurrency guarantees.
**Cons:** over-built for single-writer-per-object; large surface to own.

## Confirmation

This ADR graduates to **Accepted** when:

- [ ] An `HlcSerializationClock` stamps every pin and CloudEvent; a property test shows the `hlc` is **monotonic non-decreasing** across simulated skew + out-of-order delivery, and orders two causally-related events correctly when their wall clocks invert.
- [ ] A BPMN process with a timer **and** a call-activity runs to completion **across a forced restart** with **zero completed steps re-run** (the ARC-ADR-018 spike proof, extended to the kernel).
- [ ] A DBOS **scheduled workflow** fires **exactly once per tick** across a restart.
- [ ] A BPMN **service task** invokes a real **Agent Gateway** task and the result correlates by `correlation_id`.
- [ ] The forge emits **BPMN/CACAO** from an IR process projection; the runbook-orchestrator doctor runs the emitted artifact end-to-end (event → run → `fleet.runbook.completed`).
- [ ] A process instance appears as a single **OTel trace** with HLC-ordered spans across the nesting.
- [ ] **Skew SLI** is exported on bus receive and alerts when ε exceeds the tier bound; the region/link-aware drift-guard rejects an edge clock beyond its (looser) bound.
- [ ] An event crossing the OmniDesk **leaf node** (loose W32Time clock) still orders correctly by HLC relative to region-originated events.
- [ ] `docs/contracts.md` + mkdocs nav updated.

## Open Questions

1. **Where does the frontend hop get stamped** — BFF or middle-core? (Lean middle-core/BFF, server-authoritative per D8.)
2. **Kernel-inside-DBOS granularity** — does the whole kernel run as one DBOS workflow, or does DBOS drive it node-by-node (finer checkpoints, more overhead)?
3. **DBOS system-DB placement/HA in prod** — ties the ARC-ADR-018 promotion gate and ARC-ADR-015 deployment.
4. **Time-sortable event IDs** — add UUIDv7/ULID for bus message keys alongside the content-addressed identity hashes (which are deliberately *not* time-sortable)?
5. **Condition grammar growth** — inherit ARC-ADR-031 Q4 (FEEL/STIX subset → vetted library?).
6. **Real-exec enablement** — inherit ARC-ADR-031 Q2/Q6 when a process drives destructive actions (allowlist + HITL + signature verification).
7. **Reasoner visibility** — does the ARC-ADR-019 reasoning layer see process/perdurant assertions, enabling inference over process state?
8. **Multi-region build trigger** — what concretely justifies a second region + NATS supercluster (latency SLO? data residency? availability target)? Until then it stays designed-for-not-built.
9. **Edge-originated durability** — the OmniDesk leaf has no DBOS store; where does a process *started at the edge* durably land — forwarded to a region's system-DB over the bus, or queued locally until reconnect?
10. **Edge clock bound** — what `max_drift_ms` do we accept for the W32Time edge link before rejecting its events as too skewed (tighten W32Time config, or accept tens-of-ms)?

## Related Decisions

- [ARC-ADR-001](ARC-ADR-001-hitl-decision-point-pattern.md) / [ARC-ADR-006](ARC-ADR-006-hitl-destructive-ops.md) — HITL + destructive-ops gates for `manual`/real-exec steps.
- [ARC-ADR-002](ARC-ADR-002-jwt-forwarding-auth-contract.md) / [ARC-ADR-008](ARC-ADR-008-agent-memory-store.md) — server-authoritative principal/state; the same discipline applied to time.
- [ARC-ADR-010](ARC-ADR-010-observability-standard.md) — process instance = OTel trace; HLC-ordered spans.
- [ARC-ADR-011](ARC-ADR-011-runtime-secret-resolution-workload-identity.md) — DBOS system-DB DSN resolution.
- [ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md) — relator/hyperedge model the process projection extends.
- [ARC-ADR-018](ARC-ADR-018-async-job-execution-model.md) — DBOS, promoted here from ingest to the durable process runtime.
- [ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md) — reasoning over (now) process assertions.
- [ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md) — NATS JetStream + CloudEvents, the trigger + envelope transport; its cluster/leaf/gateway topology is the causality mesh.
- [ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md) — container tiering; the mesh tiers (ACA app / edge leaf / platform) map onto it.
- [ARC-ADR-025](ARC-ADR-025-gcp-scope-narrowing.md) — Azure-only compute; the mesh is single-cloud (no multi-cloud compute fabric).
- [ARC-ADR-026](ARC-ADR-026-data-vault-2-1-methodology.md) — analytics-side load-dates aligned to the same axes.
- [ARC-ADR-028](ARC-ADR-028-agent-gateway-a2a-mcp.md) — the Agent Gateway, the service-task invoke target.
- [ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md) / [ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md) — the forge + ingestion pipeline that gain the BPMN/CACAO projection.
- [ARC-ADR-031](ARC-ADR-031-automated-runbook-orchestration.md) — the BPMN/CACAO kernel; **this ADR answers its Open Q1 (durable waits) and Q5 (ontology → executable process).**
- [RT5 — Ontology-Grade Persistence](../release-trains/RT5-ontology-grade-persistence.md) — the bitemporal pin store + `ISerializationClock` seam the HLC plugs into.
- Labs: [Ontology-Pipeline](../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md), [Reification-and-Hyperedges](../../obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md).
- Vision: [HEADLESS_FOUNDRY_ORCHESTRATOR](../../planning/ideas/HEADLESS_FOUNDRY_ORCHESTRATOR.md) — the multi-region orchestration horizon this design stays ready for.

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-30 | Claude Code (assisted) | Initial Proposed capstone — binds ARC-ADR-018/022/026/028/031 + RT5 via an HLC temporal envelope and DBOS-as-process-runtime; records the hub owner's three forks (HLC+envelope, promote DBOS, process-in-ontology); answers ARC-ADR-031 Open Q1 + Q5. |
| 0.2 | 2026-05-30 | Claude Code (assisted) | Added §5 (physical time-sync & horizontally-scaling mesh topology): platform-managed time per tier (ACA consumes Azure host clock; chrony only where we own the host; W32Time edge), skew SLI + region/link-aware drift bound, NATS cluster/leaf/gateway as the gossip-free causality mesh, durable-execution-regional / causal-order-global, single-region + OmniDesk leaf now and multi-region-ready. Hub-owner forks chosen 2026-05-30. |
