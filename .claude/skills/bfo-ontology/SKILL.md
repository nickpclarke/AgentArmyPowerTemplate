---
name: bfo-ontology
description: Ground models in Basic Formal Ontology (BFO 2020, ISO/IEC 21838-2) — the realist top-level ontology used by the OBO Foundry and Common Core Ontologies (CCO). Use when classifying entities as continuant vs occurrent, writing OBO-style ontologies, producing a BFO/CCO interop projection (e.g. for the IKW-GraphEngine "offer both" design), authoring Aristotelian definitions, or choosing between the Common Logic and OWL 2 axiomatizations of BFO. Distinct from the ufo-ontology skill (design-oriented UFO/OntoUML lineage).
---

# BFO — Basic Formal Ontology

BFO is a small, domain-neutral **top-level (upper) ontology**. It is **realist**: its categories are meant to carve reality at its joints, so every domain class is asserted as a subtype (`is_a`) of exactly one BFO category. BFO is the upper level of the **OBO Foundry** (biomedical ontologies), of **CCO** (Common Core Ontologies, a BFO mid-level suite used in defense/intelligence), and is standardized as **ISO/IEC 21838-2:2021**.

Use this skill when the job is to *commit to reality* — interoperability, data integration, scientific/engineering description — rather than to capture a stakeholder's conceptualization. For the latter (modal meta-properties, conceptual modeling), use the **ufo-ontology** skill.

## The three commitments that drive every decision

1. **Continuant vs Occurrent** — the top split of `Entity`.
   - A **continuant** *endures* through time, is wholly present at each moment it exists, and can change (a person, a heart, a quality, a role).
   - An **occurrent** *unfolds* in time, has temporal parts, and is never wholly present at a single instant (a process, a process boundary, a temporal region).
   - Test: "Does it have temporal parts / phases that happen?" → occurrent. "Is the whole thing there right now?" → continuant.

