---
tags: [vision]
---
# Governance in the Model

Policy isn't bolted on — it's **modeled** alongside objects and scenarios.

- **DMN** (decisions) → routing, eligibility, gates as data.
- **SHACL** (constraints) → what a valid object/graph looks like; validation by the runtime.
- **decision-record** → the auditable trace of HITL/policy/architecture choices.

> [!tip] Why this scales agent autonomy
> You can only safely let agents act if the rules are explicit, enforced, and evidenced. Modeled policy + runtime enforcement + [[Evidence as a Primitive|evidence]] = autonomy with guardrails. The more of the policy that lives in the model, the less ad-hoc human review each action needs.

**Tension (v1):** the plan *references* DMN/SHACL by ID rather than compiling them. Fine to start — but decide early whether YAML stays authoritative with DMN/SHACL as exports, or those become authoritative later. Drift between them is the risk ([[Open Questions and Risks]]).

> [!note] Governance of the model itself
> `model.yaml` becomes the most powerful file in the platform. Who may edit it? That edit path needs its own gate — model changes are architecture changes.

Related: [[Scenarios as Agent Tools]], [[Model-Driven Platform]].
