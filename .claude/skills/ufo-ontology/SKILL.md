---
name: ufo-ontology
description: Model with the Unified Foundational Ontology (UFO) and its modeling language OntoUML, plus the gUFO OWL implementation. Use when designing conceptual models with ontological stereotypes (kind, subkind, phase, role, relator, mode, quality, category, mixin, event, situation), reasoning about rigidity / sortality / identity / dependence, reifying n-ary relations as relators, detecting OntoUML anti-patterns, or producing a gUFO-aligned OWL projection. This is the AgentArmy primary authoring discipline. Distinct from the bfo-ontology skill (realist BFO/CCO lineage, used for the interop projection).
---

# UFO — Unified Foundational Ontology (and OntoUML)

UFO is a foundational ontology grounded in **modal logic, cognitive science, and linguistics** (Guizzardi et al., NEMO/UFES). Its purpose is **ontologically well-founded conceptual modeling** — capturing a stakeholder's conceptualization precisely. Its modeling language is **OntoUML** (a UML class-diagram profile), and **gUFO** is its lightweight OWL 2 DL implementation for the Semantic Web.

Unlike BFO (which carves mind-independent reality), UFO organizes types by **meta-properties** — *is this type rigid? does it carry an identity principle? does it depend on a relationship?* — because those distinctions are what make a conceptual model correct and unambiguous. Use this skill for authoring; use **bfo-ontology** for the realist interop projection.

## The four meta-properties that decide every stereotype

1. **Sortality** — does the type carry a **principle of identity** (a criterion for counting/identifying instances)?
   - **Sortal** — yes (Person, Car). Every individual instantiates exactly one *ultimate sortal* (a Kind) that supplies its identity.
   - **Non-sortal / Mixin** — no; aggregates instances from multiple kinds (PhysicalObject, Customer-as-Person-or-Org).
2. **Rigidity** — must instances *keep* this type to keep existing?
   - **Rigid** — necessarily applies to its instances in every world (Person, Car). Lose it ⇒ cease to exist.
   - **Anti-rigid** — contingently applies; an instance can gain/lose it while persisting (Student, Child, Customer).
   - **Semi-rigid** — rigid for some instances, anti-rigid for others (a Mixin).
3. **Identity provision** — does the type *supply* identity (Kind) or *inherit* it (Subkind/Phase/Role)?
4. **Dependence** — anti-rigidity caused by an **intrinsic** contingent property (→ **Phase**) or a **relational/extrinsic** one (→ **Role**)?

## The OntoUML stereotype decision tree

```
Is the type a Substantial/object type (provides or inherits identity)?
├── SORTAL (carries identity)
│   ├── RIGID
│   │   ├── provides identity, independent .......... «kind»  (functional complex)
│   │   │      variants by identity meta-kind: «collective», «quantity»
│   │   └── inherits identity (specializes a kind) ... «subkind»
│   └── ANTI-RIGID
│       ├── intrinsic contingent property ............ «phase»
│       └── relational contingent property ........... «role»
└── NON-SORTAL (no identity of its own; aggregates kinds)
    ├── RIGID ......................................... «category»
    ├── ANTI-RIGID
    │   ├── relational ............................... «roleMixin»
    │   └── intrinsic ................................ «phaseMixin»
    └── SEMI-RIGID ................................... «mixin»

Is it an aspect/moment (existentially dependent on a bearer)?
├── intrinsic, value in a quality space .............. «quality»
├── intrinsic, may bear its own qualities ............ «mode»
└── relational (binds ≥2 participants), reified ...... «relator»

Is it a perdurant / happens in time? ................. «event»  (UFO-B)
Is it a state-of-affairs snapshot? ................... «situation»
Higher-order / value types .......................... «type», «datatype», «enumeration»
```

Every stereotype, its constraints, and the relation stereotypes (mediation, characterization, material, formal, componentOf, memberOf, subQuantityOf, …) are in [references/ONTOUML_PROFILE.md](references/ONTOUML_PROFILE.md). The deeper theory of endurants/perdurants/moments and identity meta-kinds is in [references/UFO_TAXONOMY.md](references/UFO_TAXONOMY.md).

## Relators — the centerpiece (and why reification matters)

A **relator** is a *moment* (existentially dependent endurant) that **mediates** a set of participants — it is the **truthmaker of a material relation** (a marriage makes "is married to" true; an enrollment makes "is enrolled at" true). Relators are how UFO handles n-ary relationships: reify the relationship as a relator that **mediates** each participant (via «mediation», an existential-dependency relation), then **derive** the material relation from it.

Reify as a relator when the relationship **(a)** has its own identity/lifecycle, **(b)** binds >2 participants as one unit, **(c)** carries its own properties (time, provenance, value), or **(d)** participates in further relations. This is exactly the repo's reification criterion. Watch the **RelOver** anti-pattern (overlapping role types → ambiguous role assignment).

## Modeling workflow

