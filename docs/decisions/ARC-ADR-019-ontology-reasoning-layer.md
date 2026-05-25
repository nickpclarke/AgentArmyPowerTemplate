# ARC-ADR-019 — Ontology + Reasoning Layer (pluggable gUFO ‖ BFO profiles, behind the UDA)

| Field | Value |
|---|---|
| ID | ARC-ADR-019 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — to be decided pending spike backend-core #63) |
| Supersedes | — |
| Superseded by | — |
| Tags | ontology, reasoning, owl, gufo, bfo, inference, uda, arcadedb, middle-core, backend-core |

---

## Context and Problem Statement

The platform has rich graph **storage** (ArcadeDB multi-model graph/vector + the UDA `GraphCapable` connector) and a model factory that already emits **gUFO-aligned OWL** for the middle-core model (middle-core #49, with reified lifecycle states/transitions). What it does **not** have is **inference** — deriving new facts/classifications from the knowledge graph under a formal ontology. Graph traversal ≠ reasoning.

Research [#60](https://github.com/nickpclarke/backend-core/pull/60) (`docs/research/0001-trinity-graph-engine.md`) established that the gap is reasoning (not storage) and that Microsoft Trinity is the wrong vehicle (dormant, redundant as storage, stack-friction). Follow-up [#62](https://github.com/nickpclarke/backend-core/pull/62) (`docs/research/0002-ontology-reasoning-layer.md`) established the legally-clean, decoupled path: take the **ontologies + ideas** (MIT / CC BY 4.0), not the Trinity-coupled C# code, and run reasoning as a separable capability.

**The decision: what is the architecture of the ontology + reasoning layer** — where it runs, how foundational ontologies plug in, and what reasoner powers it?

## Decision Drivers

| # | Driver |
|---|---|
| D1 | Reasoning must be **decoupled from storage** — ArcadeDB is a property-graph/vector store, not an OWL reasoner. |
| D2 | Consistent with ADR-001's n-layer doctrine: model it as a **UDA capability** (`ReasonerCapable`/`OntologyCapable` mixin), additive + replaceable, not a core swap. |
| D3 | The foundational ontology should be a **pluggable profile** — the Labs "one model, many projections" thesis extends to "one reasoner, many foundational ontologies." |
| D4 | **gUFO** is the lowest-friction first profile: native OWL 2 DL, single Turtle file (CC BY 4.0), closest to the OntoUML/model-driven vision, and the model factory already emits gUFO OWL. |
| D5 | **BFO 2020** must remain viable as a parallel profile for scientific/regulatory rigor (ISO 21838-2), which needs beyond-DL axioms (Z3/CLIF). |
| D6 | No heavy/native or single-maintainer runtime dependency baked into the core (the lesson from #60). Reasoner runtime stays pluggable + reversible. |
| D7 | Reuse must preserve licenses/attribution (MIT / CC BY 4.0); take ontologies from canonical upstreams, re-implement verification natively. |

## Considered Options

1. **Pluggable foundational profiles (gUFO ‖ BFO) over a shared reasoner, behind the UDA — gUFO first** *(recommended seed)*. Reasoning is a `ReasonerCapable`/`OntologyCapable` capability: export a `knowledge-graph-snapshot` subgraph → RDF → OWL reasoner → materialize inferred edges back into ArcadeDB. The foundational ontology is a loaded profile; the store + reasoner + mapping machinery is shared. Prove with gUFO (OWL 2 DL), add BFO 2020 (+ Z3 for beyond-DL) as the parallel profile.
2. **Single profile (gUFO only)**. Same decoupled architecture, but commit to gUFO and drop the BFO parallel pipeline. Simpler; loses the scientific/regulatory rigor path.
3. **No dedicated reasoning layer (status quo)**. Keep graph traversal + the generated OWL as documentation only; no live inference. Cheapest; the inference gap remains unaddressed.

## Decision Outcome

**To be decided** — deferred pending the evidence from the time-boxed spike **backend-core #63** (gUFO-over-a-snapshot PoC + a store/reasoner build-vs-buy note). This ADR is queued **Proposed** so the direction is on record and the spike has a target to confirm or refute. The HITL framing:

### Recommendation note (not a decision)

Lean **Option 1** (pluggable gUFO ‖ BFO, reasoner-behind-the-UDA, gUFO-first), conditioned on the #63 spike proving the export→reason→materialize boundary is practical. Rationale: it addresses the real gap (inference) without re-importing a declined engine (#60), keeps the bet reversible (D2/D6), and extends the platform's own "one model, many projections" thesis to reasoning (D3). The **reasoner runtime** (owlready2 Python vs Oxigraph Rust vs Z3 for BFO) is a build-vs-buy sub-decision the spike will inform — keep it pluggable, don't pre-commit. If #63 shows materialization or reasoner cost is impractical at scale, fall back to Option 3 and revisit when a concrete inference requirement forces it.

## Pros and Cons of the Options

### Option 1 — Pluggable profiles, shared reasoner, behind the UDA (recommended)
**Pros:** addresses the inference gap; decoupled + reversible (ADR-001); gUFO + BFO both supported as swappable profiles; reuses the factory's gUFO OWL; no native/Trinity dependency. **Cons:** new moving part (export/reason/materialize loop); a reasoner runtime to operate; materialization-freshness semantics to define.

### Option 2 — gUFO only
**Pros:** simplest path to inference; one profile to operate. **Cons:** forecloses the BFO/regulatory-rigor path that #62 argues is genuinely worth keeping (D5).

### Option 3 — No reasoning layer (status quo)
**Pros:** zero cost/risk now. **Cons:** the inference gap — the actual prize identified in #60 — stays unaddressed; the generated OWL stays inert documentation.

## Sources / references

- Research: backend-core #60 (`0001-trinity-graph-engine.md`), #62 (`0002-ontology-reasoning-layer.md`)
- Spike: backend-core #63 (gUFO reasoning PoC)
- Inputs: middle-core #49 (gUFO OWL emitter); the Labs `knowledge-graph-snapshot` object + "one model, many projections" vision
- Related: [ADR-005](ARC-ADR-005-backend-core-openapi-contract.md), [ADR-009](ARC-ADR-009-canonical-data-model-arrow.md); ADR-BACKLOG #016 (ontology *representation* — reification/hyperedges — distinct from this *reasoning* layer; the two compose)
