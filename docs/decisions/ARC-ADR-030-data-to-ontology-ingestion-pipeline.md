# ARC-ADR-030 — Data → Ontology Ingestion Pipeline as a backend-core Service (structured + unstructured sources, provenance-first, HITL-curated)

| Field | Value |
|---|---|
| ID | ARC-ADR-030 |
| Status | Proposed |
| Date | 2026-05-28 |
| Deciders | Hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | ontology, ingestion, knowledge-graph, backend-core, rdf, provenance, shacl, hitl, extraction, identity-resolution |

---

## Context and Problem Statement

[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md) gives the fleet a code generator (`agentarmy-forge`) that **consumes a validated ontology** and emits source for the spokes. Forge is a *pure, deterministic, verifiable* function precisely because it assumes a clean, shape-validated ontology already exists at its input — `GET /ontology/snapshot` (BE-7) hands it canonical RDF.

But **nothing produces that ontology yet.** Today operators hand-curate the model YAML; `POST /ontology/ingest` (BE-8, from ADR-029) is only a file-drop entry point. Standing up the real thing — turning the fleet's **structured** sources (DB rows, CSV/Parquet, OpenAPI/JSON schemas, existing relational models) and **unstructured** sources (PDFs, docs, prose, transcripts, HTML) into a populated, shape-valid ontology in the Fuseki store ([ADR-019](ARC-ADR-019-ontology-reasoning-layer.md)) — is a substantial, *distinct* problem with the **opposite** engineering character to forge:

| | Forge (ADR-029) | Ingestion (this ADR) |
|---|---|---|
| Direction | ontology → code | data → ontology |
| Determinism | fully deterministic (golden-checkable) | structured = deterministic; **unstructured = probabilistic** |
| Verification | compile + byte-identical golden | shape validation + provenance + human curation |
| Hard part | multi-target emit coherence | **identity resolution + confidence + HITL** |

The non-determinism, identity resolution, provenance, and human-in-the-loop curation make this big enough to own its own ADR rather than a phase of 029 (where it was flagged as Open Question 7).

The decision: **What is the architectural home for the data → ontology pipeline, and how is it structured so its non-determinism never leaks past the validation gate into the canonical ontology forge consumes?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Keep the deterministic side clean.** The probabilistic extraction must not leak past the SHACL/ShEx gate. Forge's purity (D1 of ADR-029) depends on the canonical graph being shape-valid and curated — the messy world stays on the *upstream* side of the gate. |
| D2 | **Provenance is first-class ("evidence as a primitive").** Every asserted triple is traceable to its source, extraction method, model+prompt version, confidence, and timestamp. An assertion without evidence is not admissible. Aligns with the Labs *Evidence as a Primitive* and *Governance in the Model* north-stars and reification/hyperedges ([ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md)). |
| D3 | **Structured and unstructured are different subsystems.** Structured lifting is declarative and reproducible; unstructured extraction is LLM/NER-based and non-deterministic. They share the downstream gate + graph but not the extractor. |
| D4 | **Identity resolution is central, not incidental.** Entities from different sources must merge (same-as) or the graph fragments into per-source islands. This is the load-bearing hard part, and it must be central (one resolver), echoing generator-first's single-source-of-truth logic. |
| D5 | **HITL for low-confidence.** Uncertain extractions route to a Decision Artifact (`hitl-coordinator`) and sit in a staging graph until accepted — they never auto-promote into the canonical graph. |
| D6 | **Idempotent + replayable.** Re-ingesting the same source must not duplicate entities; the structured path must be deterministically replayable; the unstructured path must be *auditable* (provenance pinned) even where not bit-reproducible. |
| D7 | **Co-locate with the store it writes.** The pipeline holds state (staging graph, identity-resolution index, provenance, HITL queue) and writes Fuseki on every batch — it belongs next to the RDF store, not a network hop away. |

---

## Considered Options

### Option 1 — A service in **backend-core**, co-located with the Fuseki store (recommended)

The ingestion pipeline is a service inside `backend-core` (the spoke that already owns the Fuseki RDF store per ADR-019 and the BE-7/BE-8 contracts). It orchestrates: **source connectors → extraction → identity resolution → staging graph (candidates + provenance) → SHACL/ShEx gate → HITL curation for low-confidence → canonical graph → snapshot + `fleet.ontology.changed` event**. The LLM/NER-heavy *unstructured* extraction may be delegated to a function-tier callout (or the LLM gateway, [ADR-021](ARC-ADR-021-llm-gateway.md)); orchestration, state, the validation gate, and graph writes stay in backend-core.

### Option 2 — A standalone function-tier container (symmetric with forge)

