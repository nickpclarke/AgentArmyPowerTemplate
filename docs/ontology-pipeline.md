# The Ontology Pipeline

Turn unstructured documents into **proven, queryable, provenance-tracked knowledge**
— not plausible LLM extractions. This is the implemented pattern; the decisions
behind it are [ARC-ADR-030](decisions/ARC-ADR-030-data-to-ontology-ingestion-pipeline.md)
/ [032](decisions/ARC-ADR-032-ontology-sift-sort-authoring-loop.md) /
[033](decisions/ARC-ADR-033-fsharp-ontology-compiler-core.md) /
[019](decisions/ARC-ADR-019-ontology-reasoning-layer.md) /
[016](decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md); the
broader vision is the Labs north-star (`obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md`).

## The pattern in one line

**The LLM proposes; the formal layer disposes.** A concept reaches the canonical
graph only when it is *proven* — schema-valid, anti-pattern-free, reasoner-consistent
across a dual gUFO+BFO grounding, and SHACL-conformant — and every step is traceable
back to its source. *Snapped, not plausible.*

## What a document becomes — four substrates

```
document (.docx/.pdf/.txt)
  ├─ ingest ───────────────▶ VECTOR INDEX     (ArcadeDB LSM_VECTOR, Cohere embed-v-4-0)
  └─ sift (Cerebras) ─┬────▶ HOLOGRAPHIC LPG  (ArcadeDB — every candidate + lifecycle state)
                      ├────▶ MID-LEVEL MAP    (proven concepts aligned to business-mid.ttl)
                      └────▶ CANONICAL RDF     (Fuseki — only the PROVEN, + PROV-O lineage)
```

| Substrate | Store | Holds | Role |
|---|---|---|---|
| **Vector index** | ArcadeDB `LSM_VECTOR` | doc chunks + 1536-d embeddings | semantic retrieval (RAG) |
| **Holographic LPG** | ArcadeDB graph | every candidate + per-level results + `state` | the working/staging graph; **quarantine is a `state`**, not a separate store |
| **Canonical RDF** | Fuseki (TDB2, `/knowledge`) | only *proven* gUFO+BFO triples + lineage + mappings | the authoritative knowledge graph |
| **Mid-level map** | RDF (in the canonical graph) | proven concepts aligned to a shared vocabulary | cross-document **integration** layer |

The vector index and the ontology graph trace to the **same source document**, so a
consumer can pivot `concept → source span → chunk`.

## The discipline — propose → sift → snap | quarantine

The sift ladder ([ARC-ADR-032](decisions/ARC-ADR-032-ontology-sift-sort-authoring-loop.md)):

| Level | Gate | Proves |
|---|---|---|
| **L1** | JSON-Schema on the IR fragment | well-formed, valid stereotypes |
| **L2** | OntoUML anti-pattern check | role bindings reference declared entities |
| **L3** | OWL reasoner closure (owlrl) | **gUFO and BFO classifications agree** (an Event grounded to a Continuant is *inconsistent*, not merely odd) |
| **L4** | SHACL conformance (pyshacl) | relator under-mediation and other shape rules |
| *(prod)* | the Fuseki **sieve** (`sieve.sh`) | an independent SHACL re-check before promotion |

Only an all-green candidate **snaps** (projects to canonical RDF). Anything that
can't be proven within the repair budget lands in **quarantine** — retained with its
full violation report, never auto-promoted.

## Mid-level mapping — and the evidence ladder

A proven concept is still document-local (one doc's "Rumor" ≠ another's). The
**mid-level mapper** aligns it to a shared vocabulary (`business-mid.ttl`, ~40
business/epistemic/risk classes) so the fleet integrates across documents.

- **Primary signal — embedding cosine** in the *same* Cohere space the RAG index
  uses (a measurable number), gated by **gUFO archetype compatibility**: a reified
  relation may only map to a relator class; an occurrent never to an object.
- Thresholds → `skos:exactMatch` / `skos:closeMatch` / `rdfs:subClassOf`.
- **Below the floor → escalate** to the gateway model, and its verdict is **cited as
  PROV-O provenance** (`sift:citedSource "cerebras:zai-glm-4.7"`). A decision a
  measurable signal couldn't make is handed to a model — and the model is *named*.

Every mapping records its method, cosine, embed model, and any cited source. The
"propose / dispose" rule holds here too: the model only *picks* among cosine-ranked
candidates; it cannot invent a class.

## Functional core, imperative shell

The same `project` + sift logic exists in two forms ([ARC-ADR-033](decisions/ARC-ADR-033-fsharp-ontology-compiler-core.md)):

- **Imperative shell — Python** (`backend-core`): all the IO — HTTP, Cerebras gateway,
  Cohere embeddings, ArcadeDB, Fuseki. The live `/api/v1/ontology/*` routes.
- **Functional core — F#** (`tools/ontology-sift/fsharp`): the *provable*
  transformations. The category theory pays rent here: the IR is a **coproduct**
  (discriminated union), `project` is a **functor** (a catamorphism folding the
  fragment to triples), the ladder is a **Result monad** (L1 short-circuit) into a
  **Validation applicative** (L2–L4 accumulate), and the outcome is the coproduct
  `Snapped | Quarantined`. With `FS0025`-as-error, adding a stereotype case **fails
  the build** until every projection handles it — "snapped, not plausible" enforced
  by the compiler, not by tests. See `tools/ontology-sift/fsharp/README.md`.

## Provenance, end to end

PROV-O threads the whole chain, so the canonical commit is auditable:

```
source span ─ wasDerivedFrom ─▶ concept ─ wasGeneratedBy ─▶ propose activity (proposer + prompt hash)
concept ─ skos:exactMatch/closeMatch/subClassOf ─▶ mid:Class
   └─ wasGeneratedBy ─▶ map activity (method, cosine, embed model, citedSource?)
```

## Run it

| Want | How |
|---|---|
| **See the whole thing** on a real doc | `backend-core/notebooks/ontology_pipeline_e2e.ipynb` → Run All (needs backend-core `:8000` + Fuseki `:3030`) |
| **Call the pipeline** | `POST /api/v1/ontology/pipeline` `{ "source_text", "source_doc", "proposer": "gateway" }` |
| **Prove the F# core** | `dotnet run --project tools/ontology-sift/fsharp` (parity doctor) |
| **Offline, no LLM** | `tools/ontology-sift/doctor.py` (fixture proposer; deterministic) |

## Where it lives

- `backend-core/app/ontology/` — `sift_engine.py`, `proposer.py`, `midlevel.py`,
  `pipeline.py`, `arcade_schema.py`, `api.py`; `discipline/` (IR schema, gUFO/BFO-lite
  TTLs, SHACL shapes, `midlevel/business-mid.ttl`).
- `tools/ontology-sift/` — the Python reference + offline doctor + `spikes/` +
  `fsharp/` (the compiler core).
- Contract: `backend-core/contracts/backend-core.openapi.json` (`/api/v1/ontology/*`).

## Status

Implemented and proven live on the "Three makes a tiger" document (2026-05-29):
57 chunks → vector index; one fragment **snapped** (all four gates green); 11 concepts
mapped (3 exact / 4 close / 4 escalated + cited `zai-glm-4.7`); 183 triples in Fuseki.
Shipped in backend-core #130 and hub #336.
