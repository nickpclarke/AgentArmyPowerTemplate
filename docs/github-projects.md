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
| **Type** | Single Select | Epic, Feature, Story, Enabler, Bug, Spike | On creation |
| **PI** | Text | e.g. `PI-1`, `PI-2` | On creation or during PI Planning |
| **Priority** | Single Select | P0, P1, P2 | During backlog refinement |
| **Size** | Single Select | XS, S, M, L, XL | During estimation |
| **Estimate** | Number | Story points (Fibonacci) | During sprint planning |
| **Iteration** | Iteration | Sprint name | When committed to a sprint |
| **Start date** | Date | Planned start | During sprint planning |
| **Target date** | Date | Planned completion | During sprint planning |

---

## Status Values

| Value | Meaning | How it's set |
|---|---|---|
| Todo | In backlog, not started | Default when added to board |
| In Progress | Work has started | Auto-set when a PR referencing this issue is opened |
| Done | Work is complete | Auto-set when that PR is merged |

To manually override status:

```bash
gh project item-edit --id ITEM_ID \
  --project-id PROJECT_ID \
  --field-id STATUS_FIELD_ID \
  --single-select-option-id OPTION_ID
```

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
