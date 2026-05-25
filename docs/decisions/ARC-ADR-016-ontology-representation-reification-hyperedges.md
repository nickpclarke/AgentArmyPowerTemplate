# ARC-ADR-016 — Ontology Representation: Reification + Hyperedges (relator-vertex + typed role-binding)

| Field | Value |
|---|---|
| ID | ARC-ADR-016 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — hub owner decides) |
| Supersedes | — |
| Superseded by | — |
| Tags | ontology, reification, hyperedge, relator, gufo, ufo, n-ary, bitemporal, prov, middle-core, backend-core, arcadedb |

---

## Context and Problem Statement

A binary `(from, relationship_type, to)` edge cannot express a single fact that ties **3+ participants** together, cannot carry metadata **about the relationship as a whole** (time, provenance, confidence), and cannot be the **subject of a further relationship** (statements-about-statements). The platform's material relations — ingest-evidence (source + chunks + exercise + evidence), decisions, mandates, mitigations — are exactly these n-ary, metadata-bearing, reference-able relations.

The decision: **what is the canonical representation of n-ary / reified relationships** across the model factory, the canonical model (ADR-009), and ArcadeDB?

This is the **representation** decision; it composes with — and is distinct from — **ARC-ADR-019** (the *reasoning* layer). Research synthesis lives in the Labs note *Reification-and-Hyperedges*; a working implementation already exists in **middle-core #61** (issue #38).

## Decision Drivers

| # | Driver |
|---|---|
| D1 | Express **n-ary** relations (3+ participants as one semantic unit), not just binary. |
| D2 | A relationship needs **its own identity/lifecycle** and must carry whole-relation metadata (time, provenance, confidence). |
| D3 | **Statements-about-statements** — a relation must be able to participate in further relations (reification). |
| D4 | **gUFO/UFO alignment** — a relator is an *endurant* mediating participants via typed roles; consistent with the model-driven "one model, many projections" thesis and ADR-019 reasoning. |
| D5 | **Additive / non-breaking** — today's binary edges must keep working; the first slice cannot regress the knowledge-drop scenario. |
| D6 | **Bitemporal + PROV** placement must be unambiguous and audit-safe (no in-place deletes). |
| D7 | Efficiently **implementable on ArcadeDB** (LPG, index-free adjacency). |
| D8 | **Reify judiciously** — a rule, not a reflex: reify only material relations with identity/lifecycle, >2 participants, whole-relation metadata, or onward participation; never formal relations (parthood, subset). |

## Considered Options

