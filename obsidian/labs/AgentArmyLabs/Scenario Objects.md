---
tags: [oop, pattern, platform]
track: oop
---
# Scenario Objects

> [!note] Pattern
> Treat a scenario as an object with **inputs, policy, steps, and an evidence contract**. “Run scenario” becomes the stable API, even as internals evolve.

**🎛 [[Obsidian Board]] · 🧩 [[OOP Patterns for Agentic Platforms]] · 🧱 [[Middle-Core]]**

## Core responsibilities

- Validate inputs against the model
- Apply policy gates
- Orchestrate provider calls / projections
- Emit evidence-pack with deterministic structure

Related concepts: [[scenario-template]], [[capability-exercise]], [[evidence-pack]], [[Scenarios as Agent Tools]].
