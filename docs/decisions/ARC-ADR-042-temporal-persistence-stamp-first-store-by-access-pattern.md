# ARC-ADR-042 — Temporal Persistence: Stamp First, Store by Access Pattern (no new time-series engine)

| Field | Value |
|---|---|
| ID | ARC-ADR-042 |
| Status | Accepted |
| Date | 2026-05-30 |
| Deciders | Hub owner (Nicky Clarke) — convened a five-seat architecture panel; accepted 2026-05-30 |
| Supersedes | — |
| Superseded by | — |
| Tags | time-series, bitemporal, hlc, postgres, arcadedb, timescale, dbos, jetstream, prometheus, data-vault, pace-layering, persistence, yagni |

---

## Context and Problem Statement

ARC-ADR-038 (Unified Process & Time, *Proposed*) introduced a canonical **temporal envelope** (five axes + a Hybrid Logical Clock) but it is still **reference code** — `tools/temporal/hlc.py` + a JSON schema — with **per-layer wiring pending** (`docs/contracts.md`: "proposed … per-layer wiring pending"). That raised a natural question from the hub owner:

> *"Have we fully utilized either the Postgres time-series or the ArcadeDB time-series database, now that we have a time standard?"*

An audit answered plainly: **no — neither is used.** ArcadeDB has **zero** time-series-bucket DDL (the one RT5 spike used regular vertices/documents with bitemporal *fields*); Postgres runs only a bare `dbos_system` DB with an empty migration tree; TimescaleDB / hypertables / Apache AGE are absent; DBOS (ARC-ADR-018) is *Proposed* and **blocked on "the Postgres system-DB story."** The time standard meant to make a time-series store meaningful is itself not wired.

Worse, two accepted/proposed decisions now imply **different homes** for time data: ARC-ADR-041 (pace layering) floats **Postgres + Apache AGE** as the fast-layer substrate, while the RT5 pinning line + ARC-ADR-016 imply the bitemporal ledger lives in **ArcadeDB** alongside the relators it is edge-connected to.

The decision: **where does time-ordered / time-series data live, and is a dedicated time-series engine warranted now that there is a time standard?** Because this adds (or refuses) a stateful store — a hard-to-reverse, fleet-shaping move — the hub owner convened a **five-seat adversarial panel** rather than a single recommendation.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **A time standard decouples *order* from *storage*.** Once the HLC rides in the envelope, ordering no longer depends on which store holds the bytes — so the store choice becomes a cheap two-way door, not an urgent one. |
| D2 | **"Time" is not one thing.** At least three semantically distinct data classes are being conflated (ops telemetry, the bitemporal semantic ledger, value/drift telemetry); conflating even two into one undifferentiated timestamp column is a modeling bug no engine fixes retroactively. |
| D3 | **Earned surface (ARC-ADR-023).** Every stateful store is backup/HA/upgrade/monitoring surface. Pre-product, a new store must be *earned* by a measured need, not anticipated. |
| D4 | **Congruence-first (ARC-ADR-041).** "The database proves nothing about meaning; do not let storage shape truth." Choosing a store for its query features and letting that reshape the data model is the congruence violation. |
| D5 | **Bitemporal correctness (ARC-ADR-026 / ARC-ADR-016).** Valid time and transaction time are distinct facts; the ledger is append-only, closed by `superseded_at`, never `UPDATE`d. This is store-independent and inviolable. |
| D6 | **Ordering must be correct from row one.** Persisting before the HLC seam is wired stamps rows with skew-prone wall-clock time and can invert causation permanently — unfixable without mutating an append-only ledger. |

## The five-seat panel

| Seat | Agent | Charge | Verdict (one line) |
|---|---|---|---|
| Postgres / Timescale advocate | `postgres-pro` | Steelman Postgres+Timescale(+DBOS) as the time home | Postgres for the ledger (tstzrange + GiST); Timescale *deferred*; ArcadeDB gets one-way projections. Conf: med-high |
| ArcadeDB consolidation advocate | `database-administrator` | Steelman one multi-model engine | Ledger as ArcadeDB vertices+bitemporal fields (PIN-S2); TS buckets YAGNI; Postgres stays DBOS-only. Conf: med-high |
| Data-flow realist | `data-engineer` | Right-size / YAGNI | **Add nothing now.** Three classes, three existing homes. Instrument first. Conf: high (nothing-new) |
| Macro referee | `architect-reviewer` | Store-count, tiering, reversibility | **It's a stamping decision, not a store decision.** Stamp-first; no new store; one-writer-of-the-envelope invariant. Conf: high |
| Bitemporal-correctness lens | `data-vault-architect` | Temporal semantics / Data Vault | Model first, store last; **wire HLC before first persist**; append-only invariant is sacred. Conf: high (model) |

