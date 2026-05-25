# Meta-Planning: Governing the Template Platform

Strategic governance for how AgentArmy template system itself evolves and improves.

**This is NOT about planning features.** See `/docs/release-trains/` for that.  
**This is about planning how we PLAN** — principles, ceremonies, decision frameworks, and learning workflows.

---

## Why Meta-Planning Exists

**Problem:** The agent army has grown to 168 agents across 11 categories. Governance artifacts exist (MECE rubric, scorecard, taxonomy docs) but they are not *enforced* or *integrated into operations*.

**Result:** Boundary rules documented in scorecard don't propagate to agent descriptions. New agents are added without checking if they violate existing principles. Learning from production incidents doesn't feed back to principle refinement. Spokes have no template for establishing their own governance.

**Solution:** Meta-planning establishes the **governance layer** that connects aspirational principles → decisions → agent onboarding → operational feedback → principle evolution.

---

## Folders

- **`principles/`** — Foundational axioms (ARMY_PRINCIPLES.md)
- **`decisions/`** — Decision frameworks (AGENT_ONBOARDING_RUBRIC.md)
- **`spoke-templates/`** — What a forked Spoke should set up in its own `/planning/meta/`

---

## Critical Documents

| Document | Purpose | Audience | Cadence |
|---|---|---|---|
| `principles/ARMY_PRINCIPLES.md` | Core axioms for how the army operates | All agents, team, Spoke authors | Review quarterly |
| `decisions/AGENT_ONBOARDING_RUBRIC.md` | Checklist for validating new agents | `agent-distinctiveness-advocate`, architects | Per-agent (before merge) |
| `spoke-templates/SPOKE_META_PLANNING_TEMPLATE.md` | What a Spoke should create in its own `/planning/meta/` | Fork users | Reference (timeless) |

> **Planned (not yet created):** `ceremonies/PLANNING_CEREMONIES.md` (planning cadence), `decisions/DECISION_FRAMEWORK.md` (trade-off framework), and `learning/INCIDENT_TO_PRINCIPLE_WORKFLOW.md` (production → KB → principle loop). Status is tracked in [`../MARKDOWN_SAFE_ARTIFACTS_REPORT.md`](../MARKDOWN_SAFE_ARTIFACTS_REPORT.md). The Governance Loop below describes how these fit once they exist.

---

## The Governance Loop

```
Production
   ↓ (incident captured by Stop hook)
error-coordinator analyzes failure
   ↓
knowledge-synthesizer extracts pattern
   ↓
Pattern added to KB & anti-patterns library
   ↓
Principle review ceremony (quarterly)
   ↓ (principle refined or new principle added)
ARMY_PRINCIPLES.md updated
   ↓
AGENT_ONBOARDING_RUBRIC.md constraints updated
   ↓
New agents checked against updated rubric
   ↓
Next incident avoided or handled faster
   ↓ (cycle repeats)
```

This is what **closes the learning loop**.

---

## Key Differences from `/docs/release-trains/`

| Aspect | Release Trains | Meta-Planning |
|---|---|---|
| **Scope** | Feature delivery (RT1–RT4, 6 months) | Governance & principle evolution (ongoing) |
| **Output** | Shipped features, artifact deliverables | Policy documents, enforcement rules |
| **Audience** | Engineers, PMs, delivery team | Architects, governance leads, new Spokes |
| **Cadence** | 6-week release trains | Quarterly principle review, continuous learning loop |
| **GitHub Projects** | Issues, sprints, burndown | No; decisions are documented directly |

---

## Quick Navigation

- **Starting to add a new agent?** → `decisions/AGENT_ONBOARDING_RUBRIC.md`
- **Foundational axioms?** → `principles/ARMY_PRINCIPLES.md`
- **Forking into a Spoke?** → `spoke-templates/SPOKE_META_PLANNING_TEMPLATE.md`

---

**Last Updated:** 2026-05-23  
**Audit Baseline:** 70/100 MECE score  
**Next Review:** Q2 2026 (after RT1 kickoff)

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
