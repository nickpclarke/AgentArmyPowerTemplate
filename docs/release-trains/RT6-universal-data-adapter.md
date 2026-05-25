# RT6 — Universal Data Adapter (UDA)

Durable Epic plan for the `nickpclarke/backend-core` spoke: a **FastAPI-based Universal Data Adapter**
that provides a single, provider-neutral query surface over heterogeneous storage backends (ArcadeDB,
Postgres, object storage, and future connectors), with per-connection RBAC, query caching, pagination,
and observability.

> **The backend-core repo board is the source of truth for status and issue numbers.**
> Issues for this RT live at `https://github.com/nickpclarke/backend-core/issues`.
> Stable local IDs (`UDA-*`) below are the durable planning references.
> Hub Epic cross-reference: `UDA-E` (Epic #13 in backend-core).

---

## Theme

**Universal Data Adapter**: give every spoke and agent a single, authenticated, paginated query surface
over the platform's heterogeneous storage layer — ArcadeDB (graph/ontology), Postgres (relational),
object storage (blobs), and future connectors — without coupling consumers to backend specifics.
The UDA is the **data-plane contract** that RT7 (middle-core runtime) and RT8 (agent analytics tools)
depend on; its OpenAPI schema is the integration boundary.

This RT is a **spoke-implementation train** — all deliverables are in `nickpclarke/backend-core`.

---

## Summary

| Epic | Phase | Features / Enablers | PI | Status |
|---|---|---|---|---|
| **UDA-E** Universal Data Adapter | Phase 1 (shipped) | Core adapter + ArcadeDB connector | PI-2 | **Shipped** via PR #31 |
| **UDA-E** | Phase 2 (in-flight) | Issues #33–#44 | PI-2/PI-3 | In progress |
| **UDA-E** | Phase 3 (planned) | Issues #45–#50 (Postgres, object storage, pagination, RBAC, caching, OpenLineage) | PI-3 | Not started |

**Total Phase 3:** 6 Features/Spikes = the planned work described in this document.
**Session estimate (Phase 3):** ~3–4 sessions (implementation-heavy: real connectors, RBAC middleware,
cache layer, observability spike).

**Live issues:**
- Epic: `https://github.com/nickpclarke/backend-core/issues/13`
- Phase 2 in-flight: `https://github.com/nickpclarke/backend-core/issues` #33–#44
- Phase 3 planned: #45–#50

---

## Phase 1 — Shipped (reference only)

Phase 1 delivered the foundational UDA: FastAPI app skeleton, ArcadeDB HTTP connector, query dispatch
layer, OpenAPI baseline, and Docker + CI. Merged to main in PR #31.

---

## Phase 2 — In-flight (issues #33–#44)

Issues #33–#44 are active work tracked on the backend-core board. This document does not re-specify
them in detail — see the live issues for acceptance criteria. Key themes in Phase 2:
- Connector abstraction hardening
- Query result normalisation
- Error handling and retry semantics
- OpenAPI schema refinement

---

## Phase 3 — Backlog items (issues #45–#50)

> SAFE fields per item: `Type`, `PI`, `Size`, `Estimate` (Fibonacci pts), `Priority`. Definition of
> Ready = these set + acceptance criteria below. Definition of Done = PR merged with `Closes #N`,
> CI green, OpenAPI schema updated.

---

### UDA-E — Epic: Universal Data Adapter (issue #13)

- **Type:** Epic · **PI:** PI-2 → PI-3 (multi-increment) · **Priority:** P0
- **Outcome:** A single FastAPI service exposes a provider-neutral query API over ArcadeDB, Postgres,
  and object storage; queries are paginated, cached, access-controlled per connection, and
  OpenLineage-traceable. The OpenAPI schema is the stable contract consumed by RT7 (MCR-F4 projections)
  and RT8 (GPM-F3 analytics tools).
- **Children (Phase 3):** UDA-F1, UDA-F2, UDA-F3, UDA-F4, UDA-F5, UDA-S1.

---

### UDA-F1 — Feature: Postgres connector (issue #45)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** Phase 2
  connector abstraction stable
- **Scope:** `connectors/postgres/` — `asyncpg`-based connector; connection pool management;
  parameterised query execution; result normalisation to UDA canonical row format; schema introspection
  endpoint `GET /connectors/postgres/{id}/schema`; `DATABASE_URL` env var + Key Vault reference;
  integration test against a Postgres container in CI.
- **Acceptance:** `SELECT` and parameterised DML round-trip correctly; connection pool reused across
  requests (not re-created per call); schema endpoint returns table + column metadata; CI integration
  test runs against `postgres:16` Docker container.

---

### UDA-F2 — Feature: Object-storage connector (issue #46)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P2 · **Depends on:** Phase 2
  connector abstraction stable; **parallel with** UDA-F1
- **Scope:** `connectors/object-storage/` — Azure Blob Storage + S3-compatible adapter;
  `LIST /containers/{container}`, `GET /objects/{container}/{key}`, metadata-only mode;
  presigned-URL generation for large object download; `AZURE_STORAGE_CONNECTION_STRING` /
  `AWS_S3_BUCKET` env vars; streaming response for large objects.
- **Acceptance:** list + get round-trip against Azurite emulator in CI; presigned URL expires
  correctly; metadata-only mode returns content-length + content-type without body transfer.

---

### UDA-F3 — Feature: Query pagination (issue #47)

- **Type:** Feature · **Size:** S · **Estimate:** 3 · **Priority:** P0 · **Depends on:** Phase 2
  query dispatch stable
- **Scope:** Cursor-based pagination on all list/query endpoints (`?cursor=&limit=`); opaque cursor
  token (base64-encoded offset or keyset); `X-Next-Cursor` response header; max page size enforced
  (configurable, default 100); OpenAPI schema updated with pagination parameters and response envelope.
- **Acceptance:** first page returns `X-Next-Cursor`; following cursor returns the next page; last
  page returns no cursor; requesting beyond last page returns empty list (not 404); RT8 GPM-F3
  analytics tools can iterate all results without client-side offset arithmetic.
- **Cross-RT note:** RT8 GPM-F3 (analytics tools over UDA) is blocked until this feature is stable.
  This is **the highest-priority Phase 3 item**.

---

### UDA-F4 — Feature: Per-connection RBAC (issue #48)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** UDA-F3
  (pagination must be stable before RBAC layering)
- **Scope:** Connection-level access policy stored in config or ArcadeDB; JWT claims or API-key scope
  checked against the policy on every query; `403 Forbidden` with structured error body on deny;
  admin endpoint `POST /connections/{id}/policy` to set the policy; policy evaluation logged as OTel
  span attribute.
- **Acceptance:** query with insufficient scope returns 403; policy update takes effect without
  service restart; policy evaluation appears in OTel trace; existing public/unscoped queries
  unaffected when policy is not configured.

---

### UDA-F5 — Feature: Query caching (issue #49)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P2 · **Depends on:** UDA-F3,
  UDA-F4; **parallel with** UDA-S1
- **Scope:** In-process LRU cache (Redis-ready via pluggable backend); cache key = hash of
  (connector ID, query, parameters); TTL configurable per connector; `Cache-Control` / `X-Cache-Hit`
  response headers; cache bypass via `Cache-Control: no-cache` request header; metrics:
  `uda_cache_hits_total`, `uda_cache_misses_total`.
- **Acceptance:** identical query within TTL returns `X-Cache-Hit: true`; mutating query bypasses
  cache; cache metrics appear in `/metrics`; TTL=0 disables caching for a connector.

---

### UDA-S1 — Spike: OpenLineage integration (issue #50)

- **Type:** Spike · **Size:** S · **Estimate:** 2 · **Priority:** P2 · **Time-box:** ½ session
- **Question:** Determine the minimal OpenLineage event model for UDA queries (dataset-in /
  dataset-out, job name, run ID) and whether the OpenLineage HTTP transport can be added as a
  passthrough without blocking query execution. **Output:** findings note + recommended event schema
  + estimated implementation size for a follow-up Feature.

---

## Dependency graph

```
Phase 1 (shipped) — PR #31
  └─ Phase 2 (in-flight) — #33–#44
       └─ UDA-F3 (pagination — #47)                  ← P0; unblocks RT8 GPM-F3
            ├─ UDA-F4 (RBAC — #48)
            │    └─ UDA-F5 (caching — #49)
            ├─ UDA-F1 (Postgres connector — #45)      ← parallel with F2 after Phase 2 stable
            └─ UDA-F2 (object-storage connector — #46) ← parallel with F1

UDA-S1 (OpenLineage spike — #50)                      ← independent; run any time
```

**Critical path:** UDA-F3 (pagination) is the highest-priority item — it unblocks RT8's analytics
tooling (GPM-F3) which is part of the generative platform maturity train.

---

## Cross-RT dependencies

| Downstream RT | Depends on UDA | Reason |
|---|---|---|
| RT7 MCR-F4 (C# data-platform objects) | UDA OpenAPI schema | Middle-core projection interfaces bind to the UDA contract; schema must be stable before MCR-F4 finalises |
| RT8 GPM-F3 (analytics tools over UDA) | UDA-F3 (pagination) | Agent analytics tool nodes must paginate results; blocked until UDA-F3 ships |
| RT8 GPM-EN1 (ArcadeDB pin backend) | UDA ArcadeDB connector (Phase 1/2) | Pin backend queries ArcadeDB via UDA surface |

RT6 **provides** the data-plane contract; RT7 and RT8 **consume** it. Versioning rule: a UDA OpenAPI
schema change that breaks a response shape must be accompanied by a MCR-F4 / GPM-F3 consumer update
in the same sprint; never break consumers silently.

---

## Exit criteria

**RT6 Phase 3 is done when:**
- Postgres connector runs integration-tested queries in CI (UDA-F1)
- Object-storage connector lists and retrieves blobs against Azurite in CI (UDA-F2)
- All list/query endpoints are cursor-paginated; RT8 analytics tools verified against paginated
  responses (UDA-F3)
- Per-connection RBAC enforces scope on every query (UDA-F4)
- Query caching reduces repeat query latency with measurable hit-rate metrics (UDA-F5)
- OpenLineage spike deliverable reviewed and follow-up Feature sized (UDA-S1)

---

## PI assignment

**PI-3 (candidate) for Phase 3.** Phase 1 shipped in PI-2. Phase 2 is active in PI-2/PI-3.
UDA-F3 (pagination) is the Phase 3 item most likely to be pulled into the current sprint to
unblock RT8 GPM-F3 — treat it as PI-2 tail / PI-3 head depending on Phase 2 velocity.

---

## Notes

- **Contract-first.** The UDA OpenAPI schema is the integration boundary. All consumer code
  (middle-core projections, agent tool nodes) must be generated from or validated against the
  published schema. Never couple consumers to UDA internals.
- **Spoke-implementation train.** All deliverables are in `nickpclarke/backend-core`. No hub
  template files are modified.
- **ArcadeDB is persistence, not the reasoner.** The UDA routes queries to ArcadeDB as one of
  several backends; it does not embed ArcadeDB reasoning logic.
- **Phase 2 issues (#33–#44) are tracked on the backend-core board.** This document covers Phase 3
  planning only; consult live issues for Phase 2 status.
