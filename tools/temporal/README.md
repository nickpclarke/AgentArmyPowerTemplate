# tools/temporal — the fleet's clock contract

Reference implementation of the **canonical temporal envelope** and the **Hybrid Logical
Clock (HLC)** that bind the platform's process-and-time architecture together.

Governing decision: [ARC-ADR-038](../../docs/decisions/ARC-ADR-038-unified-process-and-time-architecture.md).

## Why this exists

The platform is **bitemporal** (valid time + transaction time, RT5 pinning) but it was not
**synchronized**: the frontend, the event bus, the durable runtime, and the object store
each touched the clock independently, so under wall-clock skew and out-of-order delivery
their stamps could disagree — even invert causally. You **cannot** sync wall clocks to zero
(NTP gets ~ms, never 0), and you don't need to.

> **NTP/chrony is the physical baseline; the HLC is the ordering contract.**

## The five axes

| Axis | Field | Question it answers | Home |
|---|---|---|---|
| Valid time | `valid_from` / `valid_to` | When is the fact true *in the world*? | pin store, IR relator `temporal` |
| Transaction time | `recorded_at` | When did the *system record* it? | pin-ledger (RT5) |
| Event time | `event_time` | When did it *happen at source*? | CloudEvents `time` |
| Processing time | `processed_at` | When did *this consumer* handle it? | per-hop span |
| **Causal order** | **`hlc`** | What *happened before* what, across containers? | **everything** |

Plus the saga pair — `correlation_id` (root process instance = OTel trace) and
`causation_id` (immediate parent) — which thread the recursive nesting.

## Files

| File | What |
|---|---|
| [`temporal-envelope.schema.json`](temporal-envelope.schema.json) | The cross-cutting contract. Registered in [`docs/contracts.md`](../../docs/contracts.md). |
| [`hlc.py`](hlc.py) | Reference HLC + envelope (stdlib only). `python hlc.py` runs the self-test. |

## How each layer wires it

- **frontend-core** — display in user timezone only; **never** orders events by the client
  clock. The BFF/middle-core stamps the envelope on the browser's behalf (server-authoritative,
  mirroring [ARC-ADR-008](../../docs/decisions/ARC-ADR-008-agent-memory-store.md) thread keys).
- **middle-core** — swap `SystemSerializationClock` → `HlcSerializationClock` behind the
  existing `ISerializationClock` seam (RT5 PIN-F1). `recorded_at` stays human/transaction
  time; the `hlc` becomes the orderable causal stamp on every `PinnedElement`.
- **event-bridge / runbook-orchestrator** — every CloudEvent carries the envelope as v1.0
  **extension attributes** (`hlc`, `correlationid`, …). Bridges propagate it in and out.
- **backend-core + DBOS** — every durable workflow step is tagged with the envelope, so a
  resumed process re-enters with its causal position intact ([ARC-ADR-018](../../docs/decisions/ARC-ADR-018-async-job-execution-model.md)).

## The design knobs (your judgment, in `hlc.py`)

Two choices define the clock's safety; both are called out at the top of `hlc.py`:

1. **`MAX_DRIFT_MS`** — how far logical time may run ahead of this node's wall clock before
   we treat it as a fault (a remote node with a clock in the future would otherwise drag our
   HLC forward forever). Tighten this once chrony is enforced fleet-wide.
2. **Counter overflow / tie-break** — what happens when many events share one physical ms.
   Python ints are unbounded; the C# port must use `int64` and roll the physical ms forward
   on overflow.

## Mesh & cross-cluster time-sync (ARC-ADR-038 §5)

Time is **platform-managed and monitored, not self-run**, on a **tiered tree** — not a flat
fabric. Compute is Azure-only (ARC-ADR-025).

| Tier | Time source | Who runs it | Expected skew (ε) |
|---|---|---|---|
| Azure Container Apps | Azure host clock (PTP → host chrony → MS GPS) | Azure — **no chronyd in ACA** | sub-ms to host |
| Azure VMs / AKS | chrony → Azure PTP refclock | us (host owner) | sub-ms |
| OmniDesk / local edge | Windows W32Time | the operator | tens of ms (loosest) |
| Cross-region (future) | per-region stratum, bridged by the bus | Azure | gateway-latency bound |

- **Consume, don't run** — measure skew, don't enforce it. `skew_ms(remote, now)` on every
  bus receive is the SLI; alert when ε exceeds the tier bound.
- **Region/link-aware bound** — `update(remote, max_drift_ms=…)` lets the edge leaf and
  future gateway hops tolerate a looser ε than the tight intra-region default.
- **The bus is the causality mesh** — NATS JetStream cluster (region) + leaf nodes (edge,
  e.g. OmniDesk) + gateway/supercluster (regions, later). HLC is gossip-free, so the mesh
  scales linearly: no central clock authority, no O(N²) gossip.
- **Durable execution is regional; causal order is global** — DBOS instances live in one
  region's Postgres; cross-region/edge coordination rides the envelope, not Postgres consensus.

## Test

```sh
python tools/temporal/hlc.py     # self-test: monotonicity, cross-node causal order, drift guard, envelope round-trip
```
