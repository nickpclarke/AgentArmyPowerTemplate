# RT7 — Middle-Core Runtime: Administrable, Instrumented, ArcadeDB-Backed Platform

Durable Epic plan for taking the `nickpclarke/middle-core` repo from a model-driven prototype to a
**running, administrable, observable platform** with real ArcadeDB persistence, a model administration
surface, OpenTelemetry instrumentation, and a typed C# data-platform object layer.

> **The middle-core repo backlog is the source of truth for status and issue numbers.**
> Issues for this RT live at `https://github.com/nickpclarke/middle-core/issues`. Stable local IDs
> (`MCR-*`) below are the durable planning references. Hub Epic cross-reference: see the RT5 coordination
> note at the bottom of this document before scheduling MCR-F1.

---

## Theme

**Middle-Core Runtime**: promote the factory pipeline (`model/middle-core/model.yaml` -> modelgen ->
generated C# contracts -> runtime) from prototype to a working platform by layering on three orthogonal
capabilities that do not exist today: (a) real ArcadeDB persistence wired through the `IPinStore` seam
from RT5, (b) a model administration plane for operators and agents to manage object-type activation
and model versions, and (c) structured telemetry so agents can observe scenario runs, graph mutations,
and enforcement outcomes. The C# data-platform object layer cements the typed contract between the
generator and the runtime's provider projections.

---

## Summary

| Epic | Features | Enablers | Spikes | PI | Sequencing |
|---|---|---|---|---|---|
| **MCR-E** Middle-Core Runtime platform | MCR-F1...F5 | MCR-EN1, MCR-EN2 | MCR-S1, MCR-S2 | **PI-3 (candidate)** | MCR-EN1 first (unblocks all); MCR-F1 keystone; MCR-F2/F3/F4 parallel after keystone; MCR-F5 + MCR-EN2 last |

**Total:** 1 Epic + 5 Features + 2 Enablers + 2 Spikes = 10 board items.
**Session estimate:** ~3-4 sessions (implementation-heavy runtime + instrumentation + ArcadeDB integration;
compare RT2-style velocity: 1-3 Size:M features/session). MCR-EN1 + spikes can run in a ½-session
foundation pass.

**Live issues:** `https://github.com/nickpclarke/middle-core/issues` (Epic #7, children #8-#16).

---

## Backlog items

> SAFE fields per item: `Type`, `PI`, `Size`, `Estimate` (Fibonacci pts), `Priority`. Definition of Ready =
> these set + acceptance criteria below. Definition of Done = PR merged with `Closes #N`,
> `TreatWarningsAsErrors` and all tests green.

### MCR-E — Epic: Middle-Core Runtime platform (issue #7)

- **Type:** Epic · **PI:** PI-3 (candidate) · **Priority:** P1
- **Outcome:** middle-core runtime is administrable (model admin surface), observable (OTel + Prometheus),
  ArcadeDB-backed (via RT5 PIN-F4 seam), and has a typed C# data-platform object layer. The factory
  pipeline remains generator-first; this epic wires the generated output into a real operational stack.
- **Children:** MCR-F1, MCR-F2, MCR-F3, MCR-F4, MCR-F5, MCR-EN1, MCR-EN2, MCR-S1, MCR-S2.

---

### MCR-EN1 — Enabler: DI scaffolding + admin surface wiring (issue #13)

- **Type:** Enabler · **Size:** S · **Estimate:** 3 · **Priority:** P0 · **Depends on:** — (foundation)
- **Scope:** NuGet packages for OTel + Prometheus; register `ActivitySource`, `IActivationStore`,
  `VersionLedger` singletons; `/admin` route group stub; OpenAPI baseline on all existing endpoints.
- **Acceptance:** `dotnet build` succeeds; `/metrics` returns HTTP 200; `/admin` prefix returns HTTP 200
  for GET list endpoints; `TreatWarningsAsErrors` passes.
- **Note:** Unblocks MCR-F1, MCR-F2, MCR-F3, MCR-F4, MCR-F5 in parallel. Run first.

---

### MCR-F1 — Feature: ArcadeDB persistence for runtime objects (issue #8) — KEYSTONE

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P0 · **Depends on:** RT5 PIN-F4
  (must ship first), MCR-EN1
- **Scope:** DI wires `IPinStore` -> `PinStore` + `ArcadeDbPinBackend` when `PIN_BACKEND=arcadedb`;
  `KnowledgeDropScenarioRunner` calls `PinGraphAsync` after a successful run; idempotent re-run; `/health`
  returns `degraded` + `arcadedb_reachable: false` when ArcadeDB is unreachable; integration test covers
  the full pin round-trip.
- **Acceptance:** pin round-trip idempotent; health degraded path tested; existing tests green.
- **Keystone:** once runtime objects reach ArcadeDB, MCR-F2 and MCR-F3 can proceed in parallel.

---

### MCR-F2 — Feature: Model administration API (issue #9)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** MCR-EN1
- **Scope:** `GET /admin/model/object-types`, `GET /admin/model/object-types/{id}`,
  `PATCH /admin/model/object-types/{id}/activate|deactivate`, `GET /admin/model/scenarios`,
  `GET /admin/model/versions`. Activation state stored via `IActivationStore`; deactivated types excluded
  from scenario routing.
- **Acceptance:** all 9 object types returned; deactivate -> scenario returns HTTP 422; snake_case JSON;
  OpenAPI descriptions updated.

---

### MCR-F3 — Feature: OpenTelemetry traces + Prometheus metrics (issue #10)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** MCR-EN1;
  **parallel with** MCR-F2
- **Scope:** `scenario.run` root span (attributes: scenario_id, status, duration_ms, node_count,
  edge_count); `scenario.step` and `enforcement.check` child spans; counters
  `middle_core_scenario_runs_total`, `middle_core_graph_mutations_total`,
  `middle_core_enforcement_violations_total`; histogram `middle_core_scenario_duration_seconds`;
  OTLP exporter (console fallback in Development).
- **Acceptance:** scenario run produces exportable span; `/metrics` returns counters; failure increments
  failed counter; OTLP disabled gracefully when env var absent.

---

### MCR-F4 — Feature: C# data-platform objects — typed *Data records (issue #11)

- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** MCR-EN1;
  **parallel with** MCR-F2 and MCR-F3
- **Scope:** All 9 `*Data` records get `SchemaVersion` property + `Validate()` method + `IDataPlatformObject`
  marker; new generated `DataPlatformContracts.g.cs` with `I{ObjectType}Projection` interfaces;
  `check_drift.py` extended to gate CI on model.yaml property drift.
- **Acceptance:** `SchemaVersion` populated; `Validate()` rejects null required fields and invalid states;
  drift gate fails CI on mismatch; build green.

---

### MCR-F5 — Feature: Model version ledger + schema-drift CI guard (issue #12)

- **Type:** Feature · **Size:** S · **Estimate:** 3 · **Priority:** P2 · **Depends on:** MCR-F4, MCR-F2
- **Scope:** `VersionLedger` records each activation with timestamp + git SHA; startup guard sets
  `health.model_drift: true` on schema_version mismatch; `GET /admin/model/versions` backed by ledger;
  `check_drift.py --strict` CI gate.
- **Acceptance:** version history endpoint works; boot with stale artifact sets drift flag; CI gate exits
  non-zero on mismatch.

---

### MCR-EN2 — Enabler: Docker + ACA deployment manifest (issue #14)

- **Type:** Enabler · **Size:** S · **Estimate:** 2 · **Priority:** P2 · **Depends on:** MCR-EN1, MCR-F3
- **Scope:** Update `Dockerfile` with OTel + PIN_BACKEND env defaults; `deploy/aca-middle-core.yaml`
  manifest; Docker build step in CI.
- **Acceptance:** `docker build` succeeds; ACA manifest references all required env vars; CI build step
  fails PR if image breaks.

---

### MCR-S1 — Spike: ArcadeDB admin-table patterns (issue #15)

- **Type:** Spike · **Size:** S · **Estimate:** 2 · **Priority:** P2 · **Time-box:** half session
- **Question:** Confirm DDL + query patterns for `ModelVersionLedger` and activation-state document types
  alongside the existing pinning schema. Output: SQL shapes + index recommendations for MCR-F1/F2/F5.

---

### MCR-S2 — Spike: OTel trace sampling strategy and metrics cardinality (issue #16)

- **Type:** Spike · **Size:** XS · **Estimate:** 1 · **Priority:** P2 · **Time-box:** 1-2 hours
- **Question:** Cardinality safety of chosen label sets; correct `ActivityKind` for scenario spans;
  attribute vs gauge trade-off for `graph.node_count`. Output: confirmed attribute set + sampling config
  snippet for MCR-F3.

---

## Dependency graph

```
MCR-EN1 (DI scaffolding)                          ← run first; unblocks all below
  ├─ MCR-F1 (ArcadeDB persistence)                ← KEYSTONE; needs RT5 PIN-F4
  │    (MCR-S1 feeds MCR-F1 DDL patterns)
  ├─ MCR-F2 (model admin API)                     ← parallel with F3/F4 after EN1
  ├─ MCR-F3 (OTel + Prometheus)                   ← parallel with F2/F4 after EN1
  │    (MCR-S2 feeds MCR-F3 attribute design)
  ├─ MCR-F4 (C# data-platform objects)            ← parallel with F2/F3 after EN1
  │    └─ MCR-F5 (version ledger + drift gate)    ← after F4 + F2
  └─ MCR-EN2 (Docker + ACA manifest)              ← after EN1 + F3
```

**Keystone:** MCR-F1 — once the runtime pins objects to a live ArcadeDB, the persistence seam is proven
and the admin + instrumentation features have a real backend to exercise against.

**Parallelisation opportunity:** MCR-F2, MCR-F3, and MCR-F4 are all independent of each other after
MCR-EN1; three agents can run them concurrently in a single session.

---

## RT5 coordination note

RT5 (`PIN-E`) covers the **provider-neutral pinning primitives** (`CanonicalJson`, `OntologyIri`,
`PinHash`, `PinnedElement`, `IPinStore`, `InMemoryPinBackend`) and the **ArcadeDB adapter**
(`ArcadeDbPinBackend`, DDL, idempotency semantics).

**RT7 does not reimplement any of that.** MCR-F1 is strictly integration work: it calls `IPinStore` from
within the middle-core runtime and wires the DI to point at `ArcadeDbPinBackend`. The split is:

| RT5 owns | RT7 owns |
|---|---|
| Pinning domain model (primitives, PinnedElement) | Runtime objects calling the pin store |
| `IPinStore` / `PinStore` orchestrator | DI registration selecting the backend |
| `InMemoryPinBackend` + `ArcadeDbPinBackend` | Integration test against a live ArcadeDB |
| ArcadeDB DDL for ontology elements + ledger | ArcadeDB DDL for admin tables (MCR-S1 output) |

**Scheduling rule:** MCR-F1 is **blocked** until RT5 PIN-F4 ships. If PIN-F4 slips, MCR-F1 falls back
to `InMemoryPinBackend` for the sprint and picks up the ArcadeDB wiring in the following sprint.

---

## RT6 / UDA interface note

The **Universal Data Adapter (RT6, `UDA-E`)** is built in the **backend-core** spoke, but it
**consumes interfaces from middle-core** — its logical projections + bindings map onto middle-core's
canonical model and typed data-platform objects. RT7 is the **producer** side of that contract:

- **MCR-F4** (C# data-platform objects + generated `DataPlatformContracts.g.cs`
  `I{ObjectType}Projection` interfaces + `SchemaVersion`) is the surface the UDA binds to. Publish it
  **contract-first** — a stable, versioned contract (generated projection interfaces / OpenAPI / shared
  schema), never middle-core internals.
- **MCR-F2** (model administration API) is the provider-neutral admin surface the UDA's operator plane
  can call.
- **MCR-F5** (version ledger + schema-drift guard) + `SchemaVersion` keep that contract stable for the
  UDA across model changes.

**Cross-RT dependency:** RT6 (UDA / backend-core) **depends on** RT7's published interface — MCR-F4
(and MCR-F2 for admin). Coordinate versioning at PI planning so a middle-core model change can't silently
break the UDA's bindings; the schema-drift guard (MCR-F5) is the safety net.

---

## Notes

- **Draft backlog, not yet scheduled.** Issues are created in `nickpclarke/middle-core` with the `draft`
  label. Set `PI`, `Iteration`, `Start date`, `Target date` fields at sprint planning.
- **Board:** https://github.com/nickpclarke/middle-core/issues (no shared Projects board yet; create one
  per CLAUDE.md setup guidance when the spoke team is ready).
- **Generator-first invariant:** the model -> generator -> output loop must stay untouched. MCR-F4
  extends generated output but does not alter the generator's core loop. Any generator changes must
  preserve all existing emitted files.
- **No new ontology concepts in this RT.** All business objects come from the existing `model.yaml`
  `object_types` list.