1. **Relator-vertex + typed role-binding (hyperedge-as-vertex)** *(recommended; implemented in #61)*. Reify an n-ary relation as a first-class **relator vertex** joined to each participant by a typed **role-binding** edge. Bitemporal (`valid_from`/`valid_to`/`recorded_at`/`superseded_at`) + PROV metadata sit **on the relator**, never on participants. A binary edge is a **degenerate 2-role relator** → existing edges are additive, not breaking. gUFO **Relator** category; W3C "n-ary relation = a class + binary role properties" is exactly this pattern.
2. **Binary relationships only (status quo)**. Keep `(from, type, to)`. Simplest; cannot express n-ary, whole-relation metadata, or statements-about-statements — the gap this ADR exists to close.
3. **Edge properties (LPG edge attributes)**. Put link data on the edge. Carries metadata for *binary* links but the relation is not a first-class object, can't be n-ary, can't be referenced by further relations, and isn't gUFO-aligned.
4. **RDF reification / RDF-star**. Statement-level metadata on triples. A different storage paradigm; our metadata belongs on the relator *vertex*, not bare triples — relevant only if we ever expose SPARQL over ArcadeDB.

## Decision Outcome

**To be decided** by the hub owner (Proposed stub — options + recommendation, not unilateral). Queued **Proposed** with a working implementation already attached.

### Evidence from the implementation (middle-core #61 / #38)

PR #61 implements **Option 1** as an *additive* `hyperedges:` section in `model.yaml`:
- n-ary relations reified as gUFO **Relators**; a role can target **another hyperedge** (statements-about-statements / reification).
- Projected through **all** generated artifacts: C#/JS `HyperedgeContract` (with the `Relator` gUFO category + `IsHyperedge`/`RolesOf`/`RoleTarget`/`HyperedgeParticipates` enforcement API), OWL, SHACL, RDF fixture, LinkML, ModelSummary.
- **Validation** rejects <2-role hyperedges, unknown/self role targets, IRI/property-suffix collisions, and bad qualifier types (operationalizing the **RelOver** anti-pattern guard + the ORM ≥(n-1) uniqueness smell check from the research).
- Green: `owl_check.py` (L3) passes; `python -m unittest` **53 passed / 3 skipped** incl. new hyperedge/reification tests.

### Recommendation note (not a decision)

**Accept Option 1** — relator-vertex + typed role-binding. It's the only option that satisfies D1–D4 together, it's gUFO/UFO-grounded (W3C n-ary pattern, not an ad-hoc hack), and #61 proves the additive path (D5): binary edges become degenerate 2-role relators with current scenarios/tests untouched. Persist as ArcadeDB `RelatorVertex` + `RoleBinding` edges with composite `(relator_type, valid_from, valid_to)` + `role_name` indexes (D7); put **bitemporal + PROV on the relator**, version by appending (never deleting) for audit safety (D6). Enforce the **reify-judiciously** rule (D8) — don't reify formal relations.

Open sub-questions to settle in the full ADR: cardinality enforcement tier (lean: generate-time + runtime, DB as backstop); UFO qua-individuals (defer until a concrete need); aligning the relator's `valid_from`/`recorded_at` with the global temporal tick from the Ontology-Pipeline.

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | model factory — **implemented** (#61): `hyperedges:` IR + projections + validation; generator-first |
| backend-core | nickpclarke/backend-core | ArcadeDB schema (`RelatorVertex` + `RoleBinding` edges, indexes); canonical-model binding (ADR-009) |
| frontend-core | nickpclarke/frontend-core | renders reified relations / role bindings in generative UI |

## Pros and Cons of the Options

### Option 1 — Relator-vertex + typed role-binding (recommended)
**Pros:** expresses n-ary + metadata + statements-about-statements (D1–D3); gUFO-aligned (D4); additive (binary = 2-role degenerate, D5); bitemporal/PROV on the relator, audit-safe (D6); proven on ArcadeDB via #61 (D7). **Cons:** an extra hop (participant → role-binding → relator) — mitigated by index-free adjacency + composite indexes; RelOver/cardinality discipline must be enforced (already in #61's validation).

### Option 2 — Binary only (status quo)
**Pros:** simplest, nothing to build. **Cons:** the whole gap remains — no n-ary, no whole-relation metadata, no reification.

### Option 3 — Edge properties
**Pros:** cheap link metadata for binary edges. **Cons:** not first-class, not n-ary, not referenceable, not gUFO-aligned.

### Option 4 — RDF reification / RDF-star
**Pros:** standards-based statement metadata. **Cons:** different paradigm from the LPG/relator-vertex model; only relevant under a future SPARQL surface.

## Related Decisions

- **ARC-ADR-009** — canonical data model: the CDM projects the relator/role vocabulary.
- **ARC-ADR-019** — ontology + reasoning layer: *representation* (this ADR) and *reasoning* compose; the reasoner classifies over the reified relators.
- **ARC-ADR-011** — bitemporal/PROV metadata carries no secrets; standard handling.
- Labs: *Reification-and-Hyperedges*, *Ontology-Pipeline* (the temporal pulse the relator versions align to).
- Implementation: middle-core #61 (issue #38).

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architecture review (middle-core #61 evidence) | Initial Proposed draft — options + recommendation; implementation already landed additively; HITL decision pending |