2. **Independent vs Dependent** (within continuants).
   - **Independent continuant** — the bearer; exists on its own (a cell, a car, a spatial region).
   - **Specifically dependent continuant (SDC)** — a quality/role/disposition that *inheres in* exactly its bearer (this apple's redness). It cannot migrate.
   - **Generically dependent continuant (GDC)** — a pattern that can be *copied* across many bearers (the text of a novel, a sequence, a PDF's content). It is *concretized by* SDCs.

3. **Universal vs Particular** — BFO classes are **universals** (repeatable types in reality); individuals are **particulars** (instances). `is_a` relates universals; `instance_of` relates a particular to a universal.

## Top-level category tree (memorize the spine)

```
Entity
├── Continuant
│   ├── Independent Continuant
│   │   ├── Material Entity ── Object · Fiat Object Part · Object Aggregate
│   │   └── Immaterial Entity ── Continuant Fiat Boundary · Site · Spatial Region
│   ├── Specifically Dependent Continuant
│   │   ├── Quality ── Relational Quality
│   │   └── Realizable Entity ── Role · Disposition ── Function
│   └── Generically Dependent Continuant
└── Occurrent
    ├── Process ── (History, Process Profile)
    ├── Process Boundary
    ├── Temporal Region ── 0-dimensional (instant) · 1-dimensional (interval)
    └── Spatiotemporal Region
```

Full elucidations, examples, and OBO IDs (`BFO_0000001` …): see [references/BFO_2020_HIERARCHY.md](references/BFO_2020_HIERARCHY.md).

## Relations: time-indexing is the headline

BFO relations for continuants are **time-indexed** — they are genuinely *ternary*: `c1 continuant_part_of c2 at t`. The normative **Common Logic** axiomatization keeps the ternary form; the **OWL 2** version *binarizes* (drops or reifies the time index), which is the single biggest expressivity trade-off you must manage. Occurrent relations are not time-indexed (occurrents already contain their time).

Core relations: `continuant_part_of` / `has_continuant_part`, `occurrent_part_of`, `located_in`, `occupies_temporal_region` / `occupies_spatial_region` / `occupies_spatiotemporal_region`, `participates_in` / `has_participant`, `realizes` / `is_realized_in`, `inheres_in` / `bearer_of`, `has_role` / `has_disposition` / `has_function`, `concretizes` (SDC↔GDC), `specifically_depends_on`, `generically_depends_on`, `preceded_by` / `precedes`, `exists_at`. Full table with arities, RO/BFO IDs, and OWL-binarization notes: [references/BFO_RELATIONS.md](references/BFO_RELATIONS.md).

## Classification workflow (the BFO decision procedure)

1. **Does it happen or does it exist?** Happens/unfolds → **Occurrent** (process? boundary? region?). Exists/endures → **Continuant**, go to 2.
2. **Can it exist on its own?** Yes → **Independent Continuant** (material if it has matter; immaterial if it's a boundary/site/region). No → it depends on a bearer, go to 3.
3. **Does it need exactly one specific bearer, or is it a copyable pattern?** Specific bearer → **SDC** (go to 4). Copyable pattern → **GDC** (e.g. information content entity, via IAO).
4. **Is the SDC realized in a process?** No, it just is-a-way-the-bearer-is → **Quality**. Yes, it's a potential realized when triggered → **Realizable Entity**: externally/contextually granted → **Role**; internally grounded → **Disposition**; a disposition selected-for to serve an end → **Function**.
5. **Write the Aristotelian definition:** `An X is a G that Ds` — genus (the parent universal) + differentia (what distinguishes X from siblings). Single asserted parent only.

## Methodology (OBO-style discipline)

- **Single inheritance** in the asserted hierarchy: one `is_a` parent per universal. Multiple inheritance is *inferred* by a reasoner, never asserted.
- **Univocity & realism:** terms denote universals in reality; avoid "concept", "data", "information about" unless you mean an IAO information content entity (a GDC).
- **Orthogonality:** reuse existing ontologies (RO for relations, IAO for information, PATO for qualities, CCO for mid-level) rather than re-minting terms.
- **Aristotelian definitions:** genus + differentia, textual definition for every class.
- Two normative axiomatizations ship together (ISO/IEC 21838-2): **Common Logic (CLIF)** = full first-order, time-indexed; **OWL 2 DL** (`bfo.owl`) = decidable, binarized. Pick per use: reasoning depth vs tractable validation. See [references/OBO_FOUNDRY_AND_CCO.md](references/OBO_FOUNDRY_AND_CCO.md) for OBO principles, CCO/IAO/RO, and the CL-vs-OWL trade-off in depth.

## Bridging to UFO (synthesis, not bijection)

BFO and UFO are rival foundational lineages: **realist/applied (BFO)** vs **design/conceptual (UFO)**. They map *best-effort*, not losslessly. The sharp divergences — UFO **relator** (no single BFO counterpart), UFO anti-rigid **phase** (BFO has no phase notion), UFO modal meta-properties (rigidity/sortality, absent in BFO) — are catalogued with the correspondence table in [references/UFO_BFO_MAPPING.md](references/UFO_BFO_MAPPING.md). Always ship a **mapping table + divergence list**, never claim a round-trip.

## In this repo (AgentArmy pipeline)

The platform authors in **UFO/gUFO/OntoUML** as the primary discipline and emits **BFO 2020 + CCO** as an *interop projection* — the "offer both, one IR → two upper-ontology projections" design in [`obsidian/labs/AgentArmyLabs/vision/IKW-GraphEngine (Parallel Track).md`](../../../obsidian/labs/AgentArmyLabs/vision/IKW-GraphEngine%20(Parallel%20Track).md) and [`Ontology-Pipeline.md`](../../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md). When working the BFO side:

- The **BFO/CCO projection** (Common Logic / OWL) is what the IKW-GraphEngine consumes for A-Box/T-Box/R-Box reasoning over BFO 2020 Common Logic axioms + the Guan logic engine. It is a *sidecar*, not a second source of truth — author once in the IR, project to BFO.
- Keep the projection at **validation Level 3** (OWL reasoner: HermiT/ELK) in the pipeline's layered proof stack; emit it from the canonical `model.yaml` IR, never hand-author drift.
- Ship the **mapping table + divergence list** as an artifact beside the projection (the pipeline's "documented mapping, not lossless round-trip" rule).
- Reify n-ary relations as BFO-respecting structures (a relational quality / interdependent roles) — coordinate with the hyperedge-as-vertex design in [`Reification-and-Hyperedges.md`](../../../obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md).
- **Worked example & IR spec:** [`templates/ontology-project/`](../../../templates/ontology-project/) is a complete scaffold — see `semantic/model.bfo-cco.ttl` for a realist projection and `docs/mapping-rules.md` for the per-element mapping + divergence list that must ship with it.

## References

- [BFO_2020_HIERARCHY.md](references/BFO_2020_HIERARCHY.md) — every category, elucidation, example, OBO ID.
- [BFO_RELATIONS.md](references/BFO_RELATIONS.md) — relation catalog, arities, time-indexing, OWL binarization.
- [OBO_FOUNDRY_AND_CCO.md](references/OBO_FOUNDRY_AND_CCO.md) — OBO principles, CCO/IAO/RO/PATO, Common Logic vs OWL, tooling (ROBOT).
- [UFO_BFO_MAPPING.md](references/UFO_BFO_MAPPING.md) — UFO↔BFO correspondence + divergence list.

### External sources
- BFO 2020 spec & ISO/IEC 21838-2:2021 — `https://github.com/BFO-ontology/BFO-2020`
- *Building Ontologies with Basic Formal Ontology* — Arp, Smith, Spear (MIT Press, 2015)
- OBO Foundry — `https://obofoundry.org` · Relation Ontology (RO) — `https://github.com/oborel/obo-relations`
- Common Core Ontologies — `https://github.com/CommonCoreOntology/CommonCoreOntologies`
