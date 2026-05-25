# OBO Foundry, CCO, and the BFO tooling stack

BFO is rarely used alone. It is the upper level of two ecosystems you will reuse rather than reinvent: the **OBO Foundry** (open biomedical/scientific ontologies) and the **Common Core Ontologies** (CCO, a BFO mid-level suite). This file covers the ecosystem, the methodology principles, and the Common-Logic-vs-OWL choice.

## OBO Foundry principles (the ones that change how you model)

The OBO Foundry is a community of interoperable ontologies built to shared principles. The ones with direct modeling impact:

1. **Open** — CC-BY or freer; reuse is expected.
2. **Common format** — distributed in OWL (RDF/XML or Turtle) and/or OBO format.
3. **URI / IDspace** — every term has a stable PURL under `purl.obolibrary.org/obo/`, with a registered numeric IDspace (`BFO_`, `RO_`, `IAO_`, `PATO_`, `CL_`, `GO_`, …). **Never** mint a label-based IRI; mint an opaque numeric ID and attach `rdfs:label`.
4. **Versioning** — released with version IRIs.
5. **Scope & orthogonality** — each ontology owns one domain; **do not duplicate** a term that exists elsewhere — import it. This is the single most important OBO discipline: reuse RO for relations, IAO for information, PATO for qualities, UO for units, etc.
6. **Textual definitions** — every class has a human-readable Aristotelian definition (genus + differentia) plus, ideally, a logical definition.
7. **Relations from RO** — use the Relation Ontology, don't invent object properties.
8. **Single asserted `is_a` hierarchy** — multiple inheritance is *inferred*, never asserted.
9. **Documented, maintained, has users, has a responsible authority, tracker for issues, naming conventions, dbxrefs.**

### Aristotelian definition pattern
```
genus + differentia:
  "A hepatocyte is a cell (genus) that is part of the liver and ... (differentia)."
  "A function is a disposition (genus) that exists because its bearer was
   designed or selected to realize a particular process (differentia)."
```
Write the textual definition first; the logical/OWL definition (equivalent-class axiom) follows from it.

## The standard reusable OBO ontologies

| Ontology | IDspace | Owns | Why you import it |
|---|---|---|---|
| **BFO** | `BFO_` | top-level categories | the upper grounding (every class `is_a` a BFO class). |
| **RO** (Relation Ontology) | `RO_` | relations | `part_of`, `participates_in`, `has_participant`, `realizes`, `inheres_in`, … |
| **IAO** (Information Artifact Ontology) | `IAO_` | information | `information content entity` (a GDC), `is_about`, `denotes`, `data item`, `document`. Use IAO for *anything informational* — never model information as a quality. |
| **PATO** (Phenotype And Trait Ontology) | `PATO_` | qualities | reusable quality universals (mass, length, color, shape, disposition values). |
| **OMRSE / OBI / GO / CL / UBERON / ...** | various | domain | domain universals in bio/med. |
| **UO** | `UO_` | units of measure | quantitative values. |

## Common Core Ontologies (CCO) — the mid-level for enterprise/defense

CCO (maintained originally by CUBRC; widely used in US DoD/IC) is a **suite of eleven mid-level ontologies** that specialize BFO into broadly reusable, non-biomedical universals. It is the natural mid-level when your domain is enterprise, logistics, agents, artifacts, or events rather than biology.

| CCO module | Provides |
|---|---|
| **Agent Ontology** | Person, Organization, Group, agent roles, capabilities. |
| **Artifact Ontology** | Artifacts, artifact functions, designs. |
| **Event Ontology** | Acts, processes, planned/unplanned events. |
| **Information Entity Ontology** | Information content entities (aligned with/extending IAO). |
| **Quality Ontology** | Qualities, dispositions, capabilities. |
| **Geospatial Ontology** | Geospatial regions, sites, features. |
| **Time Ontology** | Temporal regions, instants, intervals. |
| **Units of Measure** | Measurement units and quantities. |
| **Currency Unit Ontology** | Currencies, monetary amounts. |
| **Facility Ontology** | Facilities and infrastructure. |
| **Extended Relation Ontology** | CCO-level relations specializing RO. |

**Why CCO matters here:** the IKW-GraphEngine grounds in **BFO 2020 + CCO + IAO + RO + SKOS**. So the AgentArmy BFO/CCO interop projection should align domain types to CCO mid-level universals (Person → `cco:Person`, Organization → `cco:Organization`, an information record → `cco:InformationContentEntity`) so the projection is directly consumable by GE's A/T/R-box reasoning. CCO is the bridge that makes "offer both" concrete on the BFO side.

## Common Logic vs OWL 2 — choosing the axiomatization

ISO/IEC 21838-2 ships BFO in **both**; they are not interchangeable.

| Dimension | Common Logic (CLIF) | OWL 2 DL (`bfo.owl`) |
|---|---|---|
| Status | normative first-order | conformant decidable subset |
| Relations | genuine ternary (time-indexed) | binary only (binarized) |
| Reasoning | full FOL theorem proving (slow/semi-decidable) | decidable; HermiT/ELK/Pellet (fast) |
| Tooling | Hets, theorem provers (Vampire, Prover9) | Protégé, ROBOT, OWL API, pyshacl-adjacent |
| Use it for | temporal correctness, deep axioms, GE Common-Logic interop | satisfiability, disjointness, subsumption, CI validation |

In the AgentArmy layered proof stack: **OWL → validation Level 3** (reasoner smoke check); **Common Logic → the GE interop projection** and any claim that genuinely requires time-indexed relations. Don't try to make OWL carry temporal qualification it can't express — push that to the CL projection or the bitemporal relator layer.

## Tooling

- **ROBOT** — the OBO build tool: `extract` (module extraction / MIREOT), `reason`, `report` (QC checks), `template` (build classes from a TSV), `merge`, `convert`. The backbone of an OBO release pipeline.
- **Protégé** — authoring + reasoner UI.
- **OWL API / owlready2 / rdflib** — programmatic manipulation (owlready2 and rdflib are the Python path the pipeline already leans on).
- **HermiT / ELK / Pellet** — OWL reasoners (ELK for EL-profile scalability; HermiT for full DL).
- **Hets + Vampire/Prover9** — multi-logic broker for the Common Logic side (the GE ecosystem uses this lineage).
- **OOPS!** — ontology pitfall scanner.

## Quick "is this BFO-clean?" checklist

- [ ] Every class has exactly one asserted `is_a` parent terminating at a BFO category.
- [ ] Every class has a textual (genus + differentia) definition.
- [ ] Relations are RO/BFO terms, not bespoke object properties.
- [ ] Information is modeled as IAO information content entity (GDC), not a quality.
- [ ] Roles/dispositions/functions are realizable entities the bearer *bears*, not subtypes of the bearer.
- [ ] Processes and the continuants that participate in them are kept distinct.
- [ ] Numeric opaque IDs minted in a registered IDspace; labels via `rdfs:label`.
- [ ] Reused mid-level (CCO) where a universal already exists.
