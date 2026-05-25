# OntoUML Anti-Patterns, Simulation, and the gUFO OWL projection

Two things turn a UFO model from "stereotyped UML" into a *validated* ontology: catching **anti-patterns** (recurring modeling errors that admit unintended instances) and **projecting to gUFO OWL** for machine reasoning. This file covers both.

## Anti-patterns (the recurring errors)

OntoUML anti-patterns are configurations that are *syntactically legal* but allow models to be instantiated in ways the modeler did not intend. The OntoUML catalog documents ~20; these are the high-value ones. Detect them at **validation Level 2** (before reasoning).

| Code | Name | The error | Fix |
|---|---|---|---|
| **RelOver** | Relator role overlap | Two roles mediated by one relator have **overlapping extensions**, so an individual could fill both — ambiguous role binding. | Make role types disjoint, or add constraints partitioning the bearers. |
| **RWOR** | Relator with overlapping roles | Stronger RelOver: the same individual is forced into multiple roles of one relator. | Restructure roles; add disjointness. |
| **RelSpec** | Relator specialization | A relator specialization doesn't actually constrain participants differently. | Remove the spurious subtype or differentiate participants. |
| **RelComp** | Relator composition | Parthood between relators without clear role propagation. | Clarify how mediated roles flow to the part relator. |
| **AssocCyc** | Association cycle | A cycle of relations admits unintended loops (e.g. a thing part-of itself transitively). | Add acyclicity / irreflexivity constraints. |
| **DepPhase** | Dependent phase | A «phase» whose condition is actually **relational** (extrinsic) — it should be a «role». | Re-stereotype phase→role; connect to a relator. |
| **FreeRole** | Role without relator | A «role» not connected to any «relator» via «mediation» — no truthmaker. | Add the mediating relator, or re-stereotype to «subkind»/«phase». |
| **RelRig** | Relation between rigid & anti-rigid w/ wrong rigidity | A rigid type specializing/mediated as if anti-rigid (or vice versa). | Fix the rigidity assignment. |
| **GSRig** | Generalization-set rigidity | A generalization set mixes rigid and anti-rigid subtypes incorrectly. | Separate rigid (subkind) from anti-rigid (phase/role) sets. |
| **HetColl** | Heterogeneous collective | A «collective» whose members are not uniform, breaking the uniform-structure assumption. | Use a functional complex («kind») or sub-collections. |
| **MixIden** | Mixin with identity | A non-sortal effectively supplying identity (used as if a kind). | Re-stereotype to a sortal, or make it properly abstract over ≥2 kinds. |
| **ImpAbs** | Imprecise abstraction | A supertype that conflates distinct identity principles. | Split by identity meta-kind. |
| **BinOver** | Binary overlap | Overlapping ends of a binary relation create unintended self-relations. | Add disjointness/irreflexivity. |

