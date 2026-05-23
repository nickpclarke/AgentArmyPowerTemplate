# AgentArmy Enhanced Backlog: GitHub Issues Index
## All 25 Issues Ready for GitHub Projects Board Population

**Last Updated:** 2026-05-23  
**Total Issues:** 25 (4 Epics + 21 Features)  
**Status:** Created in GitHub, waiting for board population

---

## How to Use This File

When you have GitHub Projects board access (TOKEN configured):

1. Open the project board: https://github.com/nickpclarke/AgentArmy/projects/1
2. For each issue below, add to board and set fields:
   - **Type:** (from Type column)
   - **PI:** PI-1 (for RT1), PI-2 (for RT2), etc.
   - **Size:** (T-shirt estimate)
   - **Estimate:** (Story points, Fibonacci)
   - **Parent Issue:** (Epic number)
   - **Priority:** P1 for epics, P1-P2 for features

3. Set start/target dates:
   - RT1: Start Jun 1, Target Jul 12
   - RT2: Start Jul 12, Target Aug 23
   - RT3: Start Aug 23, Target Oct 4
   - RT4: Start Oct 4, Target Nov 15

---

## Release Train 1: Foundation & Routing
**Epic:** #17  
**Duration:** Jun 1 – Jul 12 (6 weeks)  
**Team:** 3.0 FTE

| # | Title | Type | Size | Est. | Parent | Routing | Status |
|---|---|---|---|---|---|---|---|
| **17** | **RT1-EPIC-001: Foundation & Routing** | Epic | L | 34 | — | — | ✓ Created |
| 18 | RT1-FEAT-001: Agent Spec Template + Capability Matrix | Feature | M | 5 | 17 | agent-distinctiveness-advocate, documentation-engineer | ✓ Created |
| 19 | RT1-FEAT-002: Executable Routing Decision Tree (YAML) | Feature | L | 8 | 17 | architect-reviewer, tooling-engineer | ✓ Created |
| 20 | RT1-FEAT-003: Claude Code Hook System (SessionStart/Stop/UserPromptSubmit/PreToolUse/PostToolUse) | Feature | L | 13 | 17 | devops-engineer, tooling-engineer | ✓ Created |
| 21 | RT1-FEAT-004: Project Context Graph Injection | Feature | L | 8 | 17 | architect-reviewer, observability-engineer | ✓ Created |
| 22 | RT1-FEAT-005: Telemetry Instrumentation (OTel spans) | Feature | M | 5 | 17 | observability-engineer | ✓ Created |
| 23 | RT1-FEAT-006: Few-Shot Prompt Library (Phase 1) | Feature | M | 3 | 17 | prompt-engineer | ✓ Created |

### RT1 Dependencies
```
18 (Agent Specs) → 19 (Routing Policy)
19 (Routing Policy) → 20 (Hooks), 21 (Context Graph)
20 (Hooks) → 21, 22 (Telemetry)
18, 19 → 23 (Prompt Library)
```

**Completion Criteria:**
- [ ] All 6 features merged
- [ ] Routing determinism >90%
- [ ] Telemetry >500 delegations
- [ ] Context injection >95% success
- [ ] Hook system stable (zero timeouts, <5ms overhead)

---

## Release Train 2: Operations & Quality
**Epic:** #24  
**Duration:** Jul 12 – Aug 23 (6 weeks)  
**Team:** 3.5 FTE

| # | Title | Type | Size | Est. | Parent | Routing | Status |
|---|---|---|---|---|---|---|---|
| **24** | **RT2-EPIC-002: Operations & Quality** | Epic | L | 41 | — | — | ✓ Created |
| 25 | RT2-FEAT-001: Multi-Agent Choreography (Saga patterns, compensation, state machines) | Feature | L | 8 | 24 | workflow-orchestrator, architect-reviewer | ✓ Created |
| 26 | RT2-FEAT-002: Agent Evaluation Gates (DoD rubrics, SLI/SLO framework) | Feature | M | 5 | 24 | observability-engineer, qa-expert | ✓ Created |
| 27 | RT2-FEAT-003: Skill Scaffolding & Composition (Recipes, versioning) | Feature | M | 5 | 24 | tooling-engineer, architect-reviewer | ✓ Created |
| 28 | RT2-FEAT-004: Learning Loop Runtime (error-coordinator + knowledge-synthesizer) | Feature | L | 8 | 24 | knowledge-synthesizer, observability-engineer | ✓ Created |
| 29 | RT2-FEAT-005: Artifact Lifecycle & Multi-Rendering Templates | Feature | M | 5 | 24 | documentation-engineer, devops-engineer | ✓ Created |
| 30 | RT2-FEAT-006: Cost Visibility & Provider Abstraction (Helicone integration) | Feature | M | 5 | 24 | finops-engineer | ✓ Created |

