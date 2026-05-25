---
tags: [platform, data, database]
track: data
---
# Data Products & Semantic Contracts

> [!note] Definition
> A data product is not a table. It’s a **named, owned, versioned capability** that exposes data *with a semantic contract*.

**🎛 [[Obsidian Board]] · 🧠 [[Data & Database Science Track]] · 🧪 [[Model-Driven Platform]]**

## The contract (what must be explicit)

- **Vocabulary** — the model’s ontology terms (not storage column names)
- **Shape** — projections: OpenAPI schema, view schema, graph type, export format
- **Guarantees** — freshness, completeness, integrity constraints
- **Evidence** — how consumers verify the guarantees (e.g., checksums, counts, drift reports)

## Why AgentArmy cares

The platform is a *skill factory* ([[Skills as a Projection]]). Data products are a first-class output surface: agents can consume a product confidently when the contract is explicit and evidence is attached.
