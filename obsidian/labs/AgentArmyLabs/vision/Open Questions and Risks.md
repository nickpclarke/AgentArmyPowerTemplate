---
tags: [vision, open-question]
---
# Open Questions and Risks

> [!danger] Watch these
> - **Projection drift** — any hand-edited target breaks "one model, many projections." Enforce with generated-files-current CI + the [[Codegen vs Interpreted|disposable-code boundary]].
> - **Authoritativeness of formal artifacts** — YAML vs DMN/SHACL/BPMN: which wins? Decide before they diverge ([[Governance in the Model]]).
> - **Second-system / modeling-everything** — the temptation to model the universe → analysis paralysis. Keep v1 to one scenario (`knowledge-drop`) and grow by need.
> - **Generator as bottleneck** — every change waits on regen + rebuild. Mitigate with the [[Codegen vs Interpreted|hybrid]] (interpret behavior wiring).
> - **Model governance** — `model.yaml` is the most powerful file; it needs its own review gate.

## Open questions
- Where exactly is the **generated ↔ hand-authored** line? (the make-or-break boundary)
- **Build the generator or adopt LinkML?** ([[Prior Art]])
- When does **ArcadeDB persistence + temporal snapshots** arrive (follow-up slice)?
- Does the [[Universal Data Adapter]] register its connectors as **modeled objects** from day one, so the two threads share `model.yaml`?
- How do **non-deterministic agents** propose model changes safely — via PRs/decision-records against the model?

Related: [[Model-Driven Platform]], [[Evidence as a Primitive]].
