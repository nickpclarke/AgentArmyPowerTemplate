# Release Train Master Index

Complete index of all Release Trains (RT1–RT4) for AgentArmy template platform evolution. 6-month roadmap (Jun 2026 – Nov 2026).

## Summary

| RT | Name | Duration | Team | Issues | Status |
|---|---|---|---|---|---|
| **RT1** | Foundation & Routing | Jun 1 – Jul 12 | 3.0 FTE | 7 (#17–23) | Planning |
| **RT2** | Operations & Quality | Jul 12 – Aug 23 | 3.5 FTE | 7 (#24–30) | Waiting for RT1 |
| **RT3** | Spoke Readiness | Aug 23 – Oct 4 | 2.5 FTE | 6 (#31–36) | Waiting for RT2 |
| **RT4** | Learning & Intelligence | Oct 4 – Nov 15 | 2.0 FTE | 5 (#37–41) | Waiting for RT3 |

**Total:** 25 issues across 4 epics  
**Total Effort:** ~11 FTE-weeks (2.75 FTE average × 4 RTs)  
**Timeline:** 24 weeks (6 months)

---

## Release Train 1: Foundation & Routing

**Epic:** #17  
**Duration:** Jun 1 – Jul 12 (6 weeks)  
**Team:** 3.0 FTE  
**Status:** Ready to kick off

### Features

| # | Title | Size | Est. | Status |
|---|---|---|---|---|
| 18 | Agent Spec Template + Capability Matrix | M | 5 | Backlog |
| 19 | Executable Routing Decision Tree (YAML) | L | 8 | Backlog |
| 20 | Claude Code Hook System (5 types) | L | 13 | Backlog |
| 21 | Project Context Graph Injection | L | 8 | Backlog |
| 22 | Telemetry Instrumentation (OTel spans) | M | 5 | Backlog |
| 23 | Few-Shot Prompt Library (Phase 1) | M | 3 | Backlog |

### Critical Success Factors

- Routing determinism >90%
- Telemetry >500 delegations  
- Context injection >95% success
- Hook system stable (<5ms overhead, zero timeouts)
- All 6 features merged

### Direct Links

- [#17 Epic](https://github.com/nickpclarke/AgentArmy/issues/17)
- [#18 Agent Specs](https://github.com/nickpclarke/AgentArmy/issues/18)
- [#19 Routing Tree](https://github.com/nickpclarke/AgentArmy/issues/19) ← Keystone
- [#20 Hook System](https://github.com/nickpclarke/AgentArmy/issues/20) ← Critical
- [#21 Context Graph](https://github.com/nickpclarke/AgentArmy/issues/21)
- [#22 Telemetry](https://github.com/nickpclarke/AgentArmy/issues/22)
- [#23 Prompt Library](https://github.com/nickpclarke/AgentArmy/issues/23)

---

## Release Train 2: Operations & Quality

**Epic:** #24  
**Duration:** Jul 12 – Aug 23 (6 weeks)  
**Team:** 3.5 FTE  
**Status:** Waiting for RT1 completion

### Features

| # | Title | Size | Est. | Status |
|---|---|---|---|---|
| 25 | Multi-Agent Choreography (Saga patterns) | L | 8 | Backlog |
| 26 | Agent Evaluation Gates (SLI/SLO framework) | M | 5 | Backlog |
| 27 | Skill Scaffolding & Composition (Recipes) | M | 5 | Backlog |
| 28 | Learning Loop Runtime (error + synthesizer) | L | 8 | Backlog |
| 29 | Artifact Lifecycle & Multi-Rendering | M | 5 | Backlog |
| 30 | Cost Visibility & Provider Abstraction | M | 5 | Backlog |

### Critical Success Factors

- Learning loop closes: failures → KB entry
- Rework reduced ≥20%
- ≥10 incident records in KB
- Multi-rendering adopted for all strategic artifacts
- All 6 features merged

### Dependencies (Block Chart)

```
RT1 Completion
  ├─ #25: Choreography (blocks #26, #28, #29)
  ├─ #26: Evaluation Gates (depends on #22 Telemetry)
  ├─ #27: Skill Scaffolding (depends on #18 Agent Specs)
  ├─ #28: Learning Loop (depends on #22, #20, critical)
  ├─ #29: Artifact Lifecycle (depends on #20, #21)
  └─ #30: Cost Visibility (depends on #22 Telemetry)
```

### Direct Links

- [#24 Epic](https://github.com/nickpclarke/AgentArmy/issues/24)
- [#25 Choreography](https://github.com/nickpclarke/AgentArmy/issues/25)
- [#26 Evaluation Gates](https://github.com/nickpclarke/AgentArmy/issues/26)
- [#27 Skill Scaffolding](https://github.com/nickpclarke/AgentArmy/issues/27)
- [#28 Learning Loop](https://github.com/nickpclarke/AgentArmy/issues/28) ← Critical
- [#29 Artifact Lifecycle](https://github.com/nickpclarke/AgentArmy/issues/29)
- [#30 Cost Visibility](https://github.com/nickpclarke/AgentArmy/issues/30)

---

## Release Train 3: Spoke Readiness

**Epic:** #31  
**Duration:** Aug 23 – Oct 4 (6 weeks)  
**Team:** 2.5 FTE  
**Status:** Waiting for RT2 completion

### Features

| # | Title | Size | Est. | Status |
|---|---|---|---|---|
| 32 | Hub→Spoke Onboarding Playbook | M | 5 | Backlog |
| 33 | Cost & Capacity Model (unit economics) | M | 5 | Backlog |
| 34 | Artifact Manifest Export (spoke init) | S | 2 | Backlog |
| 35 | Observability Dashboard (MTTR, cost) | M | 5 | Backlog |
| 36 | Spoke-Specific Prompt Adaptation | S | 3 | Backlog |

### Critical Success Factors

- ≥1 real spoke instantiated
- Spoke init <2 hours (automated)
- Full context transferred via manifest.json
- All 5 features merged

### Dependencies (Block Chart)

```
RT2 Completion
  ├─ #32: Onboarding (depends on #19 Routing, #29 Manifest)
  ├─ #33: Capacity Model (depends on #30 Cost Tracking)
  ├─ #34: Manifest Export (depends on #29 Artifact Lifecycle)
  ├─ #35: Dashboard (depends on #22 Telemetry, #26 SLIs)
  └─ #36: Prompt Adapt (depends on #23 Prompt Library)
```

### Direct Links

- [#31 Epic](https://github.com/nickpclarke/AgentArmy/issues/31)
- [#32 Onboarding Playbook](https://github.com/nickpclarke/AgentArmy/issues/32)
- [#33 Cost & Capacity Model](https://github.com/nickpclarke/AgentArmy/issues/33)
- [#34 Artifact Manifest Export](https://github.com/nickpclarke/AgentArmy/issues/34)
- [#35 Observability Dashboard](https://github.com/nickpclarke/AgentArmy/issues/35)
- [#36 Spoke-Specific Prompt Adaptation](https://github.com/nickpclarke/AgentArmy/issues/36)

---

## Release Train 4: Learning & Intelligence

**Epic:** #37  
**Duration:** Oct 4 – Nov 15 (6 weeks)  
**Team:** 2.0 FTE  
**Status:** Waiting for RT3 completion

### Features

| # | Title | Size | Est. | Status |
|---|---|---|---|---|
| 38 | Agent Lesson-Learned KB (incident log) | M | 5 | Backlog |
| 39 | Request Tracing & Decision Audit Log | M | 5 | Backlog |
| 40 | Feedback Integration (PR → routing) | M | 5 | Backlog |
| 41 | Competency Evolution Tracking | M | 5 | Backlog |

### Critical Success Factors

- KB has ≥50 incident records
- Anti-patterns library ≥15 patterns
- Agent competency trends show improvement ≥3 task types
- Feedback loop closed (comments → updates)
- All 4 features merged

### Dependencies (Block Chart)

```
RT3 Completion
  ├─ #38: KB (depends on #28 Learning Loop Runtime)
  ├─ #39: Tracing (depends on #22 Telemetry, #21 Context Graph)
  ├─ #40: Feedback (depends on #39 Tracing)
  └─ #41: Competency (depends on #26 SLIs, #38 KB)
```

### Direct Links

- [#37 Epic](https://github.com/nickpclarke/AgentArmy/issues/37)
- [#38 Agent KB](https://github.com/nickpclarke/AgentArmy/issues/38)
- [#39 Request Tracing](https://github.com/nickpclarke/AgentArmy/issues/39)
- [#40 Feedback Integration](https://github.com/nickpclarke/AgentArmy/issues/40)
- [#41 Competency Evolution](https://github.com/nickpclarke/AgentArmy/issues/41)

---

## Cross-RT Dependencies (Full Graph)

```
RT1 (Foundation)
  ├─ #18 Agent Specs
  ├─ #19 Routing Tree ────┐
  ├─ #20 Hooks ────┐      │
  ├─ #21 Graph     │      │
  ├─ #22 Telemetry ├─────┬┼──────────┐
  └─ #23 Prompts   │      │          │
                   │      │          │
                   v      v          v
RT2 (Operations)
  ├─ #25 Choreography  (depends on #19)
  ├─ #26 Eval Gates    (depends on #22)
  ├─ #27 Skills        (depends on #18)
  ├─ #28 Learning Loop (depends on #22, #20) ← CRITICAL
  ├─ #29 Artifacts     (depends on #20, #21)
  └─ #30 Cost          (depends on #22)
       │   │    │       │        │       │
       │   │    │       │        │       └──────┐
       v   v    v       v        v              v
RT3 (Spokes)
  ├─ #32 Onboarding   (depends on #19, #29)
  ├─ #33 Capacity     (depends on #30)
  ├─ #34 Manifest     (depends on #29)
  ├─ #35 Dashboard    (depends on #22, #26)
  └─ #36 Prompts      (depends on #23)
       │   │     │    │    │
       └───┼─────┼────┼────┘
           v     v    v
RT4 (Learning)
  ├─ #38 KB           (depends on #28)
  ├─ #39 Tracing      (depends on #22, #21)
  ├─ #40 Feedback     (depends on #39)
  └─ #41 Competency   (depends on #26, #38)
```

---

## Quarterly Milestone Breakdown

### Q2 (Jun–Aug): RT1 + RT2 Ramp-Up
- **Jun 1–12:** RT1 Sprint 1 (Agent Specs, Routing Tree kickoff)
- **Jun 12–26:** RT1 Sprint 2 (Hooks, Graph, continued routing)
- **Jun 26–Jul 10:** RT1 Sprint 3 (Telemetry, Prompt Library, wrap)
- **Jul 10–24:** RT2 Sprint 1 (RT1 wrap, RT2 kickoff: Choreography, Gates)
- **Jul 24–Aug 7:** RT2 Sprint 2 (Skills, Learning Loop, Artifacts)
- **Aug 7–21:** RT2 Sprint 3 (Cost Visibility, wrap)

### Q3 (Aug–Oct): RT2 Completion + RT3 Ramp-Up
- **Aug 21–Sep 4:** RT3 Sprint 1 (RT2 wrap, RT3 kickoff: Onboarding, Manifest)
- **Sep 4–18:** RT3 Sprint 2 (Capacity Model, Dashboard)
- **Sep 18–Oct 2:** RT3 Sprint 3 (Prompt Adaptation, real spoke instantiation)

### Q4 (Oct–Nov): RT3 Wrap + RT4 Execution
- **Oct 2–16:** RT4 Sprint 1 (RT3 wrap, RT4 kickoff: KB, Tracing)
- **Oct 16–30:** RT4 Sprint 2 (Feedback Integration, Competency)
- **Oct 30–Nov 15:** RT4 Sprint 3 (wrap, learning synthesis)

---

## Status Board

| Release Train | Current Status | Blocker | Next Step | ETA |
|---|---|---|---|---|
| **RT1** | Planning | None | Kick off Jun 1 | On track |
| **RT2** | Waiting | RT1 completion | Start Jul 12 | On track |
| **RT3** | Waiting | RT2 completion | Start Aug 23 | On track |
| **RT4** | Waiting | RT3 completion | Start Oct 4 | On track |

---

## Board Population Status

- [ ] GitHub Projects TOKEN configured
- [ ] All 25 issues added to project board
- [ ] Custom fields set (Type, PI, Size, Estimate, Parent)
- [ ] Iterations created (Sprint 1–12)
- [ ] Start/Target dates set

**See:** `/planning/backlog/board-population-checklist.md` for detailed setup steps.

---

**Last Updated:** 2026-05-23  
**Board Status:** All 25 issues created, awaiting board setup  
**Next Review:** When board TOKEN is configured  

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
