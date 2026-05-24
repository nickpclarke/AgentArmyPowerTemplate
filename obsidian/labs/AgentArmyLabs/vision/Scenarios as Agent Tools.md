---
tags: [vision]
---
# Scenarios as Agent Tools

The quiet payoff: **the model-driven runtime is also the agent capability layer.**

The chain already in the catalog:
`scenario-template` → `capability-exercise` (a run) → `evidence-pack` (proof) → `tool-offering` (MCP-exposable).

So: **model → generated scenario contracts → safe, evidenced `tool-offering`s → agents consume them over MCP.** Agents don't touch ArcadeDB or raw capabilities; they invoke *modeled, governed, evidenced* scenarios.

> [!important] This closes the loop with AgentArmy
> The whole platform exists to let agent armies do real work safely. Middle-core *generates* exactly the safe, composable, provable capabilities agents need — from the same model that defines everything else. The [[Universal Data Adapter]] connectors become tool-offerings too.

**Implication:** "adding an agent capability" becomes "adding a scenario to the model" — no bespoke tool code. The model is the capability registry.

Related: [[Governance in the Model]] (what makes a scenario *safe* to expose), [[One Model, Many Projections]].
