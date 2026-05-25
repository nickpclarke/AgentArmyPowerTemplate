---
tags: [platform, data, database, data-science, scenario]
track: data
---
# Schema Scout as Science

> [!abstract] Treat inspection as an experiment
> “Schema scout” isn’t a manual poke. It’s a **scenario** that produces repeatable measurements: type inventory, index inventory, sample distributions, drift deltas.

**🎛 [[Obsidian Board]] · 🧠 [[Data & Database Science Track]] · 🧱 [[Middle-Core]]**

## What the scenario should prove

- **What exists** — types/tables, properties/columns, edges/relationships
- **How it’s indexed** — index inventory + cardinalities
- **What changed** — drift report since last snapshot
- **What’s safe** — query guards, limits, redaction boundaries (see `read-only-query-lab` in [[Scenarios]])

## Evidence outputs (starter kit)

- Counts (per type/table)
- Sample rows/vertices (bounded)
- Histogram sketches (bounded)
- Drift diff (type/property/index deltas)

Related: [[Evidence as a Primitive]], [[Factory-Loop-Test-Infrastructure]].
