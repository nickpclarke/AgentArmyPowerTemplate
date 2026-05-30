---
tags: [vision, platform, data, time, bitemporal, persistence]
track: vision
---
# Temporal Persistence — Stamp First, Store by Access Pattern

> **Status:** decision record companion — the narrative behind [ARC-ADR-042](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-042-temporal-persistence-stamp-first-store-by-access-pattern.md). Captures the five-seat panel that answered *"have we used either time-series DB now that we have a time standard?"*

> **One-line thesis** — A time standard exists to **decouple order from storage**. So the answer to "which time-series store?" is: **stamp the order first (HLC), and the store becomes a cheap two-way door you can defer.** "Now we have a time standard, so we need a TS store" gets the causality backwards.

## The question that started it

*Have we fully utilized either the Postgres time-series or the ArcadeDB time-series database, now that we have a time standard?* An audit said **no — neither is used**: zero ArcadeDB time-series-bucket DDL, a bare `dbos_system` Postgres with an empty migration tree, no Timescale, no AGE, DBOS blocked on its own system-DB story. And the time standard ([[Pace-Layering and the Dreaming Ontology|ARC-ADR-038]]) meant to *make* a TS store meaningful is itself only reference code (`tools/temporal/hlc.py`) with wiring pending.

## The reframe (what five seats converged on)

The phrase "time-series store" smuggled in a false premise: that there is **one** time thing to store, and that having a clock means we must now buy a store for it. Both are wrong.

> **It is a time-*stamping* decision, not a time-*store* decision.** Once the HLC rides in the envelope, ordering no longer depends on which store holds the bytes — so the store choice is reversible. The standard's payoff *is* that deferral.

## "Time" is three data classes (conflating them is the bug)

| Class | What | Home | Pace-layer role |
|---|---|---|---|
| **A — Ops time** | skew SLI, span latency, container metrics | **OTel / Prometheus / Tempo / Loki** (already deployed) | infra observability — never a domain store |
| **B — Semantic bitemporal ledger** | pinned facts, relators, valid+transaction time | **append-only ledger** (engine deferred, behind a seam) | the slow layer's audit truth |
| **C — Value/drift telemetry** | "note drift and emergence" (ICEs) | **NATS JetStream log → materialized view** | the fast layer's semantic telemetry |

The worst outcome the panel feared: treating A, B, C as one "time-series problem" and buying one store that serves all three poorly. They have different lifecycles (sampled-and-short vs immutable-and-permanent vs ordered-replayable), different consistency models, and different query shapes. One store is not optimal for all three — and ops-time was never the domain stores' to hold.

## The five seats (adversarial, on purpose)

```
postgres-pro ───────────▶ Postgres+Timescale for the ledger (tstzrange+GiST); Timescale deferred
database-administrator ─▶ ArcadeDB consolidation (vertices+bitemporal fields, PIN-S2); buckets YAGNI
data-engineer ──────────▶ add NOTHING now; three classes → three existing homes; instrument first
architect-reviewer ─────▶ it's a STAMPING decision; no new store; one-writer-of-the-envelope invariant
data-vault-architect ───▶ model first, store last; wire HLC BEFORE first persist; append-only is sacred
```

Consensus (incl. both vendor advocates): **stamp first · add no TS engine · ops-time stays in Prometheus · drift-events are a JetStream log.** The only real split was the **Class-B ledger engine** (ArcadeDB ‖ Postgres) — and the tie-breaking seat ruled it *secondary and reversible*, because the deciding question is unanswerable until data flows.

## Two invariants that bind regardless of engine

> [!warning] Anti-dual-write (the referee's seam)
> The envelope is written **once** by the stamping authority; each store copies **only the slice it owns** and **never back-writes** another store's slice. The leak to seal: `recorded_at` (the pin's authoritative transaction time) ≠ `processed_at` (DBOS's per-span processing time) — they look alike and tempt a dual-write. One writer, N read-only slice-copiers.

> [!warning] Append-only bitemporal (the Data Vault seat's invariant)
> Every world-time assertion is **written once, never `UPDATE`d, closed by `superseded_at`**; valid time and transaction time are **separate column pairs, never collapsed into one timestamp**. Enforce with an **insert-only DB role**, not developer discipline. The named nightmares: *monotemporal collapse* (one `timestamp` column → "what did we believe at T?" is lost) and *ordering by wall-clock under skew* (causation silently inverted).

## Why stamp first is non-negotiable

Persist before the HLC seam is wired and you stamp rows with skew-prone wall-clock `recorded_at` from many containers, then order by it. Two causally-related events (A causes B) can land with `A.recorded_at > B.recorded_at` — the ledger records inverted causal order. You **cannot** fix this retroactively without mutating an append-only ledger (forbidden). The HLC seam (`ISerializationClock`) is cheap, designed, and reversible-per-impl; deferring the *store* is fine, deferring the *stamp* is the one-way door.

## Make it data-driven (the one metric)

> **Instrument one counter** — enveloped events/day, split A/B/C — in the OTel pipeline. **Revisit in ~60 days or on breach:** any class > ~50K events/day sustained, or a bitemporal as-of query > 500ms p95, or ops downsampling outgrowing Prometheus. Until a query pattern is *failing on an existing store*, the dedicated-TS-engine trigger has not fired.

The failure mode this avoids: **building the TS store nobody ingests into** — a stateful surface sitting empty for months while the stamp stays unwired.

## So: have we used the time-series DBs?

**No — and correctly so.** The standard's job is to make that store choice *deferrable*, not urgent. The real unbuilt work is **wiring the stamp**, not picking a store. Sequence: wire HLC → persist the ledger append-only behind a seam → keep ops in Prometheus, drift in JetStream → decide the ledger engine on the 60-day counter.

## Related

- [[Pace-Layering and the Dreaming Ontology]] — the fast/slow frame; Class-C drift telemetry are the fast layer's ICEs.
- [[Ontology-Pipeline]] — the bitemporal, append-only, congruence-first spine the ledger serves.
- [[Evidence as a Primitive]] — why the ledger is append-only and audit-bound.
- ADRs: [ARC-ADR-042](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-042-temporal-persistence-stamp-first-store-by-access-pattern.md) (this decision), [ARC-ADR-038](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-038-unified-process-and-time-architecture.md) (the stamp), [ARC-ADR-041](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-041-pace-layered-projection-and-graduation.md) (pace layering), [ARC-ADR-026](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-026-data-vault-2-1-methodology.md) (raw-vs-business, bitemporal satellites), [ARC-ADR-023](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-023-container-tiering-strategy.md) (earned surface).
