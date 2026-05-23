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

### Q2 (Jun–Aug): RT1 + RT2 ramp-up
- **Jun 1–12:** RT1 Sprint 1 — Agent Specs, Routing Tree kickoff
- **Jun 12–26:** RT1 Sprint 2 — Hooks, Context Graph, routing cont.
- **Jun 26–Jul 10:** RT1 Sprint 3 — Telemetry, Prompt Library, wrap
- **Jul 10–24:** RT2 Sprint 1 — Choreography, Eval Gates
- **Jul 24–Aug 7:** RT2 Sprint 2 — Skills, Learning Loop, Artifacts
- **Aug 7–21:** RT2 Sprint 3 — Cost Visibility, wrap

### Q3 (Aug–Oct): RT2 completion + RT3 ramp-up
- **Aug 21–Sep 4:** RT3 Sprint 1 — Onboarding, Manifest
- **Sep 4–18:** RT3 Sprint 2 — Capacity Model, Dashboard
- **Sep 18–Oct 2:** RT3 Sprint 3 — Prompt Adaptation, first real spoke

### Q4 (Oct–Nov): RT3 wrap + RT4 execution
- **Oct 2–16:** RT4 Sprint 1 — KB, Tracing
- **Oct 16–30:** RT4 Sprint 2 — Feedback Integration, Competency
- **Oct 30–Nov 15:** RT4 Sprint 3 — wrap, learning synthesis

> Sprints map to the board's `Iteration` field. They aren't created yet — add them at PI Planning per the [board-population-checklist](../backlog/board-population-checklist.md).

---

**Sequencing:** RT1 → RT2 → RT3 → RT4, strict by the dependency chain above. Track live progress, blockers, and status on the [board](https://github.com/users/nickpclarke/projects/1).
