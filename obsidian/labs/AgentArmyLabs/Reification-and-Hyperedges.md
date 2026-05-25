---
tags: [vision, ontology, middle-core]
---
# Reification & Hyperedges (research → design)

> **Status:** research synthesis + recommended design for the #96 reification slice — "relationships as first-class objects with role bindings." Companion deep-dive to [[Ontology-Pipeline]] (the *hypergraph rule*). Decisions here are the basis for implementation; nothing is built yet.

> **Decision (thesis):** Reify n-ary relations as a first-class **relator vertex** joined to participants by typed **role-binding** edges (*hyperedge-as-vertex*). Put bitemporal (`valid_from`/`valid_to`, `recorded_at`) and PROV-O metadata **on the relator**, never on participants. Treat today's binary `(from, type, to)` edge as a degenerate **2-role relator**, so the first slice is **additive** — the working knowledge-drop scenario stays untouched.

## Why reify at all (the rule, not the reflex)

Don't reify every edge. The settled criterion (UFO + LPG practice agree): reify when the relationship **(a)** has its own identity/lifecycle, **(b)** binds **>2 participants** as one semantic unit, **(c)** must carry metadata (time, provenance, confidence) as a whole, or **(d)** itself participates in further relationships. Formal relations (parthood, subset) are *not* reified; material relations (contracts, mandates, mitigations, ingest-evidence) are.

## The science (condensed)

| Body of work | What it gives us |
|---|---|
| **UFO relators** (Guizzardi) | The ontological basis: a relator is an *endurant* that mediates participants via typed roles → maps cleanly to a persistent vertex. Watch the **RelOver** anti-pattern (overlapping role-type extensions → ambiguous role assignment): keep role types disjoint or constrain. |
| **Object-Role Modeling** (Halpin) | All facts are n-ary role predicates. Gives a mechanical decomposition test: a uniqueness constraint must span ≥ *n-1* roles, else the relation is splittable (a smell). Use ORM as a **design-time validator** for the IR, not a runtime model. |
| **W3C "Defining N-ary Relations"** | The canonical justification: *reify the relation as a class, each role a binary property*. Hyperedge-as-vertex is this pattern, not an ad-hoc hack. Caveat: OWL cardinality can't restrict role *combinations* without extra axioms. |
| **RDF reification vs RDF-star (RDF 1.2)** | Statement-level metadata. Lower priority for us — our metadata sits on the relator *vertex*, not on bare triples. Relevant only if we ever expose SPARQL over ArcadeDB. |
| **LPG reification** (Neo4j/ArcadeDB) | The implementation pattern: an **intermediate node** typed as the relationship + binary role edges. ArcadeDB's index-free adjacency makes the extra hop O(1); add composite indexes per `(relatorType, roleName)`. |
| **TypeDB relation-with-roles** | The closest peer to our target. A `relation` declares named **roles**; entities `play` roles; relations can play roles in other relations (nested reification). The **role-plays link is typed/constrained at schema level** — that's exactly what our role-binding edge + IR constraints should enforce. |
| **Bitemporal** (Fowler/XTDB) | Two axes — valid time + transaction time — **on the reified relation**. Append a new relator version per change (`supersededAt` set, never deleted); "state as of D known at T" = range filter on both axes. |
| **PROV-O** | The relator *is* a qualified-influence instance: it already connects participants + time; add `wasGeneratedBy`/`wasAttributedTo` (property or companion `ProvenanceVertex`). |

## Recommended design for our stack

### IR — declare relators with typed roles (LinkML-like)
```yaml
relators:
  - id: ingest-evidence
    ufo_kind: relator
    roles:
      - { name: source,   participant_type: knowledge-source,    cardinality: "1..1" }
      - { name: chunks,    participant_type: knowledge-chunk,     cardinality: "1..*" }
      - { name: exercise,  participant_type: capability-exercise, cardinality: "1..1" }
      - { name: evidence,  participant_type: evidence-pack,       cardinality: "1..1" }
    properties:
      - { name: assembled_at, type: string }
    temporal: { valid_from: string, valid_to: string }
```
A binary relationship = a relator with exactly two roles (`source`, `target`) → existing edges become a degenerate relator, additive not breaking. The generator validates roles against known object types, applies the ORM ≥(n-1) uniqueness smell check, and rejects RelOver-style overlapping role types.

