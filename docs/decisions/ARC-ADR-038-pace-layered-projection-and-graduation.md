# ARC-ADR-038 — Pace-Layered RDF↔LPG Projection: a Drift-Sensing Operational Frontier and Dream-Consolidated Ontology Graduation

| Field | Value |
|---|---|
| ID | ARC-ADR-038 |
| Status | Proposed |
| Date | 2026-05-30 |
| Deciders | Hub owner (Nicky Clarke) |
| Supersedes | — |
| Superseded by | — |
| Tags | ontology, pace-layering, lpg, rdf, projection, drift, emergence, graduation, dreaming, annealing, ufo, bfo, ice, provenance |

---

## Context and Problem Statement

The ontology pipeline already decides most of the loop: the canonical store + reasoner ([ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md)), the relator-vertex / typed-role-binding representation for n-ary, metadata-bearing relations ([ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md)), the gate-first ingestion pipeline ([ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md)), and the sift-sort authoring loop where **the LLM proposes and the formal layer disposes** ([ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md)). Every existing projection runs *ontology → code* (forge, [ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md)), *source → ontology* (ingest), or *staging-LPG → canonical-RDF* (snap).

What is **not** yet decided is the other direction and its consequence: how the canonical ontology projects **down** into a fast operational Labeled Property Graph (LPG) that (a) **enforces the ontology's schema + rules** on high-speed data, while (b) letting operators attach **dynamic, rigor-free metadata** for operational tailoring — and how useful structure that **emerges** in that fast layer can **graduate back up** into the canonical ontology *without corrupting it*.

The organizing principle is **pace layering** (Stewart Brand): the ontology is the **slow** layer (meaning, rules, rigor, changes rarely); the LPG is the **fast** layer (operations, speed, dynamic properties that need no ontological rigor). *Fast learns, slow remembers; fast proposes, slow disposes; the coupling between them must be loose enough that the fast layer can churn without whipsawing the slow one.* The fast layer's distinctive job is to **measure the value of, and changes in, meaning** (semantic telemetry), and to **note drift and emergence** — which may, optionally, be harvested for attention.

The decision: **what is the contract across the slow↔fast membrane** — the down-projection, the admission rules for fast-layer extensions, and the up-graduation of emergent structure — such that the fast layer is freely tailorable while the slow layer stays congruent, parsimonious, and provable?

This composes ADR-016/019/029/030/032 and is grounded in the Labs notes [Pace-Layering & the Dreaming Ontology](../../obsidian/labs/AgentArmyLabs/vision/Pace-Layering%20and%20the%20Dreaming%20Ontology.md), [Ontology-Pipeline](../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md), [Reification-and-Hyperedges](../../obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md), and [Evidence as a Primitive](../../obsidian/labs/AgentArmyLabs/vision/Evidence%20as%20a%20Primitive.md). The design was pressure-tested by three independent foundational reviews — UFO/OntoUML, BFO 2020/OBO, and KR&R/knowledge-engineering — whose verdicts converged and drove the final shape (see *Review findings*).

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Pace separation.** Slow ontology vs fast LPG, loosely coupled. Down = constraint; up = a slow, gated ratchet; shear is buffered (the fast layer absorbs volatility). |
| D2 | **The fast layer enforces a *shadow* of the rules, never the rules themselves.** Only A-Box instances cross the membrane; T-Box axioms (class expressions, restrictions, `rdf:List`/`owl:intersectionOf` chains) stay in the slow layer. The LPG carries cheap RDFS-level closure, not OWL-DL inferences. |
| D3 | **Extensions must be safe by construction.** Operator metadata is `ops:`-namespaced, physically cannot shadow a canonical IRI, carries mandatory metadata (owner, purpose, created_at, provenance, TTL, stability, promotion_status), and is garbage-collected when unused. |
| D4 | **The fast layer measures value-of and changes-in meaning** (semantic telemetry) — but those measurements are **Information Content Entities about the record** (IAO), never domain universals. Rigor-free + dynamical is *correct*, not a shortcut. |
| D5 | **Popularity nominates; classification decides.** A fast statistical signal may *flag* a candidate; only a slow **ontological classifier** may assign a category. Letting a fast signal make a slow commitment is a pace violation and the root cause of anti-patterns. |
| D6 | **Category soundness.** Graduation must **branch** (datum / intrinsic-moment / relational / occurrent / ICE / admin), not funnel everything toward "class"; disjointness axioms must be **ON** so miscategorization is *rejected*, not silently flattened. |
| D7 | **Congruence-first / propose-dispose** (ADR-032 lineage). Operations *propose* meaning; the formal layer *disposes*; nothing auto-promotes; non-snapping candidates are retained + visible, never silently dropped. |
| D8 | **Round-trip honesty.** The governed core is *data-round-trippable* only given an explicit invariant set; *referential identity* is a separate guarantee; the down-projection is **asymmetrically lossy** (binarized edges drop the time index), so relation reasoning stays in RDF/Common-Logic, never in the LPG shadow. |
| D9 | **Bitemporal + PROV audit** (ADR-016 D6 lineage). Extensions, promotions, and dream-consolidations are all recorded as provenance events; no silent deletes; "evidence as a primitive." |