### RT2 Dependencies
```
25 (Choreography) ← 19 (Routing Policy)
26 (Evaluation Gates) ← 22 (Telemetry)
27 (Skill Scaffolding) ← 18 (Agent Specs)
28 (Learning Loop) ← 22 (Telemetry), 20 (Hooks)
29 (Artifact Lifecycle) ← 20 (Hooks), 21 (Context Graph)
30 (Cost Visibility) ← 22 (Telemetry)
```

**Completion Criteria:**
- [ ] All 6 features merged
- [ ] Learning loop closes: failures → KB entry
- [ ] Rework reduced ≥20%
- [ ] ≥10 incident records in KB
- [ ] Multi-rendering adopted for all strategic artifacts

---

## Release Train 3: Spoke Readiness
**Epic:** #31  
**Duration:** Aug 23 – Oct 4 (6 weeks)  
**Team:** 2.5 FTE

| # | Title | Type | Size | Est. | Parent | Routing | Status |
|---|---|---|---|---|---|---|---|
| **31** | **RT3-EPIC-003: Spoke Readiness** | Epic | L | 25 | — | — | ✓ Created |
| 32 | RT3-FEAT-001: Hub→Spoke Onboarding Playbook | Feature | M | 5 | 31 | platform-engineer, devops-engineer | ✓ Created |
| 33 | RT3-FEAT-002: Cost & Capacity Model (unit economics, showback) | Feature | M | 5 | 31 | finops-engineer | ✓ Created |
| 34 | RT3-FEAT-003: Artifact Manifest Export (spoke initialization) | Feature | S | 2 | 31 | documentation-engineer, devops-engineer | ✓ Created |
| 35 | RT3-FEAT-004: Observability Dashboard (MTTR, cost, success rate) | Feature | M | 5 | 31 | observability-engineer | ✓ Created |
| 36 | RT3-FEAT-005: Spoke-Specific Prompt Adaptation (greenfield vs. legacy) | Feature | S | 3 | 31 | prompt-engineer | ✓ Created |

### RT3 Dependencies
```
32 (Onboarding) ← 19 (Routing), 29 (Manifest)
33 (Capacity Model) ← 30 (Cost Tracking)
34 (Manifest Export) ← 29 (Artifact Lifecycle)
35 (Dashboard) ← 22 (Telemetry), 26 (SLIs)
36 (Prompt Adapt) ← 23 (Prompt Library Phase 1)
```

**Completion Criteria:**
- [ ] All 5 features merged
- [ ] ≥1 real spoke instantiated
- [ ] Spoke init <2 hours (automated)
- [ ] Full context transferred via manifest.json

---

## Release Train 4: Learning & Intelligence
**Epic:** #37  
**Duration:** Oct 4 – Nov 15 (6 weeks)  
**Team:** 2.0 FTE

| # | Title | Type | Size | Est. | Parent | Routing | Status |
|---|---|---|---|---|---|---|---|
| **37** | **RT4-EPIC-004: Learning & Intelligence** | Epic | L | 20 | — | — | ✓ Created |
| 38 | RT4-FEAT-001: Agent Lesson-Learned KB (incident log, anti-patterns library) | Feature | M | 5 | 37 | knowledge-synthesizer | ✓ Created |
| 39 | RT4-FEAT-002: Request Tracing & Decision Audit Log (end-to-end visibility) | Feature | M | 5 | 37 | observability-engineer | ✓ Created |
| 40 | RT4-FEAT-003: Feedback Integration (PR comments → routing/prompt refinement) | Feature | M | 5 | 37 | prompt-engineer, architect-reviewer | ✓ Created |
| 41 | RT4-FEAT-004: Competency Evolution Tracking (agent performance trends) | Feature | M | 5 | 37 | observability-engineer, knowledge-synthesizer | ✓ Created |

### RT4 Dependencies
```
38 (KB) ← 28 (Learning Loop Runtime)
39 (Tracing) ← 22 (Telemetry), 21 (Context Graph)
40 (Feedback Integration) ← 39 (Tracing)
41 (Competency) ← 26 (SLIs), 38 (KB)
```

**Completion Criteria:**
- [ ] All 4 features merged
- [ ] KB has ≥50 incident records
- [ ] Anti-patterns library ≥15 patterns
- [ ] Agent competency trends show improvement ≥3 task types
- [ ] Feedback loop closed (comments → updates)

---

## Batch Board Population Script

Once you have TOKEN access, run this to add all issues:

```bash
#!/bin/bash
# Add all 25 issues to GitHub Projects board

PROJECT_ID="1"  # your project ID
OWNER="nickpclarke"
REPO="agentarmy"

# RT1 Issues
for issue in 17 18 19 20 21 22 23; do
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

# RT2 Issues
for issue in 24 25 26 27 28 29 30; do
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

# RT3 Issues
for issue in 31 32 33 34 35 36; do
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

# RT4 Issues
for issue in 37 38 39 40 41; do
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

echo "All 25 issues added to project board!"
```