Mirror forge: a separate `agentarmy-ingest` function-tier image. Clean symmetry, but ingestion is **stateful** (staging graph, resolution index, provenance store, HITL queue) and writes Fuseki continuously — function-tier is for stateless bursty jobs ([ADR-023](ARC-ADR-023-container-tiering-strategy.md)), and this would create a second owner of the graph reachable only over the network.

### Option 3 — A separate spoke/repo

Its own repo + deploy surface. Splits the pipeline from the store it populates, adds a network hop on every write, and duplicates Fuseki access governance. Overkill for a producer that is fundamentally a front-end onto backend-core's graph.

### Option 4 — Push lifting into each source's owning spoke

Each spoke lifts its own data to RDF. No central identity resolution → entities from different sources never merge; the SHACL gate is reimplemented N times; drift is structural — the same failure mode ADR-029 Option 3 has.

---

## Decision Outcome

**Proposed: Option 1 — a service in backend-core.**

**Hub owner direction (2026-05-28):** the data → ontology pipeline is a **service in backend-core**. It is the *producer* front door of the ontology loop; forge (ADR-029) is the *consumer* back door; the canonical Fuseki graph between them is the single source of truth. Status stays *Proposed* pending the open questions below (extractor placement, identity-resolution strategy, provenance vocabulary).

### The pipeline, gate-first

```
structured sources ─┐                          ┌─ candidates land in
  (DB/CSV/OpenAPI)   │   deterministic lift     │  STAGING graph
                     ├─▶ extraction ─▶ identity ─▶ (+ PROV-O evidence,
unstructured sources │   probabilistic           │   confidence per triple)
  (docs/prose/...) ──┘   (LLM/NER, fn-tier)      │
                                                  ▼
                              ┌──────────── SHACL/ShEx gate ────────────┐
                              │  pass + high-confidence → auto-promote   │
                              │  pass + low-confidence  → HITL Decision  │
                              │  fail                   → reject + log   │
                              └──────────────────────────────────────────┘
                                                  ▼
                          CANONICAL graph (Fuseki) ─▶ snapshot (BE-7) ─▶ forge
                                                  └─▶ emit fleet.ontology.changed
```

The **gate is the airlock**: probabilistic, unverified, low-confidence material stays in the staging graph; only shape-valid, curated assertions cross into the canonical graph forge reads. This is what lets forge stay a pure deterministic function while its upstream is messy.

### Recommendation note (not a decision)

Phase it so the deterministic win lands first and the probabilistic hard part is incremental:

| Phase | Scope | Risk |
|---|---|---|
| **i0** | BE-8 file-drop ingest (already backlogged): RDF file → SHACL gate → canonical graph → snapshot + event. No extraction; the producer is hand-authored RDF. Proves the gate + snapshot + event loop end-to-end with forge. | Low. |
| **i1** | **Structured lifting**: declarative source→RDF mapping (RML/R2RML-style or a YAML mapping spec) for DB/CSV/OpenAPI. Deterministic, replayable, no LLM. Identity resolution v1 (deterministic business keys). | Medium — identity-key design. |
| **i2** | **Provenance + staging graph**: PROV-O evidence per triple (source, method, confidence), staging vs canonical named graphs, idempotent re-ingest via content-hash. | Medium — graph modeling (OQ2). |
| **i3** | **Unstructured extraction**: LLM/NER lifting (fn-tier callout or LLM gateway), confidence scoring, probabilistic identity resolution, **HITL routing** for low-confidence via `hitl-coordinator`. | High — non-determinism, curation UX, threshold tuning. |

Avoid **Option 2/3** — they put state and graph-ownership a network hop from the store. Avoid **Option 4** — it kills central identity resolution.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | Hosts the ingestion service; staging + canonical named graphs in Fuseki; implements BE-8 (ingest) + BE-7 (snapshot) + new source-connector registry + provenance/evidence schema; emits `fleet.ontology.changed` |
| (function) | hub `templates/…` (TBD) | Optional probabilistic-extractor function-tier image for the unstructured path (LLM/NER), or routed via the LLM gateway (ADR-021). Composition, not a new tier — see OQ1 |
| forge | nickpclarke/agentarmy-forge (ADR-029) | Downstream consumer of the canonical snapshot — unchanged, but now has a *real* producer instead of a hand-curated YAML |
| (cross-cutting) | docs/contracts.md | New backlog rows for the source-connector registry + provenance/evidence schema; BE-7/BE-8 promoted to Registry as the service ships |
| (agents) | hub `.claude/agents/` | Knowledge/ontology cluster owns the conceptual work: `ontologist-ufo`/`ontologist-bfo` author the target shapes (SHACL); `knowledge-engineer` owns population, identity resolution, and reasoner runs; `dlt-engineer`/`data-engineer` own source connectors |

---

## Pros and Cons of the Options

### Option 1 — backend-core service (recommended)