## Considered Options

1. **Stamp-first; store time by access pattern across existing stores; no new TS engine** *(chosen)*. Wire the HLC seam first; the three data classes go to the stores that already own them; defer any dedicated TS engine to a measured trigger.
2. **Adopt Postgres + TimescaleDB as the time home.** Mature TS features (continuous aggregates, `time_bucket`); but Timescale is YAGNI at pre-product volume, optimized for metrics not bitemporal ledgers, and bolting it onto the DBOS system-DB fuses two tiers (ARC-ADR-023 fusion anti-pattern) on a store that hasn't cleared its own gate (ARC-ADR-018).
3. **Consolidate all time data into ArcadeDB.** One engine, no cross-store joins; but routing *ops* telemetry there duplicates the obs stack (ARC-ADR-010) and recreates the "collapse the layers" anti-pattern; ArcadeDB's TS-bucket model is its least-proven feature (bus-factor risk).
4. **Make NATS JetStream the bitemporal ledger.** It is an ordered durable log; but it has no bitemporal predicate queries, no content-addressed identity, and you must project it into a queryable store anyway — so it is the transport, not the ledger.

## Decision Outcome

**Accepted: Option 1.** The panel converged — including both vendor advocates — on a single reframe and four shared commitments.

### The reframe (unanimous)

**This was never a "time-series store" decision; it is a time-*stamping* decision.** A time standard exists to decouple order from storage. Whoever argues "now we have a time standard, so we need a TS store" has the causality backwards: once the HLC is in the envelope, the store choice is a cheap **two-way door**.

### Shared commitments

1. **Stamp first.** Wire the HLC `ISerializationClock` seam (ARC-ADR-038 §1: `SystemSerializationClock` → `HlcSerializationClock`) **before** any persistence. This is the one near-irreversible move (un-stamped events are permanent disorder) and it is cheap + already designed behind a seam.
2. **Add no dedicated TS engine** — no Timescale, no Influx, no ArcadeDB TS *buckets* — now, and only on a **measured trigger** later.
3. **Three data classes, three homes by access pattern:**

   | Class | What | Home | Why |
   |---|---|---|---|
   | **A — Ops time** | skew SLI, span latency, metrics | **OTel / Prometheus / Tempo / Loki** (ARC-ADR-010, already deployed) | This *is* a TSDB; ARC-ADR-038 §5 already routes the skew SLI here. Never a domain store. |
   | **B — Semantic bitemporal ledger** | RT5 `PinnedElement`, relators (ARC-ADR-016), valid+transaction time | **Append-only ledger behind the `IPinStore`/`ISerializationClock` seam** — engine deferred (ArcadeDB ‖ Postgres), kept reversible | The genuinely contested store; decide on a measured trigger (is relator graph-traversal the hot path?). |
   | **C — Value/drift telemetry** | ARC-ADR-041 ICEs ("note drift") | **NATS JetStream log → materialized view** | An ordered causal event log; ICEs are Information Content Entities, not domain terms. |

4. **Two invariants that bind regardless of engine:**
   - **Anti-dual-write (referee):** the envelope is written **once** by the stamping authority; each store copies **only the slice it owns** and **never back-writes** another store's slice. Seal the `recorded_at` ≠ `processed_at` leak (the pin's authoritative transaction time ≠ DBOS's per-span processing time).
   - **Append-only bitemporal (bitemporal lens):** every world-time assertion is **written once, never `UPDATE`d, closed by `superseded_at`**; valid time and transaction time are **separate column pairs, never collapsed**. Enforce with an **insert-only DB role**, not developer discipline. *Violate it once and the audit trail is unrecoverable.*

### The deferred decision + its trigger

The **Class-B ledger engine** (ArcadeDB vertices+bitemporal-fields vs plain Postgres table) is **deliberately deferred** — the panel split 2–2 with the tie-breaking seat ruling it "secondary and reversible," because the deciding question ("is graph traversal of relator-vertices the hot query path?") is **unanswerable until data flows**. The trigger to decide it (and to revisit any dedicated TS engine):

