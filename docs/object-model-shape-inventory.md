# Object Model — Data-Shape Inventory & Object-Orientation Plan

> **What this is.** A single inventory of every data *shape* the platform supports or
> envisions, plus the plan to "object-orient" them — i.e. make each one a typed object the
> armies call directly, served by the **UDA** ([glossary](glossary.md#system-ontology--components-capabilities--surfaces))
> from the cost/latency-optimal backend. It is the shape-level companion to
> [contracts.md](contracts.md) (the inter-layer wire) and the
> [system ontology lexicon](../ontology/platform-self-model/generated/lexicon.yaml).

## The spine (what "object-orient a shape" means)

```
sift/sort (ADR-032)         forge (ADR-029)                    UDA (ADR-009/-016/-019)
raw → Cerebras proposes →   IR  ──emit──▶  ┌ Knowledge Graph ┐
formal layer disposes →     (ontology.ir   │ Vector DB       │ ─── read-seam ──▶ the armies
proven RDF in Fuseki        .schema.json)  └ Object Model    ┘     route by access pattern
        │                        ▲
   BE-7 snapshot ────────────────┘  (one IR in → many projections out; never collapse them)
```

- The **IR** ([`templates/ontology-project/ontology.ir.schema.json`](../templates/ontology-project/ontology.ir.schema.json))
  is the **single source of truth**. Every shape below is either *already expressible* in the IR,
  or a **gap** the IR/forge/UDA must grow to express.
- The **forge** emits per-target projections — emitters live in
  [`templates/forge-image/scripts/forge/emitters/`](../templates/forge-image/scripts/forge/emitters/)
  (`csharp.py`, `rust.py`, `typescript.py`, `python.py`, `sql.py`).
- **UDA serves** the typed objects. Per the [UDA labs note](../obsidian/labs/AgentArmyLabs/Universal%20Data%20Adapter.md)
  it needs three things from the forge that the IR does **not** yet carry — see *Gaps*.
- **Commons proof contract lane.** The `commons-core/ontology-sift` utility owns the shared
  `https://agentarmy.dev/ontology-sift/sieve-report.schema.json` vocabulary/validator;
  forge emits that report at certified-package time, and backend-core emits/consumes the same
  envelope at the sift/promotion API boundary. This is a contract artifact, not a new runtime
  tier decision.

## "One Model, Many Projections" — the three lockstep projections

| Projection | Backend (today) | IR flag | Object-oriented? |
|---|---|---|---|
| **Knowledge Graph** | ArcadeDB (LPG) + Fuseki (RDF) | `arcadedb`, `gufo`/`owl` | partial — binary edges live; relator-vertex envisioned (ADR-016) |
| **Vector DB** | local-embedder (#184) → vector store | _none yet_ | **gap** — no IR flag, no emitter |
| **Object Model** | served by UDA from any backend | `csharp`/`rust`/`typescript`/`python` | C# shipped; Rust shallow (see Gaps) |

## Shape inventory

Legend: **R** = real (code/schema exists) · **E** = envisioned (ADR/design only) · IR = expressible in the IR today.

### A. Ontology / semantic shapes (the authoring substrate — UFO/gUFO)

| Shape | Status | IR | Reference |
|---|---|---|---|
| Endurant types — `kind`/`subkind`/`phase`/`role`/`category`/`mixin`/`collective`/`quantity` | R | ✅ `types[].stereotype` | IR `$defs.stereotype` |
| Aspects — `mode`/`quality` | R | ✅ | IR `$defs.stereotype` |
| `relator` (n-ary, reified hyperedge-as-vertex) | E | ✅ `relators[]` | [ADR-016](decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) |
| Relations — `material`/`formal`/`mediation`/`characterization`/parthood | R | ✅ `relations[]` | IR `$defs.relation` |
| Perdurants — `event`/`situation` (process-aware) | E | ✅ `processes[]` | IR `$defs.process`, [ADR-038](decisions/ARC-ADR-038-unified-process-and-time-architecture.md) |
| BFO/CCO realist sidecar (continuant/occurrent) | E | ✅ `bfo_class`, `projections.bfo_cco` | [ADR-019](decisions/ARC-ADR-019-ontology-reasoning-layer.md) |
| Constraints — SHACL/ShEx/Alloy/SMT/OWL | R | ✅ `constraints[]` | IR `$defs.constraint` |

### B. Graph shapes

| Shape | Status | Reference |
|---|---|---|
| Property graph (LPG, binary edges) | R | ArcadeDB backend |
| RDF triples (canonical, SPARQL-queryable) | R | Fuseki; [ADR-019](decisions/ARC-ADR-019-ontology-reasoning-layer.md) |
| Hyperedge / n-ary as relator-vertex + role-binding edges | E | [ADR-016](decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) |
| Pace-layered RDF↔LPG projection (operational frontier ↔ graduated ontology) | E | [ADR-041](decisions/ARC-ADR-041-pace-layered-projection-and-graduation.md) |

### C. Relational / warehouse shapes (Data Vault 2.1)

| Shape | Status | Reference |
|---|---|---|
| Hub / Link / Satellite (raw vault, insert-only, hash keys) | R (tooling) | [`tools/data-vault/`](../tools/data-vault/), [ADR-026](decisions/ARC-ADR-026-data-vault-2-1-methodology.md) |
| Same-as link, computed satellite, reference table (business vault) | E | [ADR-026](decisions/ARC-ADR-026-data-vault-2-1-methodology.md) |
| PIT / Bridge tables | E | ADR-026 |
| Information marts — star / snowflake / OBT / graph | E (via dbt) | ADR-026; **dbt models not yet written** |

### D. Columnar / analytical

| Shape | Status | Reference |
|---|---|---|
| Arrow canonical type vocabulary (the UDA value boundary) | R | [ADR-009](decisions/ARC-ADR-009-canonical-data-model-arrow.md) |
| Parquet (object-storage destination) | R | `pipelines/dlt_pipelines/destinations.py` |
| Nested / repeated / decimal / temporal (Arrow-faithful) | R | ADR-009 |

### E. Event / stream / process

| Shape | Status | Reference |
|---|---|---|
| CloudEvents v1.0 over NATS JetStream | R | [ADR-022](decisions/ARC-ADR-022-event-bus-bridges.md) |
| BPMN 2.0 / CACAO 2.0 process projection (from `processes`) | E | IR `projections.bpmn`/`cacao`, [ADR-038](decisions/ARC-ADR-038-unified-process-and-time-architecture.md) |

### F. Temporal

| Shape | Status | Reference |
|---|---|---|
| Bitemporal validity (valid-time + transaction-time) on relators & processes | E | IR `relator.temporal`, [ADR-042](decisions/ARC-ADR-042-temporal-persistence-stamp-first-store-by-access-pattern.md) |
| HLC temporal envelope (process pinning) | E (self-test) | [ADR-038](decisions/ARC-ADR-038-unified-process-and-time-architecture.md), `tools/temporal/` |

### G. Document / vector / key-value / provenance

| Shape | Status | Reference |
|---|---|---|
| Document / nested JSON (dlt schema-inferred) | R | `pipelines/dlt_pipelines/` |
| Vector / embeddings | E | local-embedder image (#184); **no IR flag, no emitter** |
| Key-value identity-resolution index | E | [ADR-030](decisions/ARC-ADR-030-data-to-ontology-ingestion-pipeline.md) |
| PROV-O provenance / evidence-as-primitive | R (IR) / E (persisted) | IR `provenance`, `projections.prov`; BE-10 |

## Combinations & permutations worth object-orienting

The value isn't any single shape — it's the **compositions** UDA must serve transparently:

1. **Relator × bitemporal** — a reified n-ary fact that is *valid over an interval* and *recorded at a time*. The IR already carries `relator.temporal`; **no projection emits it yet**. This is the keystone object: it unifies graph + warehouse + audit.
2. **Object ⇄ graph ⇄ warehouse identity** — the *same* business object resolves to a vertex in ArcadeDB, a row in BigQuery, and a hub in the data vault. Requires **stable ids** (UDA need #1) + an identity-resolution index (ADR-030).
3. **Graph × vector** — a typed object that is both traversable (LPG) and semantically searchable (embeddings). Needs a vector projection the IR can't express today.
4. **Process × object (process-aware Object Model)** — `processes[].transforms` already links a perdurant to the endurant types it acts on; a BPMN/CACAO projection runs it on the DBOS durable runtime. Object + its lifecycle, together.
5. **Data Vault → information mart → ontology** — raw vault (dlt-loaded) → dbt business vault → mart → lifted into RDF for the forge. The warehouse becomes a *source* the sifter reads, closing the loop.
6. **RDF (graduated) × LPG (operational)** — pace-layered (ADR-041): hot operational edges in LPG, slow consolidated truth in RDF, the same object viewed at two clock speeds.

## Gaps (the concrete asks)

These are the blockers to "UDA works for all shapes, interoperably."

| # | Gap | Where | Owner |
|---|---|---|---|
| G1 | **IR has no access-pattern hint** per type (point / scan / traverse / search). UDA's planner can't route without it. | IR schema | forge team + UDA |
| G2 | **IR has no projection manifest** — which backend holds which type. UDA need #3. | IR schema | forge team + UDA |
| G3 | **No stable-id contract** so a BigQuery row and an ArcadeDB vertex are the *same* object. UDA need #1. | IR + ADR-030 | UDA + ingestion |
| G4 | **The rich shapes are flattened at the IR boundary, before any emitter runs.** forge has *two* IR notions: the OntoUML authoring IR ([`ontology.ir.schema.json`](../templates/ontology-project/ontology.ir.schema.json) — relators, processes, bitemporal) and forge's *internal* `Model`/`ObjectType` IR ([`forge/ir.py`](../templates/forge-image/scripts/forge/ir.py)) that the emitters actually consume. The emitters are faithful — `rust.py` emits fields, **binary relations**, and state enums — but n-ary **relators**, **processes**, and **bitemporal validity** have no slot in `ObjectType`, so they're lost in the RDF→ObjectType parse, not in the emitter. | forge | forge team |
| G5 | **No vector projection** — no IR flag, no emitter, despite local-embedder shipping. | IR + forge | forge team |
| G6 | **dbt models unwritten** — ADR-026 adopted Data Vault 2.1 + Datavault4dbt; only the model tooling (`tools/data-vault/`) exists, no `dbt_project.yml` / loaders / marts. | data-vault cluster | data-vault-engineer |
| G7 | **Bitemporal not persisted/emitted** — `relator.temporal` is in the IR but no projection materializes it (ADR-042). | forge + UDA | forge team |

## Plan (phased)

**Phase 0 — close the IR↔UDA contract (unblocks everything).**
- Add `access_pattern` (enum: point / scan / traverse / search / reason) and `persistence` (backend placement) to the IR `type`/`relator` schema → resolves **G1, G2**. Route via `api-designer` (IR is a contract) + an ADR.
- Define the **stable-id** rule in ADR-030's identity resolver → **G3**.
- Keep the sieve-report proof artifact aligned across Commons, forge, and backend-core so every
  snap/quarantine decision has the same portable evidence envelope.

**Phase 1 — make the forge emit the whole IR.**
- Enrich forge's `Model`/`ObjectType` IR + `rdf_parser.py` to carry relators (n-ary, role-bound) and processes, then teach **every** emitter (C#, Rust, TS, Python) to render them → **G4**. Gate with a golden corpus per target (ADR-029 already CI-gates byte-identical determinism).
- Add the **vector projection** (IR flag + emitter + embedding-dim from BE-4) → **G5**.
- Materialize **bitemporal** fields in every projection → **G7**.

**Phase 2 — warehouse + dlt close the loop.**
- Write the Datavault4dbt loaders + PIT/bridge + one information-mart projection → **G6** (data-vault-engineer).
- Wire **dlt as a first-party source** into the sifter (warehouse marts become an ontology source via BE-9 connector registry).

**Phase 3 — UDA serves the compositions.**
- Implement the planner routing table (UDA labs note) keyed on the new `access_pattern` hint.
- Prove the six compositions above end-to-end, each with a contract test.

## How dlt & dbt fit (one line each)

- **dlt** (real, `pipelines/dlt_pipelines/`) — ingestion: open-data + unstructured → warehouse/Parquet. The "first-party experience" is dlt as the *front door* of the sift→forge→UDA pipeline; `projections.dlt_anchor` anchors only hashes/manifests, never the graph.
- **dbt** (adopted, not coded) — SQL transformation *inside* the warehouse: raw vault → business vault → information marts (ADR-026). It sits *after* dlt and *before* the ontology lift — the "golden table" producer the forge can treat as a source.

---
*Generated 2026-05-31. Companion to [contracts.md](contracts.md), [glossary.md](glossary.md), and the [system-ontology lexicon](../ontology/platform-self-model/generated/lexicon.yaml).*