**Pros:** co-located with Fuseki (no network hop on writes, one graph owner); reuses backend-core's auth (ADR-002), async job model ([ADR-018](ARC-ADR-018-async-job-execution-model.md)), and event emitter ([ADR-022](ARC-ADR-022-event-bus-bridges.md)); the BE-7/BE-8 contracts already live here; symmetric mental model (backend-core = producer front door, forge = consumer back door).

**Cons:** grows backend-core's surface; the LLM-heavy unstructured path needs a toolchain/scale profile backend-core's runtime doesn't otherwise want (mitigated by delegating it to a fn-tier extractor — OQ1).

### Option 2 — standalone function-tier container

**Pros:** symmetry with forge; isolated toolchain.
**Cons:** ingestion is stateful — function-tier is for stateless bursty jobs; second owner of the graph; chatty cross-service writes.

### Option 3 — separate spoke/repo

**Pros:** independent deploy.
**Cons:** network hop on every write; duplicate Fuseki governance; over-built for a graph front-end.

### Option 4 — per-source lifting

**Pros:** each spoke owns its data.
**Cons:** no central identity resolution → fragmented graph; N copies of the SHACL gate; structural drift.

---

## Open Questions

1. **Extractor placement.** In-process in backend-core (deterministic structured lift) vs a function-tier callout / LLM gateway (probabilistic unstructured)? Lean: structured in-process, unstructured delegated to a fn-tier extractor (bursty, different toolchain, isolatable blast radius per ADR-023).
2. **Staging vs canonical graph modeling.** Separate named graphs in one Fuseki dataset, or separate datasets? Mirrors Data Vault raw-vs-business ([ADR-026](ARC-ADR-026-data-vault-2-1-methodology.md)) — candidates (raw) vs curated (business). Lean named graphs in one dataset for cheap promotion.
3. **Provenance vocabulary.** PROV-O vs a custom evidence vocab? Lean PROV-O + the Labs *Evidence as a Primitive* model, with per-assertion confidence/source attached via reification/hyperedges (ADR-016). Decide whether evidence is queryable RDF or a sidecar store.
4. **Identity-resolution strategy.** Deterministic business keys vs probabilistic / embedding-based entity linking; the same-as policy across sources (reuse the Data Vault same-as thinking, ADR-026). Threshold for auto-merge vs HITL-merge.
5. **HITL threshold.** What confidence band auto-accepts, auto-rejects, or routes to a Decision Artifact — and who is the assignee (human vs an AI app)? Ties into the HITL Decision Pattern.
6. **Idempotency + retraction.** Content-hash dedup for adds; how do source *updates* and *deletions* propagate? An ontology shrink (entity removed) cascades into a destructive forge PR (ADR-029 OQ5) — the ingest side must mark retractions explicitly, not silently drop triples.
7. **Reproducibility boundary.** The structured path must be deterministically replayable; the unstructured path is non-deterministic by nature. Pin model+prompt versions and store full extraction provenance so any run is *auditable* even when not *bit-reproducible* — and make that boundary explicit in the contract.

---

## Related Decisions

- **[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md):** Forge — the downstream consumer; this ADR is its producer (raised as ADR-029 Open Question 7).
- **[ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md):** Ontology reasoning layer (Fuseki + gUFO) — the store this service populates.
- **[ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md):** Reification + hyperedges — how per-assertion provenance/confidence attaches.
- **[ARC-ADR-026](ARC-ADR-026-data-vault-2-1-methodology.md):** Data Vault 2.1 — raw-vs-business split and same-as/identity-resolution patterns reused for staging-vs-canonical.
- **[ARC-ADR-021](ARC-ADR-021-llm-gateway.md):** LLM gateway — candidate path for the unstructured extractor's model calls.
- **[ARC-ADR-018](ARC-ADR-018-async-job-execution-model.md):** Async job model — ingestion is a long-running async job.
- **[ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md):** Event bus — the `fleet.ontology.changed` emit that triggers forge.
- **[ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md):** Container tiering — why orchestration/state stays in the application tier and only the bursty extractor is a candidate function-tier callout.
- **[ARC-ADR-005](ARC-ADR-005-backend-core-openapi-contract.md):** Backend-core OpenAPI contract — BE-7/BE-8 extend this surface.
- **[ARC-ADR-002](ARC-ADR-002-jwt-forwarding-auth-contract.md):** JWT-forwarding auth — ingest endpoints sit behind it.
- **Labs north-stars:** *Ontology-Pipeline*, *Evidence as a Primitive*, *Governance in the Model*, *Reification-and-Hyperedges*.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-28 | Claude Code (assisted) | Initial Proposed draft — data → ontology ingestion pipeline as a backend-core service; promoted from ARC-ADR-029 Open Question 7 per hub owner direction |
