# ARC-ADR-009 — Canonical Data Model + Arrow Type Vocabulary Across UDA Connectors

| Field | Value |
|---|---|
| ID | ARC-ADR-009 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — to be decided) |
| Supersedes | — |
| Superseded by | — |
| Tags | uda, canonical-model, cdm, arrow, adbc, backend-core, middle-core, connectors, contract-first |

---

## Context and Problem Statement

The Universal Data Adapter (UDA, RT6 / `UDA-E`, built in backend-core) connects to many backends from
one place — ArcadeDB is live; BigQuery, Postgres, and object-storage are planned (backend-core
#35/#43). Each backend has its own type system: ArcadeDB document/graph types, BigQuery's SQL types
(including `STRUCT`/`ARRAY`/`NUMERIC`), Postgres types, Parquet/object-store schemas. If every
connector exposes its native types, every consumer (middle-core agent tools, frontend-core, the
query lab) must special-case each connector — the opposite of "universal."

Two intertwined decisions sit here:

1. **A Common Data Model (CDM)** — the connection/connector/pipeline/capability vocabulary the
   adapter exposes (the "schema scout" + connection registry). The platform's stated thesis is that
   this CDM is **not a separate schema**: it is the same canonical `model.yaml` model middle-core
   already drives ("one model, many projections" — `Connection`, `Connector`, `Pipeline`,
   `Capability` as modeled objects). middle-core's typed `*Data` records + generated
   `DataPlatformContracts.g.cs` projection interfaces (MCR-F4, middle-core #11, with `SchemaVersion`)
   are the producer side; the UDA binds to them (RT6 ← RT7 dependency).
2. **A canonical column/value type vocabulary** — when a connector returns rows, into what neutral
   type system are values normalized so consumers don't see BigQuery vs Postgres vs ArcadeDB
   differences? Apache **Arrow** (via **ADBC**, already named in the UDA adopt list alongside `dlt`
   and `sqlalchemy-bigquery`) is the natural candidate: a columnar, zero-copy, cross-language type
   system with first-class ADBC drivers for exactly these backends.

The decision to be made is: **what is the canonical data model the UDA exposes (and is it literally
the middle-core `model.yaml` canonical model, or a separate UDA CDM?), and what is the canonical
type vocabulary (Arrow/ADBC vs JSON-Schema vs per-connector native) every connector normalizes into
at the boundary?**

Decided late, each connector invents its own type mapping and the "universal" adapter fractures into
N bespoke adapters; consumers couple to connector internals; and the RT6←RT7 contract (UDA binding to
middle-core projections) drifts. Decided early, there is one CDM and one type vocabulary every
connector and consumer agrees on.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | A consumer (agent tool, frontend, query lab) must read results from any connector through **one** type vocabulary — no per-connector type special-casing. |
| D2 | The CDM should converge with middle-core's canonical `model.yaml` model — connectors/connections/pipelines/capabilities are *modeled objects*, not a parallel schema ("one model, many projections"). |
| D3 | The type vocabulary must faithfully carry the backends in scope: ArcadeDB (live), BigQuery (`STRUCT`/`ARRAY`/`NUMERIC`/timestamps), Postgres, and Parquet/object-store schemas — including nested/repeated and decimal/temporal types. |
| D4 | Contract-first: the CDM + type vocabulary is a **published, versioned contract** (`SchemaVersion`, drift-gated) the UDA binds to — never connector internals (per [contracts.md](../contracts.md) and ARC-ADR-005). |
| D5 | The vocabulary should be efficient at the volumes the UDA will move (analytical reads from BigQuery, bulk `dlt` loads) — favor a columnar, zero-copy representation over row-by-row JSON where it matters. |
| D6 | The boundary must degrade gracefully for the long tail — a connector type with no canonical equivalent maps to a documented fallback (e.g. canonical `string` + an annotation), never a silent coercion. |

---

## Considered Options

> Two layered choices: **(A) the CDM** and **(B) the type vocabulary.** They are decided together but
> listed as paired options.

1. **Canonical model = middle-core `model.yaml` projections; type vocabulary = Arrow via ADBC**
   (recommended) — the UDA's connection/connector/pipeline/capability CDM is a projection of the
   *same* `model.yaml` canonical model (binding to MCR-F4's `DataPlatformContracts.g.cs` projection
   interfaces + `SchemaVersion`). At the data-value boundary, every connector returns Arrow record
   batches (ADBC drivers for BigQuery/Postgres; ArcadeDB + object-store adapted into Arrow). One CDM,
   one columnar type system, both versioned.
2. **Separate UDA CDM (its own schema) + Arrow type vocabulary** — the UDA defines its own connection
   registry schema independent of `model.yaml`, but still normalizes values to Arrow. Decouples the
   adapter's release cadence from middle-core; explicitly rejects the "one model" convergence.
3. **JSON-Schema CDM + JSON value normalization (no Arrow)** — model both the registry and the value
   types in JSON Schema; connectors return JSON rows. Simplest, language-neutral, no Arrow dependency;
   gives up columnar efficiency and precise decimal/temporal/nested typing.

---

## Decision Outcome

**To be decided.** HITL — this is a strategic convergence call (is the UDA's model *the* platform
model, or its own?) plus a foundational type-system choice that every connector inherits. The
Architecture Review (with `solution-architect` / `information-architect` input) must decide.

### Recommendation note (not a decision)

Lean **Option 1**, because:

- D2 + the platform's explicit "one model, many projections" thesis argue strongly that the UDA's
  registry *is* the canonical model, not a fork of it — the labs vision states the adapter's CDM
  "**is** the platform model — not a separate schema." Binding the UDA to MCR-F4's published
  projection interfaces + `SchemaVersion` (RT6←RT7) is exactly the contract-first path D4 wants.
- D1/D3/D5 favor **Arrow/ADBC** for the value boundary: ADBC drivers already exist for the named
  backends, Arrow carries nested/repeated (BigQuery `STRUCT`/`ARRAY`) and decimal/temporal types
  faithfully, and it's zero-copy/columnar for the analytical and bulk-load volumes the UDA targets.
- Pair it with a **canonical type-map table** (per connector: native type → canonical Arrow type, with
  the D6 fallback documented) maintained as part of the contract.

Two caveats to settle in the full ADR: (1) Arrow is heavier for tiny key-value reads — allow a JSON
projection *off* the canonical Arrow result for trivial cases rather than making Arrow mandatory
end-to-end; (2) confirm ADBC driver maturity for each target before committing a connector to it.

This decision should land **before** the second non-ArcadeDB connector (BigQuery, backend-core #35)
is built, so the first connector doesn't set an accidental precedent.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | UDA connector interface returns canonical types; connection registry CDM; #35 (connectors), #43 (connector onboarding) |
| middle-core | nickpclarke/middle-core | Producer of the canonical model — `DataPlatformContracts.g.cs` projection interfaces + `SchemaVersion` (MCR-F4, #11); generator-first invariant must hold |
| frontend-core | nickpclarke/frontend-core | Consumes canonical results in generative UI (gallery, tables) — one render path regardless of source connector |

---

## Pros and Cons of the Options

### Option 1 — `model.yaml` projection CDM + Arrow/ADBC (recommended)

**Pros:**
- One model across the whole platform; the UDA registry is a projection, not a fork — kills CDM drift (D2).
- Arrow/ADBC carries nested/decimal/temporal types faithfully and is efficient at analytical volumes (D3, D5).
- Contract-first and versioned via MCR-F4 `SchemaVersion` + drift gate (D4); binds to published interfaces, not internals.

**Cons:**
- Couples UDA release cadence to the middle-core model contract (mitigated by `SchemaVersion` + ARC-ADR-014 governance).
- Arrow adds a dependency and is overkill for trivial reads (mitigate with an optional JSON projection).
- ADBC driver maturity varies by backend — must verify per connector before adoption.

### Option 2 — Separate UDA CDM + Arrow

**Pros:** Decouples the UDA's release cadence from middle-core; the adapter evolves independently.

**Cons:** Directly contradicts the "one model, many projections" thesis; creates a second canonical schema to keep aligned with `model.yaml` — the exact projection-drift risk the platform warns against.

### Option 3 — JSON-Schema CDM + JSON values (no Arrow)

**Pros:** Simplest; language-neutral; no Arrow/ADBC dependency; easy to eyeball on the wire.

**Cons:** Loses columnar efficiency for analytical/bulk reads (D5); JSON's weak typing blurs decimals/timestamps/nested structures (D3); larger payloads at BigQuery volumes.

---

## Related Decisions

- **ARC-ADR-005:** backend-core OpenAPI contract — the contract-first discipline this decision extends to the data-value layer; the UDA's surface is published the same way.
- **ARC-ADR-014** (backlog): Contract versioning & drift governance — `SchemaVersion`/deprecation policy that keeps this CDM stable for consumers (the RT6←RT7 safety net).
- **ARC-ADR-016** (backlog): Ontology representation (reification + hyperedges) — the canonical model this CDM projects from also carries the reified-relation vocabulary.
- **ARC-ADR-012** (backlog): Read-query caching — cache keys/serialization depend on the canonical result type chosen here.
- **ARC-ADR-018** (backlog): Async/job-execution — `dlt` pipelines load *into* this canonical model.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