---

## Considered Options

1. **Pace-layered membrane: drift-sensing frontier + dream-consolidated graduation** *(recommended)*. Three LPG zones (CANON / FRONTIER / CANDIDACY), one membrane enforcer, a two-stage graduation (**NOMINATE** fast / **CLASSIFY→DISPOSE** slow) with category gates, and slow-layer evolution modeled as **dream consolidation** (annealing + re-sparsification) rather than a per-item ratchet.
2. **Collapse the layers** — make the LPG *be* the ontology (or the reverse). Rejected: violates congruence-first; "storage-shaped truth"; the LPG proves nothing about meaning and cannot reason.
3. **Read-only projection, no operator extensions** — clean, but operations cannot tailor, and the whole point (capturing value/drift telemetry from real use) is lost.
4. **Auto-promoting ratchet (frequency-thresholded, single funnel)** — the naïve version the reviews refuted: popularity deciding category mints anti-patterns (relator-as-kind, mixin-as-identity, occurrent-as-continuant), thrashes, and corrupts canon.

---

## Decision Outcome

**Proposed: Option 1.** The membrane is the [ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md) "propose/dispose" philosophy generalized, with **operations as a new proposer** (alongside Cerebras-over-documents and structured lifting). Operations may *propose* meaning; only the slow ontological layer *disposes*.

### Three zones in the LPG

| Zone | Source | Mutability | Governed by |
|---|---|---|---|
| **CANON** | deterministic down-projection of canonical RDF; every element keeps its source `iri` | **read-only** (locked; drift-gated) | the ontology (ADR-016 representation) |
| **FRONTIER** | operator `ops:`-namespaced extensions + dynamic telemetry | writable, namespaced, TTL'd, GC'd | the admission enforcer |
| **CANDIDACY** | flagged emergent structure under sift/repair/validate | staging | the sift-sort loop (ADR-032) |

### The membrane (Projection & Admission Enforcer)

```
        ┌──────────── SEMANTIC / SLOW PLANE — canonical RDF · OWL · SHACL · reasoner (ADR-019) ────────────┐
        └───────────▲────────────────────────────────────────────────────────────────┬─────────────────────┘
        promote (gated ratchet / dream-snap, ADR-032)                                  │ project down
        ═══════════ PROJECTION & ADMISSION ENFORCER (the membrane) ═════════════════════▼══════════════════════
        classify every write · namespace · stamp PROV-O · validate (closed-world) · drift-detect · note · GC
        ──────────────────────────────────────────────────────────────────────────────────────────────────────
        OPERATIONAL / FAST PLANE — LPG     [ CANON read-only ]  [ FRONTIER ops: ext ]  [ CANDIDACY staging ]
```

### Down-projection (CANON): RDF → LPG — only A-Box crosses (D2)

