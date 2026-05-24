---
tags: [vision]
---
# Codegen vs Interpreted

The core architectural fork for a model-driven runtime.

| | **Codegen** (v1 plan) | **Interpreted** (EnterpriseWeb-pure) |
|---|---|---|
| Model → | generated C# contracts compiled in | model read & executed at runtime |
| Wins | type safety, debuggability, determinism, IDE support | late binding, hot-reload, no rebuild to change behavior |
| Costs | rebuild to change the model; generator is a bottleneck | runtime errors, harder to debug, weaker typing |

> [!note] The v1 call is right
> Start with **codegen + an in-memory hypergraph**: deterministic, testable, and safe. It earns trust before adding dynamism.

**The likely end state is a hybrid:** generated *contracts* (types, IDs, schemas) for safety + an *interpreted orchestration* layer (scenario steps, policy, projections) for flexibility. The line to hold: **structure is compiled; behavior wiring is late-bound.**

> [!warning] The classic trap
> Editing generated code. The [[Disposable code|disposable-code rule]] (behavior in partial classes / plugins / handlers, never in `*.g.cs`) is what keeps regeneration free. This boundary is make-or-break.

Related: [[One Model, Many Projections]], [[Determinism]] note inside [[Evidence as a Primitive]].
