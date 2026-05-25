---
tags: [platform, data, database, vision]
track: data
---
# Graph + Relational Together

> [!note] The stance
> Don’t pick one store to rule them all. Pick one **model** to rule them all — then project into the best storage for each job.

**🎛 [[Obsidian Board]] · 🧠 [[Data & Database Science Track]] · 🧪 [[One Model, Many Projections]]**

## A workable division of labor

- **Graph (ArcadeDB / LPG)** — identity + relationships + provenance + hyperedges (see [[Reification-and-Hyperedges]])
- **Relational / analytical (BigQuery)** — aggregates, analytics, cheap scans
- **Runtime object graph (C#)** — scenario execution, policy gating, evidence assembly

## The anti-pattern to avoid

> [!danger] Storage-shaped truth
> If the ontology starts looking like table design, you’ve inverted the system. The model names reality; stores are projections.