| RDF construct | LPG projection | Rule |
|---|---|---|
| IRI resource | node + reserved `iri` (canonical join key) | invertibility precondition (but see D8 / C4) |
| `rdf:type` | label(s) | T-box hierarchy stays slow; carry RDFS-materialized type closure only |
| datatype property | node property + `_rdf_datatype` (and `_rdf_lang` for tagged) sidecar | preserves XSD/decimal/lang on round-trip |
| binary object property | typed edge | edge type via a namespace registry (collision guard) |
| n-ary / metadata-bearing relation | **relator vertex + typed role-binding edges** | = ADR-016 verbatim; bitemporal + PROV on the relator |
| blank node | skolemized IRI + `_rdf_was_blank` + source-graph scope | **A-Box only**; T-Box blank nodes are *not* projected |
| `owl:sameAs` cluster | one elected canonical node + `_rdf_same_as_aliases[]` | **closure runs *before* projection** (else duplicate nodes) |
| inferred triples | tagged `inferred` overlay, excluded from mining | reason slow/open-world; never mine entailments as "novel" |

### The two-stage graduation (the ratchet, split on pace)

```
FAST ── STAGE 1: NOMINATE (continuous · statistical · rigor-free) ───────────────
  value (freq · fan-out · centrality · demand)  +  drift (SHACL-strain ·
  cardinality divergence · sense-split)  → time-series + hysteresis → FLAG
  (the measurements are ICEs — they NEVER graduate; they only point)
        │ a flagged candidate crosses the membrane
        ▼
SLOW ── STAGE 2: CLASSIFY → DISPOSE (rare · gated · categorical) ────────────────
  A. CATEGORY TRIAGE  ─┬─ ADMIN (cache/UI/TTL) ────────────▶ stays fast, never a term
     (BFO)             ├─ ICE about the record (score/tenant)▶ IAO annotation only
                       ├─ OCCURRENT/TEMPORAL (verified_by…) ▶ OCCURRENT ladder
                       └─ WD (world-descriptive) ─┐
  B. WD FORK ─────────────────────────────────────┼─ datum ─────────▶ stays a property
     (UFO)                                         ├─ intrinsic moment ▶ «quality» | «mode» (1 bearer, NOT an edge)
                                                   └─ relational ─┐
  C. RELATION GATE ────────────────────────────────┬─ formal (taller-than/part-of) ▶ typed edge, never a relator
     (UFO+BFO)                                      └─ material ▶ reify + pick realist shape:
                                                      relational-quality | roles+process | process+ICE (+ bind time-index)
  D. TYPE SORTER ── sortality → kind/subkind | category/mixin (req. ≥2 kinds);
     (UFO+OBO)        rigidity → subkind | phase/role; + genus-differentia,
                      one asserted is_a → BFO via reused CCO/IAO, opaque ID, reuse RO
  E. DISPOSE ── L2 anti-pattern · L5 Alloy · L3 reasoner (disjointness ON) · L4 SHACL ·
                CQs · instance dedup + duplicate-universal check · HITL signs the STEREOTYPE
                            ▼
                CANONICAL TERM ──▶ re-projected DOWN into CANON (read-only)
```

The recommender (Stage 1) **nominates**; the classifier (Stage 2) **decides**. FK-smell, frequency, and fan-out are *hints*, never gates.

### Slow-layer evolution = dream consolidation, not a per-item ratchet

The slow layer does not react to each candidate. It **mostly sleeps**, and periodically **dreams**: an offline, attention-budgeted consolidation that *replays* harvested drift/emergence, *expands* the possibility space (entailment, recombination), then *anneals* toward a low-energy configuration and **re-sparsifies** (prunes redundancy, merges duplicate universals, deprecates dead structure). The "energy" being minimized is **description length + uncovered drift**, subject to **hard consistency + category well-formedness** — so the UFO/BFO gates are not a checkpoint, they are the *shape of the basin the graph settles into*. **Dreaming is free; crystallization is gated and recorded** (every consolidation is a PROV-O event: merged X,Y→Z, pruned W, because…). Re-sparsification *is* the demotion/GC path; the cooling schedule *is* the hysteresis that prevents thrash. Full treatment: [Pace-Layering & the Dreaming Ontology](../../obsidian/labs/AgentArmyLabs/vision/Pace-Layering%20and%20the%20Dreaming%20Ontology.md).

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | Owns the operational LPG, the membrane/admission enforcer, the FRONTIER + CANDIDACY zones, the Stage-1 recommender, and the dream-consolidation orchestrator; projects canon down and snaps promotions up to Fuseki (ADR-019). |
| canonical store | Fuseki (ADR-019) | Holds slow-layer truth; runs reasoner (gUFO ‖ BFO) + SHACL; the only arbiter of meaning. |
| forge | nickpclarke/agentarmy-forge (ADR-029) | Emits the deterministic CANON down-projection DDL/mapping (drift-gated), mirroring the RT5 "generate DDL from modelgen" pattern. |
| persistence | ArcadeDB / (candidate: Postgres + Apache AGE) | Fast-layer LPG. AGE is a strong candidate: JSONB for rigor-free metadata, SQL for value/drift measurements, pgvector for sense-drift/dedup, RLS/triggers as the admission membrane (OQ3). |
| (agents) | hub `.claude/agents/` | `ontologist-ufo`/`ontologist-bfo` own the category classifier + the energy landscape (anti-pattern catalog, disjointness); `knowledge-engineer` owns the recommender, identity resolution, and dream runs. |
| (cross-cutting) | docs/contracts.md | New rows for the projection/mapping contract + the FRONTIER extension-metadata schema. |

