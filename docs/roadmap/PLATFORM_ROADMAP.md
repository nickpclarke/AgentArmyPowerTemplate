# AgentArmy Template Platform Roadmap
## Strategic Brief & Visual Roadmap (2026 Q2–Q4)

---

## Executive Summary

AgentArmy must climb from **Custom/Manual orchestration** (today) to **Self-Service, Observable, Cost-Optimized Platform** (6 months). The competitive pressure is real: new agent frameworks (Copilot extensibility, Anthropic Managed Agents) are disrupting the routing/orchestration layer that AgentArmy currently executes by hand.

**The keystone move:** Convert the static CLAUDE.md routing table into an **executable policy engine**. This single shift unblocks intelligent routing, spoke self-service, observability, and the learning loop — everything downstream depends on it.

**Investment thesis:** Spend capital building genesis (A: spoke instantiation, D: learning loop) and refuse to fight the commodity wars (E/F: observability, cost). Let Langfuse/Helicone commoditize those layers while you climb the moat.

---

## The Wardley Map (Strategic Landscape)

Below is the OWM syntax for `create.wardleymaps.ai`. **Key insight:** Your most evolved asset is Agent Definitions (180 specialists, already in Product stage). Your biggest vulnerability is the static routing table (Custom, treating it as ground truth when it should be a hypothesis).

```wardley
title AgentArmy Platform Evolution — Self-Service, Observable, Cost-Optimized Orchestration

anchor Developer / Platform Team [0.98, 0.34]

component Self-Service Spoke Instantiation [0.93, 0.10] label [-60, -5]
component Intelligent Agent Routing [0.80, 0.22] label [10, -8]
component Cross-Agent Choreography [0.62, 0.18] label [-95, 5]
component Learning Loop (Teachable Failure) [0.55, 0.12] label [12, -2]
component Agent-Run Observability [0.45, 0.30] label [12, 6]
component Pre-Delegation Cost Visibility [0.42, 0.28] label [-150, 0]
component Agent Definitions (180) [0.50, 0.45] label [10, -10]
component Agent Registry + MECE Governance [0.35, 0.40] label [-175, 6]
component Coordination Plane (GitHub Projects) [0.30, 0.72] label [10, 8]
component CI/CD Runtime (GitHub Actions) [0.20, 0.78] label [10, -10]
component LLM Inference (Claude / Copilot) [0.15, 0.68] label [-130, 5]
component Compute / Hosting [0.08, 0.90] label [10, 5]

Developer / Platform Team->Self-Service Spoke Instantiation
Developer / Platform Team->Intelligent Agent Routing
Developer / Platform Team->Agent-Run Observability
Developer / Platform Team->Pre-Delegation Cost Visibility
Self-Service Spoke Instantiation->Intelligent Agent Routing
Intelligent Agent Routing->Cross-Agent Choreography
Cross-Agent Choreography->Learning Loop (Teachable Failure)
Learning Loop (Teachable Failure)->Agent-Run Observability
Intelligent Agent Routing->Agent Definitions (180)
Intelligent Agent Routing->Agent Registry + MECE Governance
Cross-Agent Choreography->LLM Inference (Claude / Copilot)
Agent-Run Observability->LLM Inference (Claude / Copilot)
Pre-Delegation Cost Visibility->LLM Inference (Claude / Copilot)
Intelligent Agent Routing->Coordination Plane (GitHub Projects)
Cross-Agent Choreography->CI/CD Runtime (GitHub Actions)
Coordination Plane (GitHub Projects)->Compute / Hosting
CI/CD Runtime (GitHub Actions)->Compute / Hosting
LLM Inference (Claude / Copilot)->Compute / Hosting

evolve Self-Service Spoke Instantiation 0.55 label [12, -3]
evolve Intelligent Agent Routing 0.60 label [12, -8]
evolve Cross-Agent Choreography 0.45 label [10, 6]
evolve Learning Loop (Teachable Failure) 0.42 label [12, 4]
evolve Agent-Run Observability 0.68 label [10, -10]
evolve Pre-Delegation Cost Visibility 0.70 label [-40, -12]
evolve LLM Inference (Claude / Copilot) 0.85 label [10, 6]

pipeline Agent Definitions (180) [0.40, 0.50]

note Inertia: static CLAUDE.md table = knowledge+cultural inertia [0.74, 0.30]
note WAR zone: vendors commoditizing agent obs/cost (Langfuse, Helicone) [0.40, 0.40]
note WONDER: choreography+learning loop is new genesis above commodity LLMs [0.60, 0.05]

annotation 1 [0.80, 0.22] Routing must become a policy engine, not a doc
annotation 2 [0.55, 0.12] Learning loop is the durable moat
```