> The ORM cross-check (from the repo's reification note): a uniqueness constraint on an n-ary relation must span **≥ n−1** roles; if it spans fewer, the relation is *splittable* — a decomposition smell worth flagging alongside RelOver.

## Simulation with Alloy (validation Level 5)

OntoUML models can be **transformed to Alloy** and simulated to find counterexamples — small instances the model permits but the modeler rejects. This is the fastest way to catch "can this model exist?" / "does it admit nonsense?" errors before they reach generated code.

```alloy
// sketch: every Student must be mediated by exactly one Enrollment
sig Person {}
sig School {}
sig Student in Person {}
sig Enrollment { student: one Student, school: one School }
fact EveryStudentEnrolled { all s: Student | some e: Enrollment | e.student = s }
run {} for 4   // inspect generated worlds for unintended instances
```

Workflow: stereotype check (L2) → Alloy simulate (L5, small scope) → fix → gUFO/OWL reason (L3) → SHACL (L4). The OntoUML Server / OaaS and historical Menthor automate the OntoUML→Alloy transform.

## gUFO — the OWL 2 DL projection

**gUFO** (`http://purl.org/nemo/gufo#`, prefix `gufo:`) is the lightweight, Semantic-Web implementation of UFO. It exposes **two parallel taxonomies** so you can talk about both individuals and the types they instantiate.

### Individual taxonomy (assert your *instances* under these)
`gufo:Endurant` (→ `gufo:Object`, `gufo:Relator`, `gufo:Quality`, `gufo:Mode`, `gufo:Collection`, `gufo:Quantity`, `gufo:IntrinsicMode`, `gufo:ExtrinsicMode`) · `gufo:Perdurant` (events) · `gufo:Situation` · `gufo:Aspect`.

### Type taxonomy (assert your *classes* as instances of these — higher-order)
`gufo:Kind`, `gufo:SubKind`, `gufo:Role`, `gufo:Phase`, `gufo:Category`, `gufo:RoleMixin`, `gufo:PhaseMixin`, `gufo:Mixin`, `gufo:RelatorType`, `gufo:ModeType`, `gufo:QualityType`, `gufo:Collection`, `gufo:Quantity`.

### Stereotype → gUFO mapping
| OntoUML | gUFO type class | also assert instances as |
|---|---|---|
| «kind» | `gufo:Kind` | `gufo:Object` |
| «subkind» | `gufo:SubKind` | `gufo:Object` |
| «phase» | `gufo:Phase` | `gufo:Object` |
| «role» | `gufo:Role` | `gufo:Object` |
| «category» | `gufo:Category` | (abstract) |
| «roleMixin» | `gufo:RoleMixin` | (abstract) |
| «mixin» | `gufo:Mixin` | (abstract) |
| «relator» | `gufo:RelatorType` | `gufo:Relator` |
| «mode» | `gufo:ModeType` | `gufo:IntrinsicMode`/`gufo:ExtrinsicMode` |
| «quality» | `gufo:QualityType` | `gufo:Quality` |
| «event» | (subclass of) `gufo:Event` | `gufo:Event` |
| «situation» | (subclass of) `gufo:Situation` | `gufo:Situation` |

### Key gUFO object properties
- `gufo:mediates` — relator → participant (the «mediation» link).
- `gufo:inheresIn` / `gufo:bearer` — moment → bearer («characterization»).
- `gufo:participatedIn` — endurant → event.
- `gufo:isComponentOf`, `gufo:isMemberOf`, `gufo:isSubCollectionOf`, `gufo:isPortionOf` — parthood.
- `gufo:categorizes` / `gufo:concretizes` — higher-order typing.
- `gufo:hasQualityValue` / quality-value datatype properties — quality spaces.

### Reasoning targets (validation Level 3)
Run HermiT/ELK over the gUFO projection to check: class satisfiability, disjointness (rigid vs anti-rigid, kind disjointness), subsumption, and that every object resolves to one kind. gUFO ships disjointness axioms that make many anti-patterns surface as unsatisfiable classes.

## Tooling

- **OntoUML Plugin for Visual Paradigm** — the maintained authoring + verification path (anti-pattern checks, gUFO/OWL export, model simulation). Successor to **Menthor** (deprecated) and **OLED**.
- **OntoUML Server / OaaS** — microservices: model verification, transform to gUFO-OWL, transform to relational schema, modularization. Strong build-vs-borrow candidate for the projection + L2 verification steps.
- **ontouml-metamodel / ontouml-js / ontouml-models-lib** — the implementation-independent metamodel and canonical **JSON schema**; aligning the AgentArmy `model.yaml` IR to this schema unlocks the whole ecosystem (verification, transformation, the OntoUML/UFO Catalog as a test corpus).
- **Tonto** — a textual DSL for OntoUML (an alternative IR authoring surface).
- **gufo2html** — gUFO → HTML docs (a ready-made docs projection).

## In the AgentArmy pipeline

- Anti-pattern detection = **Level 2** of the layered proof stack; run it on the IR before the reasoner.
- The IR `stereotype` field **is** the OntoUML class stereotype; the `relators:` block **is** the «relator» + «mediation» structure. Emit gUFO OWL from the IR (Level-3 target) and keep it drift-gated like the generated C#.
- Align the IR to the **ontouml-metamodel JSON schema** to borrow OaaS verification rather than hand-building Level 2.
