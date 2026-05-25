# Ontology Pipeline (North-Star)

> **Status:** living design doc — current thinking for the ontology-derived generative pipeline that the middle-core runtime is growing into. This page reconciles the two raw idea notes ([Ontology.md](https://github.com/nickpclarke/AgentArmy/blob/main/planning/ideas/Ontology.md), [ontology2.md](https://github.com/nickpclarke/AgentArmy/blob/main/planning/ideas/ontology2.md)) into one authoritative direction. Where they conflicted, the decision is recorded in [Rejected alternatives](#rejected-alternatives).

> **One-line thesis** — Treat the ontology as a **source model that compiles into many projections** (semantic, constraint, runtime, persistence, verification, provenance) rather than a single ontology-to-code script. The same model that humans and agents edit drives every generated surface, and an AI agent consumes the result over a stable API without ever touching generated code.

## Core principle: a multi-representation compiler, congruence-first

The source of truth is an **OntoUML / UFO / gUFO-aligned conceptual model**. "Congruence-first" means the machine representation must stay aligned with external reality: we keep semantics and proofs in a dedicated control plane, and let the database be the fast, practical persistence layer — not the arbiter of meaning.

```text
[OntoUML / UFO source model]
          |
          v
[Canonical Ontology IR]  (YAML / JSON-Schema, LinkML-like)   <-- humans + agents edit here
          |
   +------+-----------------------------------------------+
   |          |          |           |          |         |
   v          v          v           v          v         v
[OWL 2 DL]  [SHACL]   [C# hyper-   [ArcadeDB   [Alloy/Z3] [PROV-O +
 /gUFO      /ShEx      graph        multi-model  proofs     hash manifest
 reasoning  validation runtime]     persistence]            + VC/DID anchor]
```

Architectural rule: **do not collapse semantic ontology, runtime graph, database schema, and proof artifacts into one representation.** Maintain explicit projections with a deterministic generator between them.

## Semantic spine (UFO / gUFO + alignments)

gUFO is the core identity/aspect discipline layer (a lightweight OWL 2 DL implementation of UFO). Downstream agents pull these vocabularies to build their validation indices:

| Layer | Vocabulary | URI |
|---|---|---|
| Foundational | gUFO | `https://raw.githubusercontent.com/nemo-ufes/gufo/master/gufo.ttl` (ns `http://purl.org/nemo/gufo#`) |
| Software-eng mid-level | SEON | `https://raw.githubusercontent.com/fabianoruy/SEON/master/seon.owl` |
| Enterprise (minimalist) | gist | `https://ontologies.semanticarts.com/o/gistCore13.0.0.ttl` |
| Financial | FIBO | `https://spec.edmcouncil.org/fibo/ontology/master/latest/AboutFIBOProd.ttl` |
| Time | OWL-Time | `https://www.w3.org/ns/time.ttl` |
| Provenance | PROV-O | `https://www.w3.org/ns/prov-o.owl` |
| Observation | SOSA | `https://www.w3.org/ns/sosa.ttl` |
| Catalog | DCAT | `https://www.w3.org/ns/dcat.rdf` |

Today the repo references two local ontologies (`model/middle-core/ontology/middle-core.ttl`, `top-level-ufo-lite.ttl`) as a gUFO bridge. The URIs above are the upstream catalog we vendor/pin from as the pipeline matures.

> [!note] Offer both upper ontologies (UFO **and** BFO)
> UFO/gUFO is our **primary** authoring + reasoning discipline. We also want a **BFO 2020 + CCO** alignment for interop with [[IKW-GraphEngine (Parallel Track)]]. Treat the upper-ontology grounding as *another projection*: keep one OntoUML-stereotyped IR and emit **both** alignments (gUFO OWL + BFO Common Logic), shipping a documented mapping + divergence list rather than a lossless round-trip.

## Canonical IR — the nervous system

A YAML/JSON-Schema model (LinkML-like) is the stable transformation target every generator, source-generator, validator, and CI step reads. It must express types with stereotypes (`kind`, `subkind`, `role`, `phase`, `relator`, `event`, `situation`, `quality`, `mode`, `category`, `mixin`), **n-ary relations as first-class relators**, constraints, and per-element provenance.

In this repo that role is played today by [`model/middle-core/model.yaml`](https://github.com/nickpclarke/AgentArmy/blob/main/model/middle-core/model.yaml) — a minimal first cut of the IR (object types, data objects, relationships, state machines, scenarios, projections, use-case traceability).

## Runtime model — hypergraph, congruence-first

The in-memory model is **hypergraph-first**, not RDF-first or binary-property-graph-first. OntoUML relators, commitments, situations, events, evidence bundles, and process states usually involve **more than two participants**, so relationships become first-class objects with role bindings:

```text
MitigationCase
  role: mitigatedRisk     -> Risk
  role: mitigatingControl -> Control
  role: accountableOwner  -> Person
  role: evidence          -> EvidenceBundle
  role: effectiveDuring   -> TimeInterval
```

### Bitemporal, event-sourced state

State changes are **not overwritten**. Each change is appended as a point-in-time delta event (a semantic diff) triggered by a `gufo:Event`, carrying temporal validity (`validFrom` / `validTo`). This separates **Endurants** (durable objects) from **Perdurants** (events), and gives every object a time-series record of how it was classified in the ontology at each point in time. Provenance links deltas via `prov:wasGeneratedBy`.

## Persistence — ArcadeDB multi-model

ArcadeDB is the single persistence engine, used for what it is good at, while OWL/SHACL/provers stay upstream and beside it:

- **Graph topology** — vertices/edges stamped with temporal validity intervals. Hyperedges persist as **vertices** connected to participants through `BINDS_ROLE` edges (hyperedge-as-vertex).
- **Time-series** — high-frequency telemetry tracking Perdurants.
- **Document / SQL** — structured event payloads and rich metadata.
- **Vector** — semantic-retrieval sidecars for agent/LLM context.

> ⚠️ **Do not make ArcadeDB "be" the ontology.** ArcadeDB proves nothing about semantic correctness. Reasoning (OWL/gUFO), closed-world constraints (SHACL), and structural/arithmetic proofs (Alloy/Z3) are a separate control plane.

## Validation & proof — layered, because each tool proves a different thing

| Level | Tool | Proves |
|---|---|---|
| 1 Syntactic | JSON-Schema on the IR | well-formed model, unique IDs, valid stereotypes |
| 2 OntoUML/UFO | stereotype + anti-pattern checks | sound conceptual modeling |
| 3 Semantic | OWL 2 DL / gUFO reasoner (HermiT/ELK) | satisfiability, disjointness, subsumption |
| 4 Constraint | SHACL (pyshacl) / ShEx | closed-world business rules, data quality |
| 5 Structural | Alloy | finite-scope counterexamples ("can this model exist?") |
| 6 Arithmetic/temporal | Z3 / SMT-LIB2 | cardinality math, ordering, allocation, time windows |

## Provenance & tamper-evidence

Every transformation emits **PROV-O** metadata and a hashable artifact manifest. If on-chain anchoring is used, anchor **only hashes/manifests/credentials** (canonical artifact hash, generated-code hash, validation-report hashes, PROV bundle, VC/DID envelope) — never the full ontology graph. DLT proves lineage and tamper-evidence; it does not replace semantic validation.

> **Naming:** "DLT" here means **distributed ledger technology** — distinct from this repo's data-load tooling (`dlt`) and the `dlt-engineer` agent.

## Where we are vs. the north-star

The middle-core runtime already implements the spine of this pipeline:

| North-star concept | Today in the repo | State |
|---|---|---|
| Canonical IR / nervous system | `model/middle-core/model.yaml` | ✅ minimal |
| Deterministic generated C#, never hand-edited, under `/generated` | `templates/middle-core/generated/*.g.cs` + generator | ✅ |
| Authoring loop (regen → validate → drift gate) | `tools/modelgen/regen.sh`, `.github/workflows/middle-core-model.yml` | ✅ |
| C# in-memory graph runtime | `ModelObjectGraph` | ✅ binary edges only |
| Agent access surface | GraphQL `/graphql` (schema + live graph) | ✅ |
| ArcadeDB persistence projection | `FakeArcadeDbProjectionPort` | ◻ stub |
| Provenance | evidence packs | ◻ lightweight ancestor |
| OWL/SHACL/Alloy/Z3 verification | `.ttl` referenced only | ◻ not loaded |
| Hyperedge-as-object | — | ◻ not yet |
| Bitemporal delta events | snapshot/overwrite graph | ◻ not yet |

## Roadmap — sequenced onto the loop

> **Deploy now (extends the loop already in place)**
> - **Vendor + pin the ontology URI catalog** above into `model/middle-core/ontology/` and add a CI link/resolve check (reuses the drift-gate pattern in `middle-core-model.yml`).
> - **Provenance manifest:** have the generator emit a `build-manifest.json` with per-artifact content hashes, drift-gated like the `.g.cs`. Cheap operationalization of the PROV-O mandate.
> - **Publish the IR/projection contract** (this page) so agents and source-generators target a stable shape.

**Next**

- **SHACL projection + `pyshacl` CI level** generated from `model.yaml` (validation Level 4).
- **Reified relationships (hyperedge-as-object)** in the IR, the C# runtime, and the GraphQL surface — the deepest structural change; do it before persistence hardens.
- **OWL/gUFO projection** + a reasoner smoke check (Level 3).

**Later**

- **Bitemporal, event-sourced state** (delta events, `validFrom`/`validTo`) over ArcadeDB graph + time-series.
- **Real ArcadeDB projection** (hyperedge-as-vertex DDL, round-trip tests) replacing the fake port.
- **Alloy/Z3 verification** (Levels 5–6) and **DLT anchoring** of artifact hashes.

## Coding-agent rules

- **Projection rule** — never collapse semantic ontology, runtime graph, DB schema, and proofs into one representation.
- **Hypergraph rule** — n-ary relations, relators, situations, commitments, events, and evidence bundles are first-class objects in memory; persist them in ArcadeDB as vertices joined to participants by role-binding edges.
- **Generated-code rule** — generated C# is deterministic, metadata-rich, and never hand-edited; everything goes under `/generated` (or Roslyn `.g.cs`).
- **Validation rule** — OWL/gUFO for reasoning, SHACL for closed-world data constraints, Alloy for structural checks, Z3/SMT for arithmetic/temporal/allocation.
- **Provenance rule** — every transformation emits PROV-O + a hashable manifest; DLT stores only hashes/manifests/credentials.

## Rejected alternatives

| Option | Decision | Why |
|---|---|---|
| **VelocityGraph** (pure .NET OODB as primary store) | ❌ Rejected | Pulls persistence off the multi-model engine; commercial licensing and uncertain maintenance make it a risky foundation. ArcadeDB already provides graph + document + time-series + vector. |
| **Microsoft Orleans virtual actors / `JournaledGrain`** as the persistence/agency layer | ❌ Rejected | Event sourcing is kept as a **data pattern over ArcadeDB**, not an actor-runtime rewrite. Orleans is a large architectural commitment that diverges from the current generator + graph + GraphQL loop. |

The valuable ideas from those notes — **bitemporal delta events** and **congruence-first design** — are retained above and ride on the ArcadeDB multi-model track.

---
*Canonical Labs (WIP) note — lives in the in-repo Obsidian vault (`obsidian/labs/AgentArmyLabs/`) so every agent (Claude, Codex, Copilot) can read and edit it in its checkout. Edit via PR; graduate the stable summary to `docs/` when it settles.*
