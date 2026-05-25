# ARC-ADR-012 — Read-Query Caching & Invalidation for UDA Read Path: In-Process TTL vs Shared Cache vs Runtime Cache

| Field | Value |
|---|---|
| ID | ARC-ADR-012 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | caching, uda, performance, ttl, redis, invalidation, backend-core, cost-control |

---

## Context and Problem Statement

The Universal Data Adapter (UDA) read path (backend-core **#49**) re-executes identical read-only
queries against connected backends — ArcadeDB today, BigQuery/Postgres/object-store next (ARC-ADR-009).
A repeated cross-connector query in the query lab, or the same agent tool firing the same lookup across
turns, pays full backend latency *and*, for metered backends like BigQuery, full **cost** every time.
A read cache — TTL-bounded, keyed by connection + query + params — collapses those repeats.

The danger is a cache that returns the *wrong* result. Two invariants are non-negotiable: **never cache
writes** (a cached write would be a correctness and durability bug), and **never cache auth-varying
results** — if two principals with different per-connection roles (ARC-ADR-013) would see different
rows, a cache key that omits the principal serves one user another's data. So the cache key, its
invalidation, and its isolation are the substance of the decision, not just "should we cache."

The decision to be made is: **whether and where to cache UDA read results — the cache topology
(in-process TTL vs a shared cache such as Redis vs the platform/middle-core runtime cache), the cache
key (connection + query + params, and how the principal/role factors in), the TTL/invalidation policy,
and the isolation guarantees — given the hard rule that only read-only, non-auth-varying results are
ever cached.**

Decided late, each connector or endpoint bolts on its own ad-hoc cache with its own key, no shared
invalidation, and inconsistent (or absent) principal isolation — the worst case being a stale or
cross-tenant read. Decided early, one cache contract governs key shape, TTL, invalidation, and the
"reads only, principal-scoped" rule across the whole UDA read path.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Correctness first** — only **read-only** queries are cacheable; a write (or any mutating capability) is never cached and should invalidate affected cached reads. |
| D2 | **No auth leakage** — results that vary by principal/role (ARC-ADR-013 per-connection RBAC) must be isolated; the key must encode the principal (or the cache scoped per-principal) unless results are provably principal-invariant. |
| D3 | **Deterministic key** — `connection + normalized-query + params` (+ principal where D2 applies); query normalization must be stable so equivalent queries hit, and divergent ones don't collide. |
| D4 | **Bounded staleness** — a TTL that is explicit, per-connector-tunable, and short enough that read-after-write windows are acceptable; explicit invalidation on known writes through the UDA. |
| D5 | **Cost control** (D for FinOps) — for metered backends (BigQuery slots/bytes), the cache is a spend lever; hit-rate and bytes-saved should be observable (ARC-ADR-010 metrics). |
| D6 | **Topology fit** — single-instance backend-core can use in-process; a scaled-out/multi-replica deployment needs a shared cache to avoid per-replica cache fragmentation and inconsistent invalidation. |

---

## Considered Options

1. **In-process TTL cache (per backend-core instance)** — a bounded in-memory TTL map keyed by
   `connection + query + params` (+ principal per D2). Simplest, lowest latency, zero new
   infrastructure; but cache state is per-replica (no cross-replica sharing or invalidation) and lost
   on restart.
2. **Shared cache (Redis or equivalent)** — a single logical cache all backend-core replicas read/write,
   with TTL and explicit invalidation. Consistent across replicas, survives restarts, enables global
   invalidation on a known write; adds an external dependency (its own secret via ARC-ADR-011, ops, and
   a network hop).
3. **Platform / middle-core runtime cache** — fold read caching into the platform's existing runtime
   layer (e.g. the middle-core model/projection runtime) rather than backend-core, caching at the
   "one model, many projections" boundary (ARC-ADR-009) instead of at the connector. Aligns with the
   canonical-model thesis but places the cache further from the connector that knows when a result is
   stale.

---

## Decision Outcome

**Accepted 2026-05-25 — Option 3: fold read-query caching into the platform / middle-core runtime cache layer (not a backend-core-local cache); keep the cache contract reads-only + principal-scoped.** The HITL framing that produced this choice: This is an **HITL** decision — the Architecture Review (or hub owner) must choose,
because the topology trade-off (operational simplicity vs cross-replica correctness vs alignment with
the canonical-model runtime) couples to the deployment model (ARC-ADR-015) and the authorization model
(ARC-ADR-013), and is a strategic call, not a mechanical one.

### Recommendation note (not a decision)

Lean **Option 1 (in-process TTL) as the starting point, with Option 2 (shared cache) as the documented
upgrade once backend-core scales past one replica**:

- **Ship the cache contract first, topology second** (D3/D4): nail the key
  (`connection + normalized-query + params + principal-where-D2-applies`), the per-connector TTL, and
  the invalidation hooks **independent** of whether the store is in-process or Redis — so swapping
  topology is a backend change, not a contract change.
- **Bake the two hard rules into the cache layer, not callers** (D1/D2): the cache **refuses** to store
  a write/mutating capability's result, and **refuses** to serve a principal-varying result across
  principals — make these structural, not conventions a connector author must remember.
- **Start in-process** (D6): while backend-core is single-instance, Option 1's zero-infra, lowest-latency
  cache is correct and sufficient. The moment it runs multi-replica, per-replica caches fragment and
  invalidation breaks — that is the trigger to adopt Option 2 (Redis), whose connection secret resolves
  via ARC-ADR-011's `akv:` scheme.
- **Instrument from day one** (D5): emit `backend_uda_cache_hits_total` / `_misses_total` and
  bytes/cost-saved per ARC-ADR-010's naming, so the cache's value (and BigQuery spend reduction) is
  measurable and the in-process → shared decision is data-driven.
- **Defer Option 3** unless the canonical-model runtime proves the better invalidation point: it is
  architecturally attractive but moves the cache away from the connector that holds the freshest
  staleness signal.

A spike (`performance-engineer`) measuring hit-rate and read-after-write staleness on the real ArcadeDB
+ a metered BigQuery query would size the TTL and confirm the in-process → shared trigger.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | UDA read path #49 — the cache layer, key, TTL, invalidation, and the reads-only/principal-scoped rules live here |
| middle-core | nickpclarke/middle-core | Agent tools that repeat read queries benefit transparently; Option 3 would site the cache here at the projection boundary |
| frontend-core | nickpclarke/frontend-core | Query lab read latency improves; no direct cache logic (thin proxy per ARC-ADR-003) |
| (infra) | hub templates | Redis (if Option 2) deployment + its secret via ARC-ADR-011; cache metrics scraped per ARC-ADR-010 |

---

## Pros and Cons of the Options

### Option 1 — In-process TTL cache (recommended start)

**Pros:**
- Zero new infrastructure; lowest possible latency (no network hop); trivial to ship.
- No extra secret or ops surface; correct and sufficient while backend-core is single-instance.

**Cons:**
- Per-replica state — no sharing, no global invalidation; multi-replica deployments fragment and risk inconsistent staleness.
- Cache lost on restart/deploy (cold cache after every release).

### Option 2 — Shared cache (Redis)

**Pros:**
- Consistent across replicas; survives restarts; enables global invalidation on a known write.
- Cache hit-rate and cost savings centrally observable; the obvious scaled-out target.

**Cons:**
- New external dependency: its own secret (ARC-ADR-011), ops, network hop, and failure mode (cache down → fall back to backend).
- Principal-scoped keys can grow the keyspace; eviction policy must be tuned.

### Option 3 — Platform / middle-core runtime cache

**Pros:**
- Aligns with the "one model, many projections" canonical-model thesis (ARC-ADR-009); caches once for all consumers.

**Cons:**
- Sits further from the connector that knows when a result is stale — invalidation is harder to reason about.
- Couples caching correctness to the runtime layer's lifecycle, not the read path's.

---

## Related Decisions

- **ARC-ADR-005:** backend-core OpenAPI contract — the read endpoints whose results are cached.
- **ARC-ADR-009:** Canonical data model — cached rows are in the canonical Arrow/CDM shape; Option 3 caches at the projection boundary.
- **ARC-ADR-010:** Observability standard — cache hit/miss + cost-saved metrics use its naming and cardinality rules.
- **ARC-ADR-011** (proposed): Runtime secret-resolution — a Redis (Option 2) connection string resolves via the `akv:` + managed-identity scheme.
- **ARC-ADR-013** (proposed): Per-connection RBAC — defines the principal/role dimension that the cache key must encode (D2) to avoid auth-varying leakage.
- **ARC-ADR-015** (backlog): Deployment & release-promotion — single- vs multi-replica deployment is the trigger for the in-process → shared topology switch (D6).

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