> **Instrument one counter** — enveloped events/day, split by class A/B/C — in the OTel pipeline (costs nothing). **Revisit in ~60 days or on a threshold breach:** any single class > ~50K events/day sustained, or an as-of/bitemporal query > 500ms p95, or ops downsampling outgrowing Prometheus. Until a query pattern is *failing on an existing store*, the trigger has not fired.

### Consequences

**Positive:** zero new stateful surface (ARC-ADR-023 honored); the store choice stays a two-way door (D1); ops-time stays where it already works; the contested choice is made on data, not vibes; congruence-first preserved (no store reshapes the ledger model).
**Negative / cost:** requires the discipline to wire the stamp *before* persisting (D6) and to write down the two invariants as contract rows rather than folklore; the Class-B engine question stays open (intentionally) and must be revisited on the trigger, not forgotten.

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | Wire `HlcSerializationClock` behind the existing `ISerializationClock` seam (ARC-ADR-038 §1; RT5 PIN-F1). The first concrete unblock. |
| backend-core | nickpclarke/backend-core | Owns the Class-B ledger (append-only, insert-only role) + the Class-C JetStream materialization; emits the per-class event-rate counter. |
| obs stack | hub `templates/observability` | Class-A home, unchanged (ARC-ADR-010). Add the per-class enveloped-events counter as the decision metric. |
| (cross-cutting) | docs/contracts.md | Add a contract row for the anti-dual-write invariant (one-writer / read-only-slice-copiers) and the append-only ledger invariant. |
| (agents) | hub `.claude/agents/` | `data-vault-architect` owns ledger temporal modeling; `data-engineer` the per-class instrumentation; `observability-engineer` the obs-stack counter. |

## Open Questions / Follow-ups

1. **HLC-seam wiring** — graduate ARC-ADR-038 from *Proposed* by swapping the clock seam and stamping the envelope on pins/CloudEvents/DBOS steps. *This is the load-bearing next step; everything else depends on it.*
2. **Class-B engine** — ArcadeDB vertices vs plain Postgres table, decided on the 60-day counter + the "graph-traversal hot path?" question. Ties to **ARC-ADR-041 OQ3** (fast-LPG substrate) — note it is a *graph-engine* decision with a TS aspect, not a TS-engine decision.
3. **DBOS system-DB story** — unblock ARC-ADR-018; keep that Postgres scoped to durable-step time only (do not let it absorb the analytics/ledger role — ARC-ADR-023 fusion guard).
4. **Contract rows** — write the two invariants into `docs/contracts.md` so they are enforced, not folklore.

## Related Decisions

- **[ARC-ADR-038](ARC-ADR-038-unified-process-and-time-architecture.md):** the temporal envelope + HLC — the stamp this ADR says to wire *first*.
- **[ARC-ADR-041](ARC-ADR-041-pace-layered-projection-and-graduation.md):** pace layering — Class-C telemetry are ICEs in the fast layer; OQ3 (fast-LPG substrate) is the same open store question as Class-B.
- **[ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md):** relator-vertex + bitemporal/PROV on the relator, versioned by append — the ledger's shape.
- **[ARC-ADR-026](ARC-ADR-026-data-vault-2-1-methodology.md):** raw-vs-business + bitemporal satellites — the ledger is a raw-vault satellite; as-of views (PIT/bridge) are business-vault, derived.
- **[ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md):** earned surface + the fusion-image anti-pattern (why not to bolt Timescale onto the DBOS system-DB).
- **[ARC-ADR-018](ARC-ADR-018-async-job-execution-model.md):** DBOS — Class-A/durable-step time; blocked on the Postgres system-DB story.
- **[ARC-ADR-010](ARC-ADR-010-observability-standard.md):** OTel/Prometheus — the Class-A home.
- **Labs:** *Temporal Persistence — Stamp First, Store by Access Pattern*; *Pace-Layering and the Dreaming Ontology*; *Ontology-Pipeline*.

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-30 | Claude Code (assisted) | Initial — five-seat panel (postgres-pro / database-administrator / data-engineer / architect-reviewer / data-vault-architect). Accepted: stamp-first, store-by-access-pattern, no new TS engine; Class-B engine deferred to a measured trigger. |
