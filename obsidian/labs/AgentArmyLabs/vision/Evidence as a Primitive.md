---
tags: [vision]
---
# Evidence as a Primitive

`evidence-pack` + `IEvidenceSink` aren't a logging afterthought — make **evidence a first-class output of every scenario run**.

- Every scenario emits a deterministic evidence pack: object counts, step results, policy status, links to sources/chunks/exercise.
- "Done" is redefined: nothing completes without an evidence pack. **Evidence-driven, not just test-driven.**
- Evidence + [[Governance in the Model|decision-record]] = the platform's **audit + trust backbone**.

> [!tip] The agent angle
> In a world of non-deterministic agents, evidence is how you *verify* what an agent's action actually did. Agents act → the runtime evidences → humans/policy gate on the evidence. This is the concrete substrate under HITL.

**Determinism is the enabler.** A deterministic generator + deterministic runtime means the same model + inputs → identical evidence. That gives reproducibility, caching, and provable behavior — the **stable spine** agents act through.

**Stretch:** evidence as an event stream → event-sourced history → [[Open Questions and Risks|temporal "what did the system prove at time T"]].

Related: [[Model-Driven Platform]], [[Scenarios as Agent Tools]].