### C# runtime
```csharp
public sealed record RelatorInstance(
    string RelatorId, string RelatorType,
    IReadOnlyList<RoleBinding> Bindings,
    string? ValidFrom, string? ValidTo, string RecordedAt,   // bitemporal: valid + transaction time
    ProvenanceRef? Provenance);
public sealed record RoleBinding(string RoleName, string ParticipantId, string ParticipantType, int Ordinal);
```
All graph reads go through `RelatorInstance`; binary edges are wrapped as a 2-binding relator → zero-cost special case, current generated code unaffected.

### ArcadeDB persistence (hyperedge-as-vertex)
- Vertex `RelatorVertex { relator_type*, valid_from, valid_to, recorded_at, superseded_at }`
- Edge `RoleBinding (extends E) { role_name, ordinal }` from `RelatorVertex` → participant.
- Composite index `(relator_type, valid_from, valid_to)`; hash index on `role_name`.
- Traversal is two hops (participant → role-binding → relator), mitigated by index-free adjacency.

### Bitemporal + PROV compose on the relator
Both land on the relator vertex (not participants/edges). Version by appending a new relator vertex; link provenance via a single edge to a `ProvenanceVertex`. Audit-safe (no in-place delete).

## Recommended first slice (additive — smallest end-to-end proof)
1. Add a `relators:` section to the model IR (beside `relationship_types`), with **one 3–4-role relator** (`ingest-evidence` is a natural fit — it already binds source + chunks + exercise + evidence in the knowledge-drop scenario).
2. Generator emits the `RelatorInstance` C# record + `RelatorVertex`/`RoleBinding` ArcadeDB type defs + role/cardinality validation.
3. Runtime builds the one relator (reusing the objects knowledge-drop already creates) and exposes it (e.g. `/model/relators/{id}`).
4. **Leave the 5 binary edges and all current counts/tests untouched.** Migrate binary→2-role relator in a *later* slice once the round-trip is proven.

## Open questions
- Cardinality enforcement: at generation time (Python), runtime (C#), DB (ArcadeDB constraints), or all three? (Lean: generate-time + runtime; DB as backstop.)
- Do we need UFO **qua-individuals** (participant-relative properties)? Defer until a concrete use case.
- Reification ↔ the temporal pulse: a relator version *is* a perdurant delta — align the relator's `valid_from`/`recorded_at` with the global tick from [[Ontology-Pipeline]].

## Sources
- [Relations in Ontology-Driven Conceptual Modeling — Guizzardi et al. (2019)](https://www.inf.ufes.br/~gguizzardi/Relations_in_Ontology-Driven_Conceptual.pdf)
- [OntoUML Mediation](https://ontouml.readthedocs.io/en/latest/relationships/mediation/index.html) · [RelOver anti-pattern](https://ontouml.readthedocs.io/en/latest/anti-patterns/RelOver/index.html)
- [Object-Role Modeling overview — Halpin](https://www.orm.net/pdf/ORMwhitePaper.pdf)
- [Defining N-ary Relations on the Semantic Web — W3C (2006)](https://www.w3.org/TR/swbp-n-aryRelations/)
- [RDF 1.2 Concepts — W3C](https://www.w3.org/TR/rdf12-concepts/) · [RDF-star fundamentals — Ontotext](https://www.ontotext.com/knowledgehub/fundamentals/what-is-rdf-star/)
- [Modeling Hyper Edges in a Property Graph — Needham/DZone](https://dzone.com/articles/neo4j-modeling-hyper-edges) · [Intermediate nodes — Neo4j GraphAcademy](https://graphacademy.neo4j.com/courses/modeling-fundamentals/8-adding-intermediate-nodes/1-intermediate-nodes/)
- [The case for a structured hypergraph — TypeDB](https://typedb.com/blog/the-case-for-a-structured-hypergraph) · [Why TypeDB isn't a graph DB but can behave as one](https://typedb.com/blog/why-typedb-isnt-a-graph-database-but-it-can-behave-as-one)
- [HyperGraphDB — Iordanov (2010)](https://link.springer.com/chapter/10.1007/978-3-642-16720-1_3)
- [Bitemporal History — Fowler](https://martinfowler.com/articles/bitemporal-history.html) · [Bitemporality — XTDB](https://v1-docs.xtdb.com/concepts/bitemporality/)
- [PROV-O — W3C](https://www.w3.org/TR/prov-o/) · [LinkML: modeling property graphs](https://linkml.io/linkml/howtos/model-property-graphs.html)
- [Meta-Property Graphs: reification with metadata — arXiv 2024](https://arxiv.org/html/2410.13813v1)
