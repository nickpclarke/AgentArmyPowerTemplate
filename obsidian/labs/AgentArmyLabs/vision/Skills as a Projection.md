---
tags: [vision]
---
# Skills as a Projection

> [!abstract] The generalization
> The model-driven generator's output **isn't only C#.** A scenario / `tool-offering` in the model can project to **Agent Skills** (`SKILL.md`), **MCP tool definitions**, OpenAPI operations, even UI forms — any consumer surface. Code is one target; *capabilities* are another.

This extends [[One Model, Many Projections]] with a self-referential twist: **the platform's model generates the very skills its agents use.**

- `tool-offering` (modeled, governed, evidenced) → emit a **`SKILL.md`** (Agent Skills spec) → any agent (Claude, Codex, Copilot) picks it up.
- Same object → emit an **MCP tool** for runtime invocation.
- The just-installed kepano **obsidian-skills** are this exact format — proof the target is standard and real.

> [!tip] Why this is the unlock
> "Add an agent capability" collapses to **"add a scenario to `model.yaml` and regenerate."** Skills stop being hand-written and drift-prone; they become **generated, versioned, evidenced projections** of the one model. The generator becomes a *skill factory*. See [[Scenarios as Agent Tools]].

> [!question] Open questions
> - Minimal model fields → a good `SKILL.md` (name, *description-for-triggering*, inputs, evidence contract)?
> - How do generated skills stay safe? ([[Governance in the Model]])
> - Do they publish to a marketplace the armies subscribe to (like we did with kepano)?

Related: [[Model-Driven Platform]], [[One Model, Many Projections]], [[Open Questions and Risks]].
