# Backlog Index

> **The GitHub Projects board is the backlog.** Item status, fields, and hierarchy live on the board — not in this file. This page is a thin pointer so the board stays the single source of truth.

**Board:** https://github.com/users/nickpclarke/projects/1

## What's on the board

The RT1–RT4 platform-evolution backlog: **4 Epics + 21 Features** (issues #17–41), each with SAFE fields set — `Type`, `PI`, `Size`, `Estimate`, `Priority`, `Start date`, `Target date` — and Features linked to their Epic via the `Parent issue` field.

| Release Train | Epic | Features | PI |
|---|---|---|---|
| RT1 — Foundation & Routing | [#17](https://github.com/nickpclarke/AgentArmy/issues/17) | #18–23 | PI-1 |
| RT2 — Operations & Quality | [#24](https://github.com/nickpclarke/AgentArmy/issues/24) | #25–30 | PI-2 |
| RT3 — Spoke Readiness | [#31](https://github.com/nickpclarke/AgentArmy/issues/31) | #32–36 | PI-2 |
| RT4 — Learning & Intelligence | [#37](https://github.com/nickpclarke/AgentArmy/issues/37) | #38–41 | PI-3 |
| RT5 — Ontology-Grade Persistence | _to be created (PIN-E)_ | _PIN-F1–F4, EN1–EN2, S1–S2_ | PI-3 (candidate) |
| RT7 — Middle-Core Runtime | [#7](https://github.com/nickpclarke/middle-core/issues/7) (middle-core repo) | [#8](https://github.com/nickpclarke/middle-core/issues/8)–[#16](https://github.com/nickpclarke/middle-core/issues/16) | PI-3 (candidate) |

**RT5 (candidate, not yet on board):** the ontology-grade object-pinning Epic for the
`middle-core` repo — 9 items decomposed with SAFE fields, acceptance criteria, and dependencies in
[RT5-ontology-grade-persistence.md](../../docs/release-trains/RT5-ontology-grade-persistence.md).
Create the issues per the [board-population runbook](board-population-checklist.md) when scheduled.

**CopilotKit Generative-UI (backlogs drafted):** three spoke epics created 2026-05-25 — `frontend-core` #12 (generative UI), `middle-core` #17 (agent runtime, distinct from RT7), `backend-core` #16 (CORS + RBAC pass-through); 5 ADR stubs in `docs/decisions/` (ARC-ADR-002–006, all Proposed); coordination map at [docs/plans/copilotkit-rollout-coordination.md](../../docs/plans/copilotkit-rollout-coordination.md). Full plan: [docs/plans/copilotkit-generative-ui.md](../../docs/plans/copilotkit-generative-ui.md).

## Querying the backlog

```bash
# Live board items + their fields
gh project item-list 1 --owner nickpclarke --format json

# All open RT issues from the repo (epics + features; --label is AND, so use --search for OR)
gh issue list --repo nickpclarke/AgentArmy --state open --search "label:epic OR label:feature"
```

For a richer slice, use the saved board **Views** (Backlog, Sprint Board, Roadmap, by Release Train) — see [docs/github-projects.md](../../docs/github-projects.md#board-views).

## See also

- **Strategy, themes & cross-RT dependencies:** [release-train-index.md](../../docs/release-trains/release-train-index.md)
- **Field definitions & SAFE mapping:** [docs/github-projects.md](../../docs/github-projects.md)
- **Adding/populating items (incl. forks):** [board-population-checklist.md](board-population-checklist.md)