**How to use:** Paste the OWM block above into https://create.wardleymaps.ai to render the full map interactively.

---

## Strategic Plays (Sequenced Execution)

| # | Play | What | Why | Timeline | Viability |
|---|------|------|-----|----------|-----------|
| **1** | **Sensing Engine** | Instrument delegation flow → OTel spans (borrow Langfuse) | Unlocks doctrine: situational awareness + flow metrics | Weeks 1–4 (Jun) | HIGH — borrow, don't build |
| **2** | **Manage Inertia / Policy Engine** | Convert CLAUDE.md table → executable routing policy resolver | Removes keystone constraint; unblocks spoke init + choreography | Weeks 5–7 (mid-Jul) | HIGH — CRITICAL dependency |
| **3** | **Land & Expand (Spoke Init)** | Ship `spoke init` generator; wires repo + board + armies automatically | First user-facing win; depends on Play 2 | Weeks 8–9 (late Jul) | HIGH |
| **4** | **Learning Loop (Durable Moat)** | Operationalize `error-coordinator` + `knowledge-synthesizer` runtime; close the loop on failures | Builds what competitors cannot replicate (your failure history) | Weeks 5–10 (concurrent) | HIGH — genius zone |
| **5** | **Buy, Don't Build (Obs/Cost)** | Integrate Langfuse + Helicone; abstract LLM provider (avoid lock-in) | Frees capital for Play 4; lets vendors win the commodity WAR | Weeks 8–11 (concurrent) | HIGH — strategic deferral |
| **6** | **Open Standard** (Future) | Release routing policy schema + spoke-init as open standard | Build ecosystem; commoditize the layer beneath your moat | After Plays 1–4 prove model | MEDIUM — requires proof first |

---

## Release Train Structure & Alignment

Four 10-week release trains, layered by capability maturity and dependency order:

### Release Train 1: Foundation & Routing (Plays 1, 2 + enablers)
**Duration:** Jun 1 – Jul 12 (~6 weeks)  
**Theme:** Make agent capabilities explicit; routing deterministic.

| Feature | Area | Type | Size | Routing | Outcome |
|---------|------|------|------|---------|---------|
| Agent Spec Template + Capability Matrix | 1 | Feature | M | `agent-distinctiveness-advocate` | Definitions + governance → transparent, queryable |
| Executable Routing Decision Tree (.yaml) | 6 | Feature | M | `architect-reviewer` | CLAUDE.md → policy engine (executable + auditable) |
| Telemetry Instrumentation (OTel spans) | Play 1 | Enabler | M | `observability-engineer` | Flow is now measurable |
| Few-Shot Prompt Library (Phase 1) | 2 | Enabler | M | `prompt-engineer` | System prompt patterns per agent category |

**Block Diagram:**
```
Developer
   ↓
Routing Policy Engine ← Agent Specs + Governance
   ↓
Instrumentation (telemetry)
   ↓
Ready for Plays 2–5
```

---

### Release Train 2: Operations & Quality (Plays 3, 4, 5 + operationals)
**Duration:** Jul 12 – Aug 23 (~6 weeks)  
**Theme:** Formalize multi-agent workflows; measure quality; establish learning loop.