1. **Find the kinds first.** Every object must instantiate exactly one ultimate **«kind»** (or «collective»/«quantity»). Identify them and their identity principle before anything else.
2. **Specialize with subkinds, phases, roles.** Rigid specialization → «subkind». Contingent + intrinsic → «phase» (in partitions that cover the kind). Contingent + relational → «role».
3. **Lift commonalities into non-sortals** («category» for rigid shared properties; «roleMixin»/«mixin» for cross-kind roles).
4. **Reify relationships as relators**; connect with «mediation» to each participant and set role cardinalities. Derive «material» relations from relators; use «formal» for direct comparatives/parthood.
5. **Add intrinsic aspects** as «quality» (value in a space) or «mode» (complex aspect).
6. **Model dynamics** with «event» and «situation» (UFO-B) where lifecycle/causation matters.
7. **Validate against anti-patterns** (RelOver, RWOR, AssocCyc, DepPhase, …) and **simulate** (Alloy) — see [references/ONTOUML_ANTIPATTERNS_AND_GUFO.md](references/ONTOUML_ANTIPATTERNS_AND_GUFO.md).
8. **Project to gUFO OWL** for Semantic Web reasoning; project to BFO/CCO for interop.

## gUFO (the OWL projection)

gUFO (`http://purl.org/nemo/gufo#`) is a lightweight OWL 2 DL implementation of UFO with two taxonomies: one for **individuals** (`gufo:Endurant`, `gufo:Perdurant`, `gufo:Object`, `gufo:Relator`, `gufo:Quality`, `gufo:Mode`, `gufo:Situation`, `gufo:Event`) and one for **types** (`gufo:Kind`, `gufo:SubKind`, `gufo:Role`, `gufo:Phase`, `gufo:Category`, `gufo:Mixin`, `gufo:RoleMixin`, `gufo:PhaseMixin`, `gufo:RelatorType`, `gufo:QualityType`, `gufo:ModeType`). Stereotypes map onto these classes; reified aspects and higher-order types are supported. Details: [references/ONTOUML_ANTIPATTERNS_AND_GUFO.md](references/ONTOUML_ANTIPATTERNS_AND_GUFO.md).

## Bridging to BFO (synthesis, not bijection)

UFO and BFO diverge sharply — UFO **relator**, anti-rigid **phase**, and the rigidity/sortality meta-properties have no clean BFO counterpart. Project UFO→BFO/CCO **best-effort** and always ship a **mapping table + divergence list**: [references/UFO_BFO_MAPPING.md](references/UFO_BFO_MAPPING.md). Never claim a lossless round-trip.

## In this repo (AgentArmy pipeline)

UFO/gUFO/OntoUML is the **primary authoring + reasoning discipline** (see [`Ontology-Pipeline.md`](../../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md)). When working here:

- The **canonical IR** is `model/middle-core/model.yaml` (LinkML-like). Its `stereotype` vocabulary — `kind, subkind, role, phase, relator, event, situation, quality, mode, category, mixin` — **is the OntoUML profile**. Keep IR types stereotyped correctly; the generator depends on it.
- **Relators are first-class** in the IR (`relators:` with typed roles), the C# runtime (`RelatorInstance`), and ArcadeDB (**hyperedge-as-vertex**: relator vertex + `BINDS_ROLE` edges). See [`Reification-and-Hyperedges.md`](../../../obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md). A binary relation is a degenerate 2-role relator.
- **Projections, not one representation:** emit gUFO OWL (Level-3 reasoner target) and the BFO/CCO interop sidecar from the *same* IR; never hand-edit a projection.
- **Validation levels:** Level 2 = OntoUML stereotype + anti-pattern checks; Level 3 = gUFO/OWL reasoner; Level 4 = SHACL; Level 5 = Alloy simulation. Run them in that order.
- **Bitemporal + PROV-O** ride on the relator (a relator version is a perdurant delta) — align with the pipeline's temporal pulse.
- Pin vocabularies from the ontology URI catalog (gUFO, SEON, gist, FIBO, OWL-Time, PROV-O, SOSA, DCAT) listed in the pipeline note.
- **Worked example & IR spec:** [`templates/ontology-project/`](../../../templates/ontology-project/) is a complete end-to-end scaffold — the canonical IR JSON Schema (`ontology.ir.schema.json`), a validating `model/model.yaml` (Risk/Control/MitigationCase relator), and every projection (gUFO, BFO/CCO, SHACL, Alloy, SMT, ArcadeDB, PROV). Copy it to start a new model.

## References

- [UFO_TAXONOMY.md](references/UFO_TAXONOMY.md) — UFO-A/B/C, endurant/perdurant/moment, identity meta-kinds, rigidity & sortality theory.
- [ONTOUML_PROFILE.md](references/ONTOUML_PROFILE.md) — every class & relation stereotype with constraints and examples.
- [ONTOUML_ANTIPATTERNS_AND_GUFO.md](references/ONTOUML_ANTIPATTERNS_AND_GUFO.md) — anti-pattern catalog, Alloy simulation, gUFO OWL mapping & tooling.
- [UFO_BFO_MAPPING.md](references/UFO_BFO_MAPPING.md) — UFO→BFO projection table + divergence list.

### External sources
- *Ontological Foundations for Structural Conceptual Models* — Guizzardi (2005, the UFO-A thesis)
- OntoUML docs — `https://ontouml.readthedocs.io` · OntoUML/UFO Catalog — `https://github.com/OntoUML/ontouml-models`
- gUFO — `https://nemo-ufes.github.io/gufo/` (`https://github.com/nemo-ufes/gufo`)
- ontouml-metamodel / ontouml-js — `https://github.com/OntoUML/ontouml-metamodel`
- *Relations in Ontology-Driven Conceptual Modeling* — Guizzardi et al. (2019)
