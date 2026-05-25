# Spoke Work Intake

How a spoke repo (frontend-core, backend-core, middle-core) receives work from the hub, manages its own backlog, and delivers via PRs — without a GitHub Projects board.

## The model

A spoke's work queue is its own repo's **Issues + Milestones**. There is no GitHub Project board per spoke. Reasons:

- MicroVM agents that run inside a spoke cannot authenticate to an external Projects v2 board.
- A per-spoke board adds overhead (custom fields, automation tokens) with no benefit at spoke scale.
- Plain Issues + Milestones are fully accessible to all agents and humans with repo access.

The hub Projects board remains the single coordination surface for cross-spoke epics, PI planning, and release-train sequencing. Spokes report progress by updating their Issues; the hub PM/scrum-master reads spoke milestones on demand.

## Hub vs spoke at a glance

| Concern | Hub | Spoke |
|---|---|---|
| Work queue | GitHub Projects v2 board | Repo Issues + Milestones |
| Planning horizon | PI / Release Trains (RT1–RT4) | Sprint = one Milestone |
| Fields | Type, PI, Size, Estimate, Iteration, Priority | Labels only (type + routing) |
| Velocity tracking | Session log in `release-train-index.md` | Short retro note on the closed Milestone |
| Cross-spoke dependencies | Hub board + release-train-index.md | Link to blocking Issue in another spoke repo |
| Release trains | Hub concern — hub PM sequences | Not a spoke concern |

## How an epic arrives

1. The hub PM/scrum-master opens an **epic Issue** in the spoke repo using the `epic-handoff.md` issue template (`.github/ISSUE_TEMPLATE/epic-handoff.md`). The issue title starts with `[EPIC]` and carries the `Epic` + `agent-army-task` labels.
2. The issue contains the goal, scope, acceptance criteria, relevant contracts (OpenAPI specs, shared types), cross-spoke dependencies, and a Definition of Done.
3. Spoke agents (or the scrum-master) review the epic Issue and decompose it into child Stories and Enablers as separate Issues in the same repo. Link each child to the parent epic with a `Parent issue` comment or GitHub sub-issue relationship.

## Decomposing an epic into stories

- Create one Issue per Story or Enabler. Use the standard `[Story]:` or `[Enabler]:` title prefix.
- Write acceptance criteria in each Issue body.
- Assign the `copilot-task` or `agent-army-task` label (see Routing labels below).
- Add the Issue to the current sprint Milestone.

When a PR closes a Story, the PR body must contain `Closes #N`. This is what signals completion — there is no board automation to rely on.

## Sprint and backlog conventions

**Sprint = one Milestone.**

Create a Milestone per sprint with a due date (two-week cadence is typical). Name it simply: `Sprint 1`, `Sprint 2`, etc.

| Action | How |
|---|---|
| Start a sprint | Open a Milestone, assign Issues to it |
| Track progress | Milestone completion % (open vs closed Issues) |
| Close a sprint | Close the Milestone; add a one-paragraph retro note to its description |
| Carry over work | Reassign open Issues to the next Milestone |
| Velocity | Count closed Issues (or story-point labels if used) in the retro note |

There are no PI or Iteration custom fields in a spoke — the hub manages those for the program level. A spoke only needs to know its current sprint Milestone.

**Backlog** is the set of Issues with no Milestone assigned. The spoke scrum-master grooms these before each sprint planning session by reviewing the parent epic, cross-spoke dependency status, and agent capacity.

## Routing labels

Apply one routing label to every spoke Issue at creation:

| Label | When to use | Who picks it up |
|---|---|---|
| `copilot-task` | Bounded, single-file change; clear acceptance criteria; Size XS or S | GitHub Copilot coding agent |
| `agent-army-task` | Complex, multi-file, or architectural; Size M or larger | Claude Code specialist agent |

Also apply a type label matching the Issue kind: `Story`, `Enabler`, `Bug`, `Spike`.

If an agent working a `copilot-task` Issue finds the scope is larger than expected, it removes `copilot-task`, adds `agent-army-task`, and comments explaining why.

## Closing the loop with the hub

Reporting back is **automatic** — you do not comment on the hub, and you do not need the hub
Epic number or board access. The `notify-hub` workflow (`.github/workflows/notify-hub.yml`,
synced into your repo) fires a `repository_dispatch` to the AgentArmy hub whenever you merge a
PR, close an Issue, or comment. The hub records it on its **Spoke Activity Log** and reconciles
its board. That workflow runs in CI with the hub token — not in your sandbox — which is why it
can reach the hub even though you can't.

Your only job when an epic's Definition of Done is met:

1. Close the epic Issue (and its Milestone) in the spoke repo.
2. That's it. The merged-PR / closed-Issue events are dispatched to the hub automatically; the
   hub PM/scrum-master updates board Status and records velocity in
   `docs/release-trains/release-train-index.md`.

> Need to find the hub for reference? It's in `.agent/hub.json` (synced) — repo, board, docs,
> and Labs URLs. Prereq for the dispatch: the `PROJECT_TOKEN` secret must exist in your repo
> (the hub sets this up per spoke).

## Reference

- Hub docs site: <https://nickpclarke.github.io/AgentArmy/>
- Epic handoff template: `.github/ISSUE_TEMPLATE/epic-handoff.md`
- Hub planning: `docs/release-trains/release-train-index.md`
- Routing guide: `CLAUDE.md` (Route work to the right army section)