| Feature | Area | Type | Size | Routing | Outcome |
|---------|------|------|------|---------|---------|
| Multi-Agent Choreography (Saga patterns, state machines) | 3 | Feature | L | `workflow-orchestrator` | Handoffs explicit; compensation on failure |
| Agent Evaluation Gates (DoD rubrics, SLI/SLO framework) | 4 | Feature | M | `observability-engineer` + `qa-expert` | Quality is measurable |
| Skill Scaffolding & Composition | 5 | Feature | M | `tooling-engineer` | Skills versioned, composable, discoverable |
| Learning Loop Runtime (`error-coordinator` + `knowledge-synthesizer`) | Play 4 | Enabler | M | `knowledge-synthesizer` | Failures are teachable; patterns accumulate |
| Cost Visibility & Provider Abstraction | Play 5 | Enabler | M | `finops-engineer` | Token budgets visible; multi-vendor abstraction |

**Block Diagram:**
```
Routing Policy Engine
   ↓
Choreography Patterns + Quality Gates
   ↓
Learning Loop (failures → lessons)
   ↓
Cost Transparency + Observability
   ↓
Ready for spoke onboarding (RT3)
```

---

### Release Train 3: Spoke Readiness & Observability (Play 3 completion + operationals)
**Duration:** Aug 23 – Oct 4 (~6 weeks)  
**Theme:** Spoke teams self-serve; cost is visible; observability is wired.

| Feature | Area | Type | Size | Routing | Outcome |
|---------|------|------|------|---------|---------|
| Hub→Spoke Onboarding Playbook (checklists, pre-commit hooks) | 9 | Feature | M | `platform-engineer` | Spoke instantiation is scriptable, not manual |
| Cost & Capacity Model (unit economics, showback) | 7 | Feature | L | `finops-engineer` | Team X can see the cost of delegating work Y |
| Spoke-Specific Prompt Adaptation (greenfield vs. legacy context) | 2 Phase 2 | Story | S | `prompt-engineer` | Prompts adapt to spoke context |
| Observability Dashboard (MTTR, success rate, cost per delegation) | 10 Phase 1 | Enabler | M | `observability-engineer` | Visibility into agent health + behavior |

**Block Diagram:**
```
Routing + Orchestration + Learning Loop
   ↓
Spoke Init (automated)
   ↓
Cost Model + Observability Dashboard
   ↓
Ready for advanced learning (RT4)
```

---

### Release Train 4: Learning & Advanced Observability (Play 4 completion + intelligence)
**Duration:** Oct 4 – Nov 15 (~6 weeks)  
**Theme:** Accumulate and share lessons; trace agent decisions; iterate on routing.

| Feature | Area | Type | Size | Routing | Outcome |
|---------|------|------|------|---------|---------|
| Agent Lesson-Learned KB (incident log, anti-patterns library) | 8 | Feature | M | `knowledge-synthesizer` | Failures become institutional learning |
| Request Tracing & Decision Audit Log (end-to-end visibility) | 10 Phase 2 | Feature | L | `observability-engineer` | Why did agent X route to Y? Fully auditable |
| Feedback Integration (PR reviews → routing/prompt refinement) | 10 Phase 3 | Enabler | S | `prompt-engineer` | Failures feed back into agent definitions |
| Competency Evolution Tracking (which agents improved on task type T?) | 8 Phase 2 | Story | M | `knowledge-synthesizer` | Agent performance is measurable over time |

**Block Diagram:**
```
Learning Loop + Observability
   ↓
Lesson KB + Tracing
   ↓
Feedback loops (rework → prompt/routing refinement)
   ↓
Continuous improvement cycle
```

---

## Prioritization Matrix (Effort vs. Impact)

