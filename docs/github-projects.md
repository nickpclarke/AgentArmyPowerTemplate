# GitHub Projects Field Reference

The AgentArmy project board has 21 fields. This document covers what each field means, when to set it, and how the fields map to SAFE constructs.

## Field Reference

### Built-in fields

| Field | Type | Notes |
|---|---|---|
| Title | Text | Issue or PR title — auto-populated |
| Assignees | — | GitHub user(s) doing the work |
| Status | Single Select | Managed by `auto-status` Action — see below |
| Labels | — | Synced from issue labels |
| Linked pull requests | — | Auto-populated when PR references issue |
| Milestone | — | Use as PI container (see SAFE mapping) |
| Repository | — | Auto-populated |
| Reviewers | — | Assigned PR reviewers |
| Parent issue | — | One level up in hierarchy (Feature for a Story) |
| Sub-issues progress | — | Completion percentage of child issues |
| Created / Updated / Closed | Date | Auto-populated |

### Custom fields added by this template

| Field | Type | Values | When to set |
|---|---|---|---|
| **Type** | Single Select | Epic, Feature, Story, Enabler, Bug, Spike, **Decision** | On creation |
| **PI** | Text | e.g. `PI-1`, `PI-2` | On creation or during PI Planning |

> **`Decision`** is the HITL Decision-Artifact type. It is set by the `hitl-coordinator` agent, not during normal backlog creation — see [HITL Decision Pattern](hitl.md).
| **Priority** | Single Select | P0, P1, P2 | During backlog refinement |
| **Size** | Single Select | XS, S, M, L, XL | During estimation |
| **Estimate** | Number | Story points (Fibonacci) | During sprint planning |
| **Iteration** | Iteration | Sprint name | When committed to a sprint |
| **Start date** | Date | Planned start | During sprint planning |
| **Target date** | Date | Planned completion | During sprint planning |

---

## Status Values

These six values are the complete set of Status options on the board. Workflow code that filters by status must match these names **exactly** (case-sensitive). Verify the live set with `gh project field-list <number> --owner <owner> --format json`.

| Value | Meaning | How it's set |
|---|---|---|
| Todo | In backlog, not started | Default when added to board |
| Ready | Refined and ready to start — Definition of Ready met | Set manually during grooming / sprint planning |
| In Progress | Work has started | Auto-set by `auto-status` when a PR referencing this issue is opened |
| In Review | PR is open and under review | Set manually when review begins |
| Done | Work is complete | Auto-set by `auto-status` when that PR is merged |
| Awaiting Decision | Blocked on a HITL decision artifact | Set via the HITL flow (`hitl-coordinator` / `hitl-decision`); `auto-status` skips the In Progress transition for `awaiting-human` items |

To manually override status:

```bash
gh project item-edit --id ITEM_ID \
  --project-id PROJECT_ID \
  --field-id STATUS_FIELD_ID \
  --single-select-option-id OPTION_ID
```

---

## Board Views

Views are how the board's fields turn into a usable workspace. GitHub Projects v2 **views cannot be created via the API or `gh` CLI** — create each one in the web UI (**+ New view**), then set its layout, grouping, filter, and sort. The set below makes each SAFE construct and the HITL workflow first-class.

| View | Layout | Group by | Filter | Sort | Purpose |
|---|---|---|---|---|---|
| **Backlog** | Table | `PI` | `-status:Done` | Priority ↓ | Refinement — every SAFE field as a column |
| **Sprint Board** | Board | `Status` | `iteration:@current` | Priority ↓ | Active sprint kanban (Todo → Ready → In Progress → In Review → Done) |
| **Roadmap** | Roadmap | `PI` | `is:open` | Start date ↑ | Timeline using Start date → Target date |
| **Release Trains** | Table | `Parent issue` | `type:Epic,Feature` | — | Epic → Feature rollup with Sub-issues progress |
| **By Type** | Board | `Type` | `is:open` | — | Distribution across Epic/Feature/Story/Enabler/Decision |
| **🟠 Decisions (HITL)** | Board | `Assignees` | `status:"Awaiting Decision"` | Target date ↑ | All open Decision Artifacts awaiting a human/AI-app call |

Filter syntax notes (Projects v2 query language):

- Single-select fields filter by token: `status:Todo`, `type:Epic`, `priority:P0`, `size:L`
- Values with spaces need quotes: `status:"Awaiting Decision"`, `status:"In Progress"`, `status:"In Review"`
- The text `PI` field filters by value: `PI:PI-1`
- Iteration shortcuts: `iteration:@current`, `iteration:@next`
- HITL slices also work off labels: `label:hitl-decision`, `label:"assignee:human"` (quote label values that contain a colon)

The **Decisions (HITL)** view is the board face of the [HITL Decision Pattern](hitl.md) — it surfaces every `Awaiting Decision` item so nothing blocks silently. See that guide for the full lifecycle (comment → close → auto-unblock).

---

## Priority Definitions

| Value | Meaning |
|---|---|
| P0 | Must ship this sprint — blocks other work or has external commitment |
| P1 | Should ship this PI — high business value, scheduled |
| P2 | Backlog — desirable but not time-sensitive |

P0 items are exempt from the stale workflow — they will never be auto-closed.

---

## Size Definitions

| Value | Effort |
|---|---|
| XS | ≤ half a day |
| S | ≤ 1 day |
| M | ≤ 3 days |
| L | ≤ 1 week |
| XL | > 1 week — consider splitting |

XL items should almost always be split before committing to a sprint.

---

## SAFE Construct Mapping

| SAFE Construct | GitHub Object | Notes |
|---|---|---|
| Portfolio Epic | Issue (Type: Epic) + Milestone | No cross-project rollup; Epic is a label convention |
| Feature | Issue (Type: Feature, parent = Epic milestone) | Use Parent issue field |
| Story | Sub-issue of Feature (Type: Story) | GitHub max 2 levels of hierarchy |
| Enabler | Issue (Type: Enabler) | Same level as Story |
| Spike | Issue (Type: Spike) | Time-box via Target date |
| Program Increment | Milestone | Named `PI-1`, `PI-2`, etc. |
| Sprint / Iteration | Iteration field | Set via project board |
| PI Objective | Issue (Type: Feature, pinned) | No native construct |
| Dependency | Linked issue + `blocked-by` label | No visual dependency map |
| WSJF | Scripted (see below) | No native calculated field |

---

## Hierarchy Convention

GitHub supports one level of parent-child natively (Parent issue → Sub-issue). Use this mapping:

```
Milestone: PI-1
└── Feature #10: User authentication (Type: Feature)
    ├── Story #11: Login with email (Type: Story)
    ├── Story #12: Password reset (Type: Story)
    └── Enabler #13: Auth middleware setup (Type: Enabler)
```

Epics that span multiple PIs use a label `Epic` and are tracked as a Milestone grouping Features across PIs.

---

## WSJF Scoring (Manual Process)

GitHub Projects v2 does not support calculated fields. Until a GitHub Action automates this, score WSJF manually:

```
WSJF = (Business Value + Time Criticality + Risk Reduction) / Job Size
```

Add a comment to the Feature issue with the scores. Use the `Priority` field to reflect the computed band:
- WSJF ≥ 8 → P0
- WSJF 4–7 → P1
- WSJF < 4 → P2

A future Action (`wsjf-priority.yml`) can automate this once Business Value, Time Criticality, and Risk Reduction custom fields are added.

---

## Useful Board Queries

```bash
# All P0 items not yet Done
gh project item-list 1 --owner OWNER --format json | \
  python3 -c "
import sys, json
items = json.load(sys.stdin)['items']
for i in items:
    if i.get('priority') == 'P0' and i.get('status') != 'Done':
        print(i['title'], i['status'])
"

# Items in current iteration
gh project item-list 1 --owner OWNER --format json | \
  python3 -c "
import sys, json
items = json.load(sys.stdin)['items']
for i in items:
    if i.get('iteration'):
        print(i['title'], i['status'], i['iteration'])
"
```

---

## Automation: Field IDs

When writing GitHub Actions that update fields via GraphQL, you need the field and option IDs. Retrieve them:

```bash
gh project field-list PROJECT_NUM --owner YOUR_USERNAME --format json
```

The `auto-status.yml` workflow has the field and option IDs hardcoded in its `env` block — update these when setting up your own fork.
