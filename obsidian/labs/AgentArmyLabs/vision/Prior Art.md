---
tags: [vision, prior-art]
---
# Prior Art

Don't invent in a vacuum — these solve adjacent pieces of the model-driven vision.

- **LinkML** — *the closest match.* YAML-canonical data model → generates JSON-Schema, Python, SHACL, docs, ER diagrams. Almost exactly the v1 generator's job; worth studying or even adopting for the YAML→artifacts step instead of hand-rolling.
- **Palantir Foundry — Ontology** — objects + links + actions as the enterprise "digital twin"; actions ≈ our scenarios, evidence ≈ their audit.
- **EnterpriseWeb** — the stated inspiration: model-as-runtime, hypergraph, dynamic composition, late binding.
- **Temporal** — durable, deterministic workflow execution; a reference for [[Evidence as a Primitive|deterministic runs]] + replay.
- **dbt** — models → compiled, tested, documented SQL; the "disposable compiled artifact + tested model" discipline.
- **Model-Driven Engineering (EMF/Ecore)** — decades of metamodel→codegen lessons (and the maintenance traps to avoid → [[Codegen vs Interpreted]]).
- **JSON Canvas / RDF knowledge graphs** — the graph substrate; ArcadeDB is the runtime store.
- **[[IKW-GraphEngine (Parallel Track)|IKW-GraphEngine]]** — a friendly sibling project (Trinity/Graph Engine + BFO/CCO semantics, native hypergraphs, TSL→C# codegen, LIKQ). *Parallel learning track*, not a foundation: we stay OntoUML/UFO but design to **offer both** upper ontologies as projections.

> [!question] Build-vs-borrow
> The generator is the riskiest hand-built piece. **LinkML** could do much of it. Spike: can LinkML (or a thin wrapper) emit the C# contracts we need, or is a custom Python generator genuinely warranted?

Related: [[Model-Driven Platform]], [[One Model, Many Projections]].
