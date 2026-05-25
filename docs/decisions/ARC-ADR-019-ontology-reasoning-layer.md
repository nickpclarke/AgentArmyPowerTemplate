# ARC-ADR-019 — Ontology + Reasoning Layer (pluggable gUFO ‖ BFO profiles, behind the UDA)

| Field | Value |
|---|---|
| ID | ARC-ADR-019 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — to be decided; spike backend-core #65 complete, evidence folded in below) |
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

**To be decided** by Architecture Review (HITL — the hub owner decides; this stays a Proposed
stub with a recommendation, not a unilateral call). The gating spike has now **run** and
confirms the direction — the recommendation below is upgraded from "conditional" to "Accept
Option 1," pending the owner's call.

### Evidence from the spike (backend-core #65)

The time-boxed PoC (`spikes/ontology-reasoning/`, self-contained: no live ArcadeDB, no app
import, no network, no Java) proved the **export → RDF → reason → materialize** loop end-to-end
on a 4-vertex snapshot, deriving facts plain graph traversal cannot:

- **Type propagation** — `alice` (asserted only as `Employee`) is classified up the gUFO chain
  `Employee → Person → FunctionalComplex → Object → gufo:Endurant`.
- **Inverse-edge materialization** — `alice worksAt acme` derives the write-back edge
  `acme employs alice`.
- **Relator range** — `Employment` relator's `gufo:mediates` range classifies its participants.
- **Indirect inconsistency** — asserting `alice` is also an `Organization` violates the
  `Person ⊓ Organization` disjointness **only after** reasoning (because `Person` is *inferred*),
  which a traversal-only system would miss. This is the *traversal ≠ inference* point, demonstrated.

The foundational ontology is a **pluggable profile** (`GufoProfile` works; `BfoProfile` is the
parallel-pipeline placeholder), so BFO slots in as *a new profile + a TBox file*, not a rewrite —
confirming D3.

**Build-vs-buy (reasoner runtime), from the spike:** **rdflib + owlrl** (OWL 2 RL forward
chaining, pure Python, no Java, zero infra) is the recommended seed. Escalate to **owlready2 +
HermiT/Pellet** only if full OWL 2 DL classification is needed; **Oxigraph** (Rust) is a strong
RDF/SPARQL *side-store* candidate (no DL reasoner) aligned with `rust-api-v2`; **Z3** is added for
the BFO profile's beyond-DL (Common-Logic) axioms; **RDFox/GraphDB** only if data outgrows
in-process reasoning. Watch closure size at scale.

### Recommendation note (not a decision)

**Accept Option 1** (pluggable gUFO ‖ BFO, reasoner-behind-the-UDA, gUFO-first), with **rdflib +
owlrl** as the seed reasoner runtime. The spike proved the export→reason→materialize boundary is
practical, addresses the real gap (inference) without re-importing a declined engine (#60), keeps
the bet reversible (D2/D6), and extends the platform's "one model, many projections" thesis to
reasoning (D3). Keep the reasoner runtime pluggable — don't pre-commit beyond the rdflib+owlrl
seed.

**Hardening that must land before any untrusted RDF/ontology is parsed (carry into the Story):**
rdflib's RDF/XML path uses `xml.sax` and resolves external entities — an **XXE/SSRF** exposure if
`format="xml"`/`application/rdf+xml` ever ingests untrusted input. Mandate **`defusedxml`** +
disabled entity resolution. But `defusedxml` closes only the XML path: rdflib/owlrl can *also*
reach the network/filesystem via **`owl:imports`, linked contexts, and other format parsers** — so
the acceptance criteria must require **offline parsing/import for *all* accepted RDF formats** (no
network or local-file retrieval of imports/contexts), not just the XML case, to close the residual
SSRF/exfiltration gap. Also input-validate snapshot fields (`namespace`/`id`/`label`) before they
become URIRefs. The spike's hand-curated gUFO subset must be replaced with the canonical `gufo.ttl`
for production.

If materialization or reasoner cost proves impractical at scale, fall back to Option 3 and revisit
when a concrete inference requirement forces it.

## Pros and Cons of the Options

### Option 1 — Pluggable profiles, shared reasoner, behind the UDA (recommended)
**Pros:** addresses the inference gap; decoupled + reversible (ADR-001); gUFO + BFO both supported as swappable profiles; reuses the factory's gUFO OWL; no native/Trinity dependency. **Cons:** new moving part (export/reason/materialize loop); a reasoner runtime to operate; materialization-freshness semantics to define.

### Option 2 — gUFO only
**Pros:** simplest path to inference; one profile to operate. **Cons:** forecloses the BFO/regulatory-rigor path that #62 argues is genuinely worth keeping (D5).

### Option 3 — No reasoning layer (status quo)
**Pros:** zero cost/risk now. **Cons:** the inference gap — the actual prize identified in #60 — stays unaddressed; the generated OWL stays inert documentation.

## Sources / references

- Research: backend-core #60 (`0001-trinity-graph-engine.md`), #62 (`0002-ontology-reasoning-layer.md`)
- Spike: backend-core #65 (runnable gUFO reasoning PoC + store/reasoner build-vs-buy; `spikes/ontology-reasoning/`)
- Inputs: middle-core #49 (gUFO OWL emitter); the Labs `knowledge-graph-snapshot` object + "one model, many projections" vision
- Related: [ADR-005](ARC-ADR-005-backend-core-openapi-contract.md), [ADR-009](ARC-ADR-009-canonical-data-model-arrow.md); ADR-BACKLOG #016 (ontology *representation* — reification/hyperedges — distinct from this *reasoning* layer; the two compose)