---

## Field Mapping Reference

When adding to board, set these fields per release train:

### Common Fields (All Issues)
| Field | Value |
|---|---|
| Status | Backlog |
| Priority | P1 (Epics) or P1-P2 (Features) |
| Type | Epic or Feature |

### RT1 Fields
| Field | Value |
|---|---|
| PI | PI-1 |
| Iteration | Sprint 1 (Week 1-2), Sprint 2 (Week 3-4), Sprint 3 (Week 5-6) |
| Start Date | 2026-06-01 |
| Target Date | 2026-07-12 |
| Size | (T-shirt: S/M/L) |

### RT2 Fields
| Field | Value |
|---|---|
| PI | PI-2 |
| Iteration | Sprint 4, 5, 6 |
| Start Date | 2026-07-12 |
| Target Date | 2026-08-23 |
| Size | (T-shirt: S/M/L) |

### RT3 Fields
| Field | Value |
|---|---|
| PI | PI-2 (spans RT2-RT3) |
| Iteration | Sprint 7, 8, 9 |
| Start Date | 2026-08-23 |
| Target Date | 2026-10-04 |
| Size | (T-shirt: S/M/L) |

### RT4 Fields
| Field | Value |
|---|---|
| PI | PI-3 |
| Iteration | Sprint 10, 11, 12 |
| Start Date | 2026-10-04 |
| Target Date | 2026-11-15 |
| Size | (T-shirt: S/M/L) |

---

## GitHub Issue Direct Links

### RT1
- [#17 RT1-EPIC-001](https://github.com/nickpclarke/AgentArmy/issues/17)
- [#18 RT1-FEAT-001](https://github.com/nickpclarke/AgentArmy/issues/18)
- [#19 RT1-FEAT-002](https://github.com/nickpclarke/AgentArmy/issues/19)
- [#20 RT1-FEAT-003](https://github.com/nickpclarke/AgentArmy/issues/20)
- [#21 RT1-FEAT-004](https://github.com/nickpclarke/AgentArmy/issues/21)
- [#22 RT1-FEAT-005](https://github.com/nickpclarke/AgentArmy/issues/22)
- [#23 RT1-FEAT-006](https://github.com/nickpclarke/AgentArmy/issues/23)

### RT2
- [#24 RT2-EPIC-002](https://github.com/nickpclarke/AgentArmy/issues/24)
- [#25 RT2-FEAT-001](https://github.com/nickpclarke/AgentArmy/issues/25)
- [#26 RT2-FEAT-002](https://github.com/nickpclarke/AgentArmy/issues/26)
- [#27 RT2-FEAT-003](https://github.com/nickpclarke/AgentArmy/issues/27)
- [#28 RT2-FEAT-004](https://github.com/nickpclarke/AgentArmy/issues/28)
- [#29 RT2-FEAT-005](https://github.com/nickpclarke/AgentArmy/issues/29)
- [#30 RT2-FEAT-006](https://github.com/nickpclarke/AgentArmy/issues/30)

### RT3
- [#31 RT3-EPIC-003](https://github.com/nickpclarke/AgentArmy/issues/31)
- [#32 RT3-FEAT-001](https://github.com/nickpclarke/AgentArmy/issues/32)
- [#33 RT3-FEAT-002](https://github.com/nickpclarke/AgentArmy/issues/33)
- [#34 RT3-FEAT-003](https://github.com/nickpclarke/AgentArmy/issues/34)
- [#35 RT3-FEAT-004](https://github.com/nickpclarke/AgentArmy/issues/35)
- [#36 RT3-FEAT-005](https://github.com/nickpclarke/AgentArmy/issues/36)

### RT4
- [#37 RT4-EPIC-004](https://github.com/nickpclarke/AgentArmy/issues/37)
- [#38 RT4-FEAT-001](https://github.com/nickpclarke/AgentArmy/issues/38)
- [#39 RT4-FEAT-002](https://github.com/nickpclarke/AgentArmy/issues/39)
- [#40 RT4-FEAT-003](https://github.com/nickpclarke/AgentArmy/issues/40)
- [#41 RT4-FEAT-004](https://github.com/nickpclarke/AgentArmy/issues/41)

---

## Summary Stats

| Metric | Value |
|---|---|
| Total Issues | 25 |
| Epics | 4 |
| Features | 21 |
| Total Story Points | 120 |
| Total Team Effort | ~11 FTE-weeks (2.75 FTE avg × 4 RTs) |
| Timeline | 24 weeks (6 months) |
| Start Date | 2026-06-01 |
| End Date | 2026-11-15 |

---

**Ready to populate board once TOKEN is configured!**

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK