# Release Train Master Index

Strategic index of Release Trains RT1–RT4 for the AgentArmy template platform evolution. 6-month roadmap (Jun 2026 – Nov 2026).

> **The [GitHub Projects board](https://github.com/users/nickpclarke/projects/1) holds live status, fields, and per-issue details — not this page.** This page holds the durable strategy: themes, success factors, cross-RT dependencies, and the milestone calendar. For the issue index see [backlog/BACKLOG_ISSUES_INDEX.md](../backlog/BACKLOG_ISSUES_INDEX.md); for the strategic rationale see [roadmap/PLATFORM_ROADMAP.md](../roadmap/PLATFORM_ROADMAP.md).

## Summary

| RT | Name | Theme | Duration | Team | Epic / Features | PI |
|---|---|---|---|---|---|---|
| **RT1** | Foundation & Routing | Make capabilities explicit; routing deterministic | Jun 1 – Jul 12 | 3.0 FTE | [#17](https://github.com/nickpclarke/AgentArmy/issues/17) / #18–23 | PI-1 |
| **RT2** | Operations & Quality | Formalize workflows; close the learning loop | Jul 12 – Aug 23 | 3.5 FTE | [#24](https://github.com/nickpclarke/AgentArmy/issues/24) / #25–30 | PI-2 |
| **RT3** | Spoke Readiness | Spoke teams self-serve; context travels | Aug 23 – Oct 4 | 2.5 FTE | [#31](https://github.com/nickpclarke/AgentArmy/issues/31) / #32–36 | PI-2 |
| **RT4** | Learning & Intelligence | Accumulate & share lessons; iterate routing | Oct 4 – Nov 15 | 2.0 FTE | [#37](https://github.com/nickpclarke/AgentArmy/issues/37) / #38–41 | PI-3 |

**Total:** 25 issues across 4 epics · ~11 FTE-weeks · 24 weeks (6 months).

---

## Velocity & Sprint Calibration

> **Living baseline** — updated after each session. Future sessions should compare against these numbers and annotate divergence.

### Session 1 Actuals (2026-05-23)

| Metric | Value |
|---|---|
| Session duration | ~3 hours |
| Parallel agents | 4 |
| Features completed | 4 Size:M (draft PRs open) |
| Throughput | **4 Size:M features / session** |

**Issues completed in Session 1:**
- #18 Agent Spec Template + Capability Matrix → PR #57
- #19 Executable Routing Decision Tree → PR #58
- #20 Claude Code Hook System → PR #55
- #44 Docs: token setup + agent onboarding path → PR #56 (pre-kickoff)

**Session 1 character:** Foundation/template/YAML-heavy work. Agent spec schemas, routing policy YAML (1275 lines), hook shell scripts, and docs additions are structurally lightweight compared to runtime choreography code. This inflated throughput vs. RT2+.

### Velocity Units

These agents work in **sessions**, not calendar weeks. The relevant planning unit is:

> **Features per session** (not story points per week)

A session = one parallel-agent invocation, typically 2–4 hours wall-clock time.

### Projected Session Count by Release Train

| RT | Features | Session estimate | Compression factor vs. Session 1 | Notes |
|---|---|---|---|---|
| **RT1** | 6 features (#18–23) | **2 sessions** | 1× | Session 1 = done (#18, #19, #20, #44); Session 2 = #21, #22, #23 |
| **RT2** | 6 features (#25–30) | **2–3 sessions** | 2–3× slower | Real choreography code, saga state machines, learning loop runtime |
| **RT3** | 5 features (#32–36) | **2 sessions** | 2–3× slower | Spoke init automation, dashboards, prompt adaptation |
| **RT4** | 4 features (#38–41) | **1–2 sessions** | 2× slower | KB, tracing, feedback, competency — smaller feature set |
| **Total** | 21 remaining features | **7–9 sessions** | — | Full roadmap estimate from Session 1 baseline |

### Caveats & Calibration Notes

- **RT2+ features are implementation-heavy.** Choreography patterns, learning loop runtime, and cost-visibility integrations involve real executable code (not YAML policy or shell scripts). Expect 2–3 features/session, not 4.
- **Parallelism ceiling.** Session 1 ran 4 agents in true parallel on independent features. RT2+ features have tighter dependencies (see Cross-RT Dependency Graph below) — some will serialize, reducing throughput.
- **Revision rounds.** Draft PRs from Session 1 will require review and revision passes. Count those as fractional sessions if significant rework is needed.
- **This baseline replaces FTE-week estimates for agent-driven work.** Calendar durations in the Milestone Calendar remain as reference anchors for stakeholder communication, but session counts are the operational planning unit.

---

## Critical Success Factors

**RT1 — Foundation & Routing**
- Routing determinism > 90%; telemetry > 500 delegations; context injection > 95% success; hook system stable (< 5ms overhead, zero timeouts).

**RT2 — Operations & Quality**
- Learning loop closes (failures → KB entry); rework reduced ≥ 20%; ≥ 10 incident records in KB; multi-rendering adopted for all strategic artifacts.

**RT3 — Spoke Readiness**
- ≥ 1 real spoke instantiated; spoke init < 2 hours (automated); full context transferred via `manifest.json`.

**RT4 — Learning & Intelligence**
- KB ≥ 50 incident records; anti-patterns library ≥ 15 patterns; competency trends improving on ≥ 3 task types; feedback loop closed (comments → updates).

---

## Cross-RT Dependency Graph

This is the durable planning artifact the board doesn't capture well — the keystone chain that drives cut order.

```
RT1 (Foundation)
  ├─ #18 Agent Specs ───────────┐
  ├─ #19 Routing Tree ──────────┼───────────────┐   ← keystone
  ├─ #20 Hooks ─────────┐       │               │
  ├─ #21 Context Graph  │       │               │
  ├─ #22 Telemetry ─────┼───────┼───────┐       │
  └─ #23 Prompt Library │       │       │       │
                        v       v       v       v
RT2 (Operations)
  ├─ #25 Choreography      (← #19)
  ├─ #26 Eval Gates        (← #22)
  ├─ #27 Skill Scaffolding (← #18)
  ├─ #28 Learning Loop     (← #22, #20)   ← critical
  ├─ #29 Artifact Lifecycle(← #20, #21)
  └─ #30 Cost Visibility   (← #22)
                        │       │       │
                        v       v       v
RT3 (Spokes)
  ├─ #32 Onboarding   (← #19, #29)
  ├─ #33 Capacity     (← #30)
  ├─ #34 Manifest     (← #29)
  ├─ #35 Dashboard    (← #22, #26)
  └─ #36 Prompt Adapt (← #23)
                        │       │
                        v       v
RT4 (Learning)
  ├─ #38 KB           (← #28)
  ├─ #39 Tracing      (← #22, #21)
  ├─ #40 Feedback     (← #39)
  └─ #41 Competency   (← #26, #38)
```

**Keystone:** #19 Executable Routing Decision Tree unblocks choreography, spoke onboarding, and the learning loop. **Critical:** #28 Learning Loop Runtime is the durable moat (see [PLATFORM_ROADMAP.md](../roadmap/PLATFORM_ROADMAP.md)).

---

## Milestone Calendar

> **Two views:** Calendar dates (original estimates, kept for stakeholder reference) and session-based milestones (the operational planning unit for agent-driven work). Use the session column to plan the next session; use the calendar column for reporting to humans.

### Q2 (Jun–Aug): RT1 + RT2 ramp-up

| Calendar window (~Jun–Aug 2026) | Session | Issues | Status |
|---|---|---|---|
| Jun 1–12: RT1 Sprint 1 — Agent Specs, Routing Tree kickoff | **Session 1** | #18, #19, #20, #44 | **DONE** — draft PRs #55, #56, #57, #58 open |
| Jun 12–26: RT1 Sprint 2 — Hooks, Context Graph, routing cont. | **Session 2** | #21, #22, #23 | Not started |
| Jun 26–Jul 10: RT1 Sprint 3 — Telemetry, Prompt Library, wrap | _(absorbed into Session 2 or earlier)_ | — | Dependent on Session 2 scope |
| Jul 10–24: RT2 Sprint 1 — Choreography, Eval Gates | **Session 3** | #25, #26 | Not started |
| Jul 24–Aug 7: RT2 Sprint 2 — Skills, Learning Loop, Artifacts | **Session 4** | #27, #28, #29 | Not started |
| Aug 7–21: RT2 Sprint 3 — Cost Visibility, wrap | _(Session 4 or Session 5 if slippage)_ | #30 | Not started |

### Q3 (Aug–Oct): RT2 completion + RT3 ramp-up

| Calendar window (~Aug–Oct 2026) | Session | Issues | Status |
|---|---|---|---|
| Aug 21–Sep 4: RT3 Sprint 1 — Onboarding, Manifest | **Session 5** | #32, #34 | Not started |
| Sep 4–18: RT3 Sprint 2 — Capacity Model, Dashboard | **Session 5 (cont.) or Session 6** | #33, #35 | Not started |
| Sep 18–Oct 2: RT3 Sprint 3 — Prompt Adaptation, first real spoke | _(Session 5–6 tail)_ | #36 | Not started |

### Q4 (Oct–Nov): RT3 wrap + RT4 execution

| Calendar window (~Oct–Nov 2026) | Session | Issues | Status |
|---|---|---|---|
| Oct 2–16: RT4 Sprint 1 — KB, Tracing | **Session 6** | #38, #39 | Not started |
| Oct 16–30: RT4 Sprint 2 — Feedback Integration, Competency | **Session 7** | #40, #41 | Not started |
| Oct 30–Nov 15: RT4 Sprint 3 — wrap, learning synthesis | _(Session 7 tail or Session 8 if needed)_ | — | Not started |

### Session Summary (operational view)

| Session | Target issues | RT | Expected throughput | Notes |
|---|---|---|---|---|
| **Session 1** ✅ | #18, #19, #20, #44 | RT1 | 4 features | **DONE** 2026-05-23 |
| **Session 2** | #21, #22, #23 | RT1 | 3 features | Remaining RT1; foundation-class work |
| **Session 3** | #25, #26 | RT2 | 2 features | Choreography + Eval Gates; implementation-heavy |
| **Session 4** | #27, #28, #29 | RT2 | 2–3 features | Skills + Learning Loop + Artifacts |
| **Session 5** | #30, #32, #33, #34 | RT2/RT3 | 2–3 features | Cost Visibility wrap + RT3 ramp |
| **Session 6** | #35, #36, #38, #39 | RT3/RT4 | 2–3 features | Dashboard + Prompt Adapt + RT4 start |
| **Session 7** | #40, #41 | RT4 | 2 features | Feedback + Competency; final sprint |
| **Session 8** _(buffer)_ | Spillover / revision passes | — | — | Hold in reserve; use if RT2+ slips |

> Sprints map to the board's `Iteration` field. They aren't created yet — add them at PI Planning per the [board-population-checklist](../backlog/board-population-checklist.md). Calendar sprint dates are the original human-team estimates and remain valid for milestone reporting; session numbers are the agent-army execution cadence.

---

**Sequencing:** RT1 → RT2 → RT3 → RT4, strict by the dependency chain above. Track live progress, blockers, and status on the [board](https://github.com/users/nickpclarke/projects/1).
