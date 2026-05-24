---
tags: [vision]
---
# One Model, Many Projections

**Thesis:** the `model.yaml` is the single source of truth; every other representation is generated *from* it and never hand-edited.

Projections of the one model:
- **C# contracts** (`*.g.cs`) — compile-time type safety for the runtime
- **ArcadeDB schema** — vertex/edge types the data actually lives in
- **OpenAPI contract** — the API surface frontend-core generates its client from
- **Agent tool-offerings (MCP)** — safe, callable capabilities
- **Agent Skills** (`SKILL.md`) — generated capabilities any agent picks up ([[Skills as a Projection]])
- **This Obsidian ontology** — the human-facing graph
- **Docs tables** — generated reference

> [!important] Consequence
> The [[Universal Data Adapter]]'s connection registry is itself modeled objects (Connection, Connector, Pipeline, Capability). So the adapter's CDM **is** the platform model — not a separate schema. Define once, project everywhere.

**Risk:** projection drift. If any target gets hand-edited, the "single source" lie collapses. Enforced by the [[Codegen vs Interpreted|generated-vs-hand-authored boundary]] and "generated files must be current" CI.

Related: [[Model-Driven Platform]], [[Prior Art]] (LinkML does exactly this for YAML→schemas/code).