---

## Pros and Cons of the Options

### Option 1 — Pace-layered membrane (recommended)
**Pros:** congruence-first preserved by construction (operations cannot mutate canon meaning); the fast layer is freely tailorable and is exactly where value/drift telemetry belongs; reuses ADR-016 representation, ADR-030 gate, ADR-032 propose/dispose, ADR-019 reasoning; the dream model gives thrash-resistance (cooling = hysteresis), demotion/GC (re-sparsification), and category-soundness (energy landscape) "for free." **Cons:** more machinery (membrane, recommender, dream orchestrator); the down-projection is lossy for relations (mitigated: reason in RDF/CL, treat LPG relations as a shadow); dream auditability + re-projection shear must be engineered (OQ4).

### Option 2 — Collapse the layers
**Pros:** one store, no membrane. **Cons:** storage-shaped truth; no reasoning; the exact anti-pattern the north-star forbids.

### Option 3 — Read-only projection, no extensions
**Pros:** simplest, no admission risk. **Cons:** operations cannot tailor; no telemetry; defeats the purpose.

### Option 4 — Auto-promoting frequency ratchet
**Pros:** fully automatic. **Cons:** popularity deciding category mints anti-patterns at scale; thrash; corrupts canon — refuted by all three reviews.

---

## Review findings that shaped this design

Three foundational pressure-tests converged on one verdict: *the naïve single-funnel ratchet let a fast-layer signal make a slow-layer commitment.* The fixes are gates, not a teardown.

- **UFO / OntoUML.** The ladder must **branch**, not funnel: add the **intrinsic-moment branch** (a property that "gains its own attributes" is a `«mode»`, not an edge); make the terminus a **sortality/rigidity sorter** (kind is rare and identity-bearing — never the default), not "a class." *"Popularity should nominate; classification must decide."* Replace gate "FK-smell → edge" with a material-vs-formal ontological gate. Upgrade claim C2: share the **whole category classifier** across projection-time and promotion-time, not just the reify rule.
- **BFO 2020 / OBO.** Add the **Category Triage** gate first: **WD** (world-descriptive → domain-eligible) vs **ICE** (information about the record → IAO annotation only) vs **ADMIN** (directives → never a term) vs **OCCURRENT/TEMPORAL** (→ a parallel occurrent ladder; do not fossilize processes into relator vertices). Split rung-3 "relator" into **relational-quality / interdependent-roles+process / process+ICE**; force a **time-index** decision (BFO relations are ternary). Enforce OBO authoring discipline at mint (genus+differentia, single `is_a` to BFO via reused CCO/IAO, opaque ID, reuse RO). Keep disjointness axioms ON so miscategorization is unsatisfiable.
- **KR&R / knowledge-engineering.** "Lossless via preserved IRIs" is too strong — define a **minimal invariant set** (datatype, lang, multi-valued, named-graph, sameAs sidecars) and run `owl:sameAs` closure **before** projection. Mining needs guards (FK-smell false positives; ops-bookkeeping exclusion list; support/lift; type-entropy; rare-but-genuine override). Promotion needs **hysteresis** (time-series, sustained window) + a **deprecate-not-delete** path. Usage evidence must be **tamper-evident** (hash-chained, time-series, not a snapshot). Re-projection needs change-log/epoch drift detection; GC needs **tombstone + resurrection** to avoid silent loss of still-referenced extensions.

