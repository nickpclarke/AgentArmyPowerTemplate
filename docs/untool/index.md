# untool.ai

**The point of a tool is not the tool. It is the work.**

untool.ai is an ontology-driven platform: a living model of objects, capabilities, and the
relations between them — served through one generic, contract-driven path, and operated by a
swarm of specialized agents. Documentation here describes the **platform**: how it thinks,
what it serves, and how its layers fit together.

## Start here

- **[Platform Architecture](../untool-platform.md)** — the system at a glance: surfaces vs.
  capabilities, the universal data adapter, and how the pieces compose.
- **[Ontology & Use Cases](ontology-and-use-cases.md)** — the object model: reified relations
  as holons, foundations as perspectives, and what the platform is *for*.

## The layers

untool.ai is built as composable layers, each developed in its own repository and aggregated
here. See **Platform Layers** for the per-layer documentation (synced from each layer):

| Layer | Role |
|---|---|
| **Frontend Core** | UI / BFF — the operator and product surface |
| **Middle Core** | Agent runtime — model authority, knowledge loop, ontology & data objects |
| **Backend Core** | Knowledge platform — graph store, credentials broker, LLM gateway, contracts |

## Architecture decisions

The **Architecture Decisions** section records the platform's design — the ontology pipeline,
the universal data adapter, temporal persistence, the generative (forge) pipeline, and more.

---

> This site is the untool.ai **platform** documentation. The AgentArmy template factory that
> generates these layers has its own docs at
> [nickpclarke.github.io/AgentArmy](https://nickpclarke.github.io/AgentArmy/).
