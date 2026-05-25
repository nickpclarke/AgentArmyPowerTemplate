---
tags: [moc]
---
# Taxonomy & Glossary

The controlled vocabulary for this vault. **Use these tags consistently** so notes cluster in the graph and Bases/searches stay reliable. Back to [[Welcome]].

## Index — all pages by concept

### Hubs (maps of content)
- [[Welcome]] — home / map of content
- [[Taxonomy]] — tags, glossary, this index
- [[Model-Driven Platform]] — vision MOC
- [[Middle-Core]] — ontology MOC

### Vision — the model-driven bet
- [[Model-Driven Platform]]
- [[One Model, Many Projections]]
- [[Skills as a Projection]]
- [[Codegen vs Interpreted]]
- [[Evidence as a Primitive]]
- [[Scenarios as Agent Tools]]
- [[Governance in the Model]]
- [[Prior Art]]
- [[IKW-GraphEngine (Parallel Track)]]
- [[UFO & GraphEngine Ecosystem]]
- [[Open Questions and Risks]]

### Middle-Core ontology
- [[Middle-Core]] (MOC) · [[Scenarios]] · `Middle-Core.base` (live DB view)
- ArcadeDB capability layer: [[knowledge-source]] · [[knowledge-chunk]] · [[knowledge-graph-snapshot]]
- Platform operational: [[work-packet]] · [[decision-record]] · [[evidence-pack]]
- Meta-services: [[capability-exercise]] · [[tool-offering]] · [[scenario-template]]

### Converging thread
- [[Universal Data Adapter]]

## Tags
| Tag                | Use on                                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| `#moc`             | maps of content / hub notes ([[Welcome]], [[Model-Driven Platform]], [[Middle-Core]], [[Taxonomy]]) |
| `#vision`          | skunkworks vision / concept notes (the `vision/` folder)                                            |
| `#middle-core`     | middle-core business objects + scenarios                                                            |
| `#business-object` | a single catalog object type                                                                        |
| `#scenario`        | a scenario definition                                                                               |
| `#open-question`   | unresolved questions to revisit                                                                     |
| `#prior-art`       | external references / inspiration                                                                   |

**Rule:** every note gets at least one tag. Hubs → `#moc`; concept notes → `#vision`; catalog entities → `#middle-core` (+ `#business-object`).

## Glossary
- **model.yaml** — the single canonical model; everything else is a [[One Model, Many Projections|projection]].
- **projection** — a generated artifact from the model: C# contracts, ArcadeDB schema, OpenAPI, MCP tools, [[Skills as a Projection|agent skills]], docs.
- **business object** — an ontology concept the platform observes (see [[Middle-Core]]).
- **scenario** — a reusable flow that exercises capabilities and emits evidence (see [[Scenarios]]).
- **evidence-pack** — the deterministic proof a scenario produces (see [[Evidence as a Primitive]]).
- **capability-exercise** — a run of a `scenario-template`.
- **tool-offering** — a safe capability eligible for MCP / skill exposure.
- **hypergraph runtime** — middle-core's in-memory object+edge graph that executes scenarios.
- **generated vs hand-authored** — generated code is disposable; behavior lives in partials/plugins/handlers (see [[Codegen vs Interpreted]]).
- **Skunkworks → Labs → Board → Docs** — the idea-maturity pipeline ([[Welcome]]).