---

## Claims scorecard

| Claim | Verdict |
|---|---|
| **C1** property → edge → relator → class | **Refuted** as a single funnel → replaced by triage + WD-fork + sortality sorter (multi-destination) |
| **C2** same rule at projection & promotion | **Upgraded** → one shared *category classifier*, invoked both directions across the membrane |
| **C3** ops propose / formal disposes | **True with teeth** → disposal must judge *category* (not just consistency) and run with disjointness ON, else it corrupts by miscategorization |
| **C4** lossless via preserved IRIs | **Split**: *transport* round-trip is true *given the invariant set*; *referential identity* needs separate dedup + duplicate-universal gates; down-projection is asymmetrically lossy (time-index) |
| **C5** reason-RDF-open / validate-membrane-closed | **Defended** (the strongest idea) + scope OWL-vs-Common-Logic (temporal/ternary claims reason in CL; SHACL on the RDFS-materialized graph, not assuming OWL entailments) |

---

## Open Questions

1. **What wakes the dreamer** — clock (cadence) vs pressure (sleep when accumulated drift / free-energy crosses a threshold) vs attention (sleep only when budget is spent). This also sets the loop's *time constants*: drift-as-alarm wants low deadband/high recall; value-as-prioritizer wants high deadband/slow. The hub owner's lean (2026-05-30): **just note drift + emergence; harvest for attention** — i.e. observation-first, optional consolidation, not an aggressive controller.
2. **ICE handling** — a separate governed **information-artifact ontology** (IAO/CCO-aligned) for the telemetry/record-metadata, vs lightweight annotations. Keeps the domain ontology clean (orthogonality) either way.
3. **Substrate** — Postgres + **Apache AGE** for the fast layer (JSONB rigor-free metadata · SQL value/drift measurements · pgvector sense-drift/dedup · RLS/triggers as the admission membrane) vs a native LPG (Neo4j+GDS) vs a both-models engine (Neptune/ArcadeDB). The slow layer needs an RDF/OWL/SHACL + reasoner store regardless.
4. **Dream auditability + shear** — crystallization must be gated (only consistent, category-sound configurations) and recorded (PROV consolidation events with a merge/prune map); re-projection after a dream must let the fast CANON zone rebind gracefully (bitemporal, no whiplash).
5. **Energy function** — the MDL/parsimony weighting; whether category-soundness enters as a hard constraint (infeasible region) or a steep soft penalty; competency-question coverage as the explanatory-power term.

---

## Related Decisions

- **[ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md):** relator-vertex + role-binding — the CANON down-projection of n-ary relations, and the reify gate reused at promotion time.
- **[ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md):** the slow-plane store + reasoner (the disposer; where dreams crystallize).
- **[ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md):** the gate-first ingestion pipeline — operations becomes another upstream proposer behind the same gate.
- **[ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md):** propose/dispose, the holographic LPG staging graph, quarantine, PROV-O lineage — reused for CANDIDACY and crystallization.
- **[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md):** forge — emits the deterministic CANON projection DDL.
- **[ARC-ADR-026](ARC-ADR-026-data-vault-2-1-methodology.md):** raw-vs-business split — the FRONTIER/CANON analogue and same-as/identity-resolution patterns.
- **[ARC-ADR-001](ARC-ADR-001-hitl-decision-point-pattern.md):** HITL — adjudicates the *stereotype* at crystallization, not just the schema diff.
- **Labs:** *Pace-Layering & the Dreaming Ontology*, *Ontology-Pipeline*, *Reification-and-Hyperedges*, *Evidence as a Primitive*, *Governance in the Model*.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-30 | Claude Code (assisted) | Initial Proposed — pace-layered RDF↔LPG projection with a drift-sensing operational frontier and dream-consolidated graduation; folds in the UFO / BFO / KR&R pressure-test findings; composes ADR-016/019/029/030/032. |