```
HIGH IMPACT
    │
    ├─ 🎯 QUICK WINS (execute first)
    │  • Routing Policy Engine (CRITICAL: unblocks 3+)
    │  • Agent Registry Query (medium impact, easy)
    │
    ├─ 🚀 STRATEGIC BETS (invest heavily)
    │  • Self-Service Spoke Init (user-facing differentiator)
    │  • Learning Loop Runtime (durable moat)
    │  • Choreography Patterns (enables multi-agent work)
    │
    ├─ 🔧 PLUMBING (concurrent, medium ROI)
    │  • Prompt Library Phase 1
    │  • Evaluation Rubrics
    │  • Hub-Spoke Playbook
    │
    └─ 🛒 BUY, DON'T BUILD (defer or consume)
       • Observability Integration → consume Langfuse
       • Cost Estimation → consume Helicone/provider APIs

LOW EFFORT  ←────────────────────────→  HIGH EFFORT
```

---

## Key Decisions & Trade-Offs

### Decision 1: Build vs. Buy Observability/Cost
**Option A:** Build your own telemetry/cost platform.
- Pros: Full control, agile iteration
- Cons: Commodity layer, vendors racing downward, burns genesis capital

**Option B:** Consume Langfuse/Helicone; build only AgentArmy-specific adapters (RECOMMENDED).
- Pros: Free up resources for moat (learning loop); ride the vendor price war; faster TTM
- Cons: Dependency on third-party vendor roadmaps

✅ **Decision: OPTION B (Buy, don't build).** This is the strategic deferral that funds Play 4 (learning loop), which is unreplicable.

---

### Decision 2: Spoke Instantiation Timing
**Option A:** Wait for all infrastructure (RT1 + RT2) before launching spoke init.
- Pros: More mature feature set at spoke launch
- Cons: Delayed user value; competitive window closes

**Option B:** Land spoke init in RT1 (after routing policy exists), then expand with observability/cost in RT2/3 (RECOMMENDED).
- Pros: Early user value + feedback; land-and-expand model
- Cons: Early spokes may lack observability (acceptable MVP)

✅ **Decision: OPTION B (Land and expand).** Routing policy + spoke init ship together; observability follows.

---

### Decision 3: Release Train Sequencing
**Strict dependency chain:**
Play 1 (Sensing) → Play 2 (Policy Engine) → Play 3 (Spoke Init)

Plays 4 (Learning Loop) and 5 (Buy Obs/Cost) run **concurrent with Play 2 onward** — they don't block each other.

---

## Doctrine Assessment (Quick Summary)

The three principles most critical to improve:

1. **Situational Awareness (score 2/5)** — Static CLAUDE.md table is a *report*, not a map. Play 1 (telemetry) + Play 2 (policy engine) fix this.
2. **Manage Inertia (score 2/5)** — The table feels like documentation when it's actually the platform's biggest constraint. Naming it + converting it to executable code removes this drag.
3. **Optimize Flows (score 2/5)** — Without measuring delegation flow (request → route → execute → succeed/fail → cost), you can't make failures teachable or costs transparent.

All four release trains improve these three principles simultaneously.

---

## Climatic Patterns (External Forces)

| Force | Likelihood | Impact | Direction |
|-------|-----------|--------|-----------|
| LLM inference commoditizes | **5/5** | **5/5** | **Accelerant** — consume, don't build; stay multi-vendor |
| Agent obs/cost vendors race | **4/5** | **5/5** | **Accelerant** — buy those layers |
| Static table inertia persists | **5/5** | **4/5** | **Threat** — convert to policy engine |
| Competitors (Copilot, Managed Agents) disrupt routing | **4/5** | **5/5** | **Threat** — you must commoditize routing so competitors commoditize the *layer beneath* your moat (learning loop) |
| New value in choreography + learning loop | **5/5** | **5/5** | **Accelerant** — your blue ocean |

---

## Success Criteria (by Release Train)

### RT1 (Foundation & Routing) ✓
- [ ] Routing policy engine is executable (label → army → agent)
- [ ] Agent specs are documented + governance is active
- [ ] Telemetry spans are emitted for every delegation
- [ ] Agent definitions are queryable from a catalog

### RT2 (Operations & Quality) ✓
- [ ] Choreography patterns are codified (sagas, compensation)
- [ ] DoD rubrics exist per agent type
- [ ] Learning loop closes: failures → `error-coordinator` → `knowledge-synthesizer` → KB entry
- [ ] Cost model is estimated (not yet live)

### RT3 (Spoke Readiness) ✓
- [ ] `spoke init` command spins up a layer repo + board + armies
- [ ] Observability dashboard shows MTTR, success rate, cost per delegation
- [ ] Onboarding playbook is complete + tested on ≥1 real spoke

### RT4 (Learning & Intelligence) ✓
- [ ] Lesson KB has ≥10 incident entries with root cause + remedy
- [ ] Request tracing shows full delegation flow (issue → label → route → PR → merge)
- [ ] Feedback loop is live: PR comments → routing/prompt refinement
- [ ] Agent competency tracking shows improvement trends

---

## Budget & Capacity Estimate

| Release Train | Duration | Team Size | Agent Routing | Notes |
|---|---|---|---|---|
| RT1 | 6 weeks | 2.5 FTE | `agent-distinctiveness-advocate`, `architect-reviewer`, `observability-engineer`, `prompt-engineer` | Foundation blocks RT2–4 |
| RT2 | 6 weeks | 3 FTE | `workflow-orchestrator`, `observability-engineer`, `knowledge-synthesizer`, `tooling-engineer` | Concurrent with Play 4, 5 |
| RT3 | 6 weeks | 2.5 FTE | `platform-engineer`, `finops-engineer`, `prompt-engineer`, `observability-engineer` | Spoke feedback informs RT4 |
| RT4 | 6 weeks | 2 FTE | `knowledge-synthesizer`, `observability-engineer`, `prompt-engineer` | Continuous improvement |

**Total:** 6 months, ~2.5–3 FTE average, 10–12 agents routing across 2 armies.

---

## Next Steps (After Approval)

1. **Review this roadmap** — does the Wardley map resonate? Any doctrine points to prioritize differently?
2. **Approve release train sequencing** — is RT1→RT2→RT3→RT4 the right order?
3. **Create GitHub issues** from features above with:
   - Type, PI, Size, Estimate set
   - Parent/child hierarchy (Epic → Feature → Story/Enabler)
   - Routing guidance (which agents + armies own each item)
   - Dependencies marked
4. **Add to the GitHub Projects board** — set Status, Priority, Start/Target dates
5. **Kick off Play 1 (Sensing Engine)** — week of Jun 1

---

## Appendix: Build/Buy/Borrow Decisioning

| Component | Stage | Decision | Why |
|---|---|---|---|
| A. Self-Service Spoke Instantiation | Genesis | **Build** | Differentiator; no vendor exists |
| B. Intelligent Agent Routing | Custom | **Build** | Core platform; declarative policy engine |
| C. Cross-Agent Choreography | Custom | **Build (on borrowed primitives)** | Use GitHub Actions DAG; encode your choreography |
| D. Learning Loop | Genesis | **Build** | Unreplicable asset; your moat |
| E. Agent-Run Observability | Custom→Product | **Buy (Langfuse)** | Commodity racing toward product; don't build |
| F. Pre-Delegation Cost Visibility | Custom | **Buy (Helicone) + thin build** | Buy metering; build the estimate surface |
| G. Agent Definitions (180) | Product | **Build (own)** | Already built; maintain via governance |
| H. Agent Registry + MECE Governance | Product (early) | **Build (own)** | Already scaffolded; productize the catalog |
| I. Coordination Plane | Commodity | **Consume (GitHub Projects)** | Never build |
| J. CI/CD Runtime | Commodity | **Consume (GitHub Actions)** | Never build |
| K. LLM Inference | Product→Commodity | **Consume; abstract provider** | Avoid lock-in; stay multi-vendor |
| L. Compute / Hosting | Commodity | **Consume** | Never build |

---

**Document prepared:** 2026-05-23  
**Review by:** [Your team]  
**Approval date:** [TBD]  
**Release date (RT1 kick-off):** 2026-06-01
