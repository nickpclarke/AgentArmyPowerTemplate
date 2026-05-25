# Release Train Master Index

Strategic index of Release Trains RT1–RT8 for the AgentArmy template platform and spoke implementations.
Rolling roadmap across ~15 agent sessions (hub RT1–RT4) + ~11 spoke sessions (RT5–RT8).

> **Planning unit:** This army plans in **agent sessions** — one parallel-agent invocation — not human calendar time. All durations are expressed in sessions. A PI (Program Increment) spans approximately 5 sessions.

> **The [GitHub Projects board](https://github.com/users/nickpclarke/projects/1) holds live status, fields, and per-issue details — not this page.** This page holds the durable strategy: themes, success factors, cross-RT dependencies, and the milestone calendar. For the issue index see [backlog/BACKLOG_ISSUES_INDEX.md](../backlog/BACKLOG_ISSUES_INDEX.md); for the strategic rationale see [roadmap/PLATFORM_ROADMAP.md](../roadmap/PLATFORM_ROADMAP.md).

## Summary

### Hub template trains (RT1–RT4)

These trains deliver artifacts to the AgentArmy hub repo itself — agent specs, routing policy, CI/CD
workflows, spoke-init tooling, and the learning loop runtime. They do not ship running application code.

| RT | Name | Theme | Session range | Epic / Features | PI |
|---|---|---|---|---|---|
| **RT1** | Foundation & Routing | Make capabilities explicit; routing deterministic | Sessions 1–2 | [#17](https://github.com/nickpclarke/AgentArmy/issues/17) / #18–23 | PI-1 |
| **RT2** | Operations & Quality | Formalize workflows; close the learning loop | Sessions 3–5 | [#24](https://github.com/nickpclarke/AgentArmy/issues/24) / #25–30 | PI-2 |
| **RT3** | Spoke Readiness | Spoke teams self-serve; context travels | Sessions 5–6 | [#31](https://github.com/nickpclarke/AgentArmy/issues/31) / #32–36 | PI-2 |
| **RT4** | Learning & Intelligence | Accumulate & share lessons; iterate routing | Sessions 6–7 | [#37](https://github.com/nickpclarke/AgentArmy/issues/37) / #38–41 | PI-3 |

**Hub total:** 25 issues across 4 epics · ~7–9 sessions · PI-1 through PI-3.

### Spoke-implementation trains (RT5–RT8)

These trains deliver running software inside the spoke repos (`middle-core`, `backend-core`,
`frontend-core`). They are independent of RT1–RT4 template work and are scheduled at PI planning
based on spoke-repo readiness, not hub template delivery.

| RT | Name | Theme | Spoke repo(s) | Epic / top-level items | PI |
|---|---|---|---|---|---|
| **RT5** | Ontology-Grade Persistence | Immutable, content-addressed, bitemporal object pinning; backend-neutral seam | middle-core | PIN-E / PIN-F1–F4, EN1–EN2, S1–S2 | PI-3 (candidate) |
| **RT6** | Universal Data Adapter | Provider-neutral query surface over ArcadeDB, Postgres, object storage; RBAC, pagination, caching | backend-core | UDA-E (#13) / Phase 1 shipped, Phase 2 #33–#44, Phase 3 #45–#50 | PI-2/PI-3 |
| **RT7** | Middle-Core Runtime | Administrable, instrumented, ArcadeDB-backed C# platform | middle-core | MCR-E (#7) / MCR-F1–F5, EN1–EN2, S1–S2 | PI-3 (candidate) |
| **RT8** | Generative Platform Maturity | Agent runtime + generative UI: streaming, memory, cockpit, observability, ACA deploy | middle-core + frontend-core | GPM-E1 (MC #32–#39) + GPM-E2 (FE #32–#37) | PI-3 (candidate) |

**Spoke total:** ~35 items across 4 epics in 3 spoke repos · ~11 sessions · RT6 Phase 1 shipped · RT5/RT7/RT8 planned.

See the per-RT docs for full Epic → Feature → Enabler decomposition and acceptance criteria:
- [RT5-ontology-grade-persistence.md](RT5-ontology-grade-persistence.md)
- [RT6-universal-data-adapter.md](RT6-universal-data-adapter.md)
- [RT7-middle-core-runtime.md](RT7-middle-core-runtime.md)
- [RT8-generative-platform-maturity.md](RT8-generative-platform-maturity.md)

---

## Velocity & Sprint Calibration

> **Living baseline** — updated after each session. Future sessions should compare against these numbers and annotate divergence.

### Session 1 Actuals (2026-05-23)

| Metric | Value |
|---|---|
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

A session = one parallel-agent invocation. No calendar clock applies; throughput is measured in features delivered per session.

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
- **This baseline replaces all FTE-week and calendar estimates.** Session counts are the sole operational planning unit for this army. No calendar anchors are maintained.

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

### Hub train chain (RT1–RT4)

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

### Spoke train chain (RT5–RT8)

The spoke trains are independent of RT1–RT4 but form their own dependency chain:

```
RT6 (UDA — backend-core)
  ├─ Phase 1 ── SHIPPED (PR #31)
  ├─ Phase 2 ── in-flight (#33–#44)
  └─ Phase 3
       ├─ UDA-F3 Pagination (#47) ─────────────────────────────────┐  ← P0; unblocks RT8 GPM-F3
       ├─ UDA-F4 RBAC (#48)       (← UDA-F3)
       ├─ UDA-F5 Caching (#49)    (← UDA-F3, UDA-F4)
       ├─ UDA-F1 Postgres (#45)   (← Phase 2 stable)
       └─ UDA-F2 Object store (#46) (← Phase 2 stable)

RT5 (Ontology Pinning — middle-core)
  ├─ PIN-F1 Core primitives
  ├─ PIN-F2 Reification + PinnedElement ──────────────────────────┐
  ├─ PIN-F3 Provider-neutral store ──────────────────────────────┐ │
  └─ PIN-F4 ArcadeDB adapter (← PIN-F3, PIN-S1) ────────────────┼─┼──┐
                                                                  │ │  │
RT7 (Middle-Core C# Runtime — middle-core)                        │ │  │
  ├─ MCR-EN1 DI scaffolding                                       │ │  │
  ├─ MCR-F1 ArcadeDB persistence (← RT5 PIN-F4) ─────────────────┼─┼──┼──┐
  ├─ MCR-F2 Model admin API (← MCR-EN1)                          │ │  │  │
  ├─ MCR-F3 OTel + Prometheus (← MCR-EN1)                        │ │  │  │
  ├─ MCR-F4 C# data-platform objects (← MCR-EN1) ────────────────┼─┼──┼──┼──┐
  ├─ MCR-F5 Version ledger (← MCR-F4, MCR-F2)                    │ │  │  │  │
  └─ MCR-EN2 Docker + ACA manifest (← MCR-EN1, MCR-F3)           │ │  │  │  │
                                                                   │ │  │  │  │
RT8 (Generative Platform — middle-core + frontend-core)            │ │  │  │  │
  ├─ GPM-F1 MC streaming (← LangGraph baseline) ← KEYSTONE        │ │  │  │  │
  ├─ GPM-F2 MC memory/thread (← GPM-F1)                           │ │  │  │  │
  ├─ GPM-F3 MC analytics tools (← GPM-F1, UDA-F3) ───────────────┘ │  │  │  │
  ├─ GPM-F4 MC contract test (← RT7 MCR-F4) ─────────────────────────  │  │  └──┘
  ├─ GPM-F5 MC OTel (← GPM-F1)                                         │  │
  ├─ GPM-EN1 MC ArcadeDB pin backend (← RT5 PIN-F4, RT7 MCR-F1) ───────┘  └──┐
  ├─ GPM-EN2 MC reification (← RT5 PIN-F2) ─────────────────────────────────┘
  ├─ GPM-F7 FE streaming render (← GPM-F1) ← FE KEYSTONE
  ├─ GPM-F6 FE cockpit (← GPM-F7, GPM-F5)
  ├─ GPM-F8 FE design system (independent)
  ├─ GPM-F9 FE perf budget CI (independent)
  ├─ GPM-F10 FE auth/session (← GPM-F7, GPM-F1b)
  ├─ GPM-F1b MC ACA deploy (← GPM-F1, GPM-F5, GPM-EN1)
  ├─ GPM-F11b FE Storybook (← GPM-F8)
  └─ GPM-EN3 FE → ACA wiring (← GPM-F1b, GPM-F10)
```

**Spoke keystone chain:** RT6 UDA-F3 (pagination) → RT8 GPM-F3 (analytics). RT5 PIN-F4 → RT7 MCR-F1
→ RT8 GPM-EN1. RT7 MCR-F4 → RT8 GPM-F4. No spoke train depends on the hub trains (RT1–RT4).

**Critical cross-RT constraint:** RT8 GPM-F3 is blocked until RT6 UDA-F3 (pagination) ships. Treat
UDA-F3 as a dependency gate when scheduling RT8 sessions.

---

## Session-Sequenced Milestone Plan

> **Operational view only.** This army plans in agent sessions, not calendar time. No calendar dates are maintained. Each row below is one session-level commitment: what lands, which issues close, and the cumulative throughput against the session baseline (~4 Size:M/session for foundation work; ~1–3/session for implementation-heavy work). Update this table after each session.

### Hub trains RT1–RT4 — session plan

| Session | RT | Target issues | What lands | Expected throughput | Status |
|---|---|---|---|---|---|
| **Session 1** ✅ | RT1 | #18, #19, #20, #44 | Agent Spec Template, Routing Tree, Hook System, Token-setup docs | 4 features | **DONE** — draft PRs #55–#58 open |
| **Session 2** | RT1 | #21, #22, #23 | Context Graph, Telemetry Instrumentation, Prompt Library Phase 1 | 3 features | Not started |
| **Session 3** | RT2 | #25, #26 | Multi-Agent Choreography, Eval Gates | 2 features | Not started |
| **Session 4** | RT2 | #27, #28, #29 | Skill Scaffolding, Learning Loop Runtime, Artifact Lifecycle | 2–3 features | Not started |
| **Session 5** | RT2/RT3 | #30, #32, #33, #34 | Cost Visibility wrap + RT3 ramp: Onboarding Playbook, Capacity Model, Spoke Manifest | 2–3 features | Not started |
| **Session 6** | RT3/RT4 | #35, #36, #38, #39 | Observability Dashboard, Prompt Adaptation, KB, Tracing | 2–3 features | Not started |
| **Session 7** | RT4 | #40, #41 | Feedback Integration, Competency Tracking — final hub sprint | 2 features | Not started |
| **Session 8** _(buffer)_ | — | Spillover / revision passes | — | — | Hold in reserve |

**Cumulative throughput target (Sessions 1–7):** ~18–21 features closed across hub RT1–RT4.
**PI mapping:** PI-1 = Sessions 1–2 (RT1); PI-2 = Sessions 3–5 (RT2/RT3); PI-3 = Sessions 6–7 (RT4).
A PI spans approximately 5 sessions at current velocity; recalibrate at each PI boundary.

### Session Summary (operational view) — Hub trains RT1–RT4

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

### Session Summary (operational view) — Spoke trains RT5–RT8

Spoke sessions run independently of hub sessions on a separate cadence. Schedule at PI planning
once spoke repo readiness is confirmed. Estimates assume implementation-heavy velocity (1–3 Size:M
features/session).

| Session | Target features | RT | Expected throughput | Notes |
|---|---|---|---|---|
| **Spoke-S1** | RT6 UDA-F3 (#47), UDA-F1 (#45) | RT6 | 2 features | UDA-F3 is P0 — gates RT8 GPM-F3; schedule first |
| **Spoke-S2** | RT5 PIN-F1, PIN-F2 | RT5 | 2 features | Foundation primitives; parallel with Spoke-S1 if agents available |
| **Spoke-S3** | RT5 PIN-F3, PIN-EN1; RT6 UDA-F2 (#46) | RT5/RT6 | 2–3 features | PIN-F3 keystone + FE wiring enabler; UDA-F2 independent |
| **Spoke-S4** | RT5 PIN-F4 (ArcadeDB adapter); RT7 MCR-EN1 | RT5/RT7 | 2 features | PIN-F4 unblocks RT7 MCR-F1; MCR-EN1 unblocks all RT7 features |
| **Spoke-S5** | RT7 MCR-F1, MCR-F2, MCR-F3, MCR-F4 | RT7 | 3–4 features | 4-way parallelism after MCR-EN1; MCR-F1 is the RT7 keystone |
| **Spoke-S6** | RT8 GPM-F1 (MC streaming), GPM-F8 (FE design), GPM-F9 (FE perf CI) | RT8 | 3 features | RT8 keystone + independent FE work; 3 parallel agents |
| **Spoke-S7** | RT8 GPM-F7 (FE streaming render), GPM-F2 (MC memory), GPM-F5 (MC OTel) | RT8 | 3 features | FE keystone unlocked; 3 parallel agents |
| **Spoke-S8** | RT8 GPM-F6 (FE cockpit), GPM-F3 (MC analytics), GPM-F4 (MC contract test) | RT8 | 3 features | Post-keystone parallelism; RT6 UDA-F3 must be stable |
| **Spoke-S9** | RT8 GPM-F10 (FE auth), GPM-F1b (MC ACA deploy), GPM-F11b (FE Storybook) | RT8 | 3 features | Deploy + auth layer |
| **Spoke-S10** | RT8 GPM-EN1, GPM-EN2, GPM-EN3; RT6 UDA-F4, UDA-F5 | RT8/RT6 | 2–3 features | ArcadeDB pin wiring + FE→ACA; RBAC + caching |
| **Spoke-S11** _(buffer)_ | Spillover, integration testing, revision passes | — | — | Hold in reserve; use if RT5/RT7 dependencies slip |

> Spoke sessions do not yet have assigned Iterations on the board — add them at PI Planning.
> Session numbers are the sole execution cadence; no calendar dates are maintained for spoke trains.
> The spoke boards are the live status source: `nickpclarke/middle-core`, `nickpclarke/backend-core`,
> `nickpclarke/frontend-core`.

---

**Hub sequencing:** RT1 → RT2 → RT3 → RT4, strict by the hub dependency chain above.
**Spoke sequencing:** RT6 Phase 3 and RT5 can start in parallel (Spoke-S1/S2). RT7 starts after
RT5 PIN-F4 ships (Spoke-S4/S5). RT8 starts after RT7 MCR-EN1 and RT6 UDA-F3 are available
(Spoke-S6+). Track live progress, blockers, and status on the respective spoke boards.
