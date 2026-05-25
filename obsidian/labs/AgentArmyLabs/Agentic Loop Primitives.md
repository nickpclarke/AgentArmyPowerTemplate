---
tags: [platform, agentic, vision]
track: platform
---
# Agentic Loop Primitives

> [!note] The goal
> Agents are non-deterministic. The platform spine has to be deterministic: **policy-gated scenarios that emit evidence**.

**🎛 [[Obsidian Board]] · 🧭 [[Platform Atlas]] · 🧱 [[Middle-Core]]**

## The minimal object model (starter set)

- **Scenario definition** → [[scenario-template]]
- **Run / execution** → [[capability-exercise]]
- **Deterministic proof bundle** → [[evidence-pack]]
- **Routing / gating decision** → [[decision-record]]
- **Work container** → [[work-packet]]

## Invariants (what stays true as everything grows)

1. **Evidence is the currency**: every meaningful action emits an evidence-pack (even if small).
2. **Policy is data**: safety, governance, and routing rules are modeled, reviewed, and versioned (see [[Governance in the Model]]).
3. **Projections are disposable**: regenerate contracts; preserve behavior boundaries (see [[Codegen vs Interpreted]]).
4. **Scenarios are the capability layer**: “add a capability” becomes “add a scenario + evidence contract” (see [[Scenarios as Agent Tools]]).

Related: [[Evidence as a Primitive]], [[Factory-Loop-Test-Infrastructure]].
