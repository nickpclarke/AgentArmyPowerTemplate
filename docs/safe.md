# SAFE Workflow Guide

How to run a Scaled Agile Framework (SAFe) workflow using this template. Covers what maps well, what needs workarounds, and what is not supported.

## SAFE Levels Supported

| Level | Support |
|---|---|
| Team | Full — sprints, stories, tasks, kanban |
| Program (ART) | Partial — PIs via Milestones, Features, cross-team tracking |
| Large Solution | Minimal — Capabilities not natively supported |
| Portfolio | Minimal — Epics by label convention only, no cross-project rollup |

This template is optimised for **Team and Program level** SAFE.

---

## Program Increment (PI) Setup

A PI is typically 10 weeks (5 × 2-week sprints). Use a GitHub Milestone to represent each PI.

```bash
# Create a PI milestone
gh api repos/OWNER/REPO/milestones \
  -X POST \
  -f title="PI-1" \
  -f description="Program Increment 1 — 2026-Q1" \
  -f due_on="2026-03-27T00:00:00Z"

# Assign a Feature to PI-1
gh issue edit ISSUE_NUM --milestone "PI-1"

# Also set the PI custom field on the project item
gh project item-edit --id ITEM_ID --project-id PROJECT_ID \
  --field-id PI_FIELD_ID --text "PI-1"
```

---

## Sprint / Iteration Setup

Iterations are managed on the project board. Create a new iteration at the start of each sprint:

1. Open your project board in the GitHub UI
2. Go to **Settings → Iteration field**
3. Add a new iteration with name (`Sprint 1`), start date, and duration (14 days)

Or via GraphQL:

```bash
gh api graphql -f query='
  mutation($project: ID!, $field: ID!) {
    addProjectV2IterationFieldIteration(input: {
      projectId: $project
      fieldId: $field
      startDate: "2026-01-06"
      duration: 14
    }) {
      iteration { id title }
    }
  }' \
  -f project="PROJECT_ID" \
  -f field="ITERATION_FIELD_ID"
```

---

## PI Planning Process

1. **Create the PI Milestone** with due date at end of PI
2. **List candidate Features** — create issues with Type: Feature, assign to the PI Milestone and set PI field
3. **Decompose Features into Stories** — create sub-issues under each Feature
4. **Estimate Stories** — set Size and Estimate fields
5. **Assign to Iterations** — commit Stories to specific sprints via the Iteration field
6. **Set PI Objectives** — create a pinned Feature-type issue per team titled `PI-N Objectives` listing committed objectives and stretch objectives

---

## Work Item Hierarchy

GitHub supports 2 levels of parent-child. Use the following mapping:

```
Milestone: PI-1
│
└── Feature (issue, Type: Feature, milestone: PI-1)
    │   Title: "User can authenticate with SSO"
    │   Parent issue: (none)
    │
    ├── Story (sub-issue, Type: Story)
    │       Title: "User sees SSO login button on login page"
    │
    ├── Story (sub-issue, Type: Story)
    │       Title: "User is redirected to IdP on SSO click"
    │
    └── Enabler (sub-issue, Type: Enabler)
            Title: "Configure SAML 2.0 provider integration"
```

Epics that span multiple PIs:

```
Label: Epic
Milestone: (no single PI — spans PI-1, PI-2)
Features reference the Epic in their body with "Part of #EPIC_NUM"
```

---

## Sprint Cadence

| Event | When | GitHub action |
|---|---|---|
| Sprint Planning | Day 1 | Assign Stories to Iteration, set Start date |
| Daily Standup | Daily | Check board status — filter by Iteration |
| Sprint Review | Day 14 | Review Done items, demo to stakeholders |
| Sprint Retrospective | Day 14 | Create an issue Type: Enabler with retro action items |
| PI Planning | Last sprint of PI | Create next PI Milestone, populate Features |

---

## Known Limitations

These are structural gaps in GitHub Projects v2 for SAFE. Each has a recommended workaround.

### 1. Hierarchy max 2 levels

**Gap:** SAFE needs Epic → Feature → Story → Task (4 levels). GitHub supports 1 level of parent-child (Feature → Story).

**Workaround:** Model only Feature → Story in the hierarchy. Epics are tracked by label and Milestone grouping. Tasks are inline checklist items in Story issue bodies.

### 2. No Program Board / dependency visualisation

**Gap:** SAFE PI Planning produces a Program Board showing Feature dependencies across teams and their iteration commitments. GitHub has no dependency graph view.

**Workaround:**
- Use a `blocked-by` label convention: add to an issue's body `Blocked by #N`
- Link issues explicitly using GitHub's "linked issues" feature
- For cross-team dependencies, create a shared tracking issue per dependency

### 3. No native WSJF calculation

**Gap:** Weighted Shortest Job First requires 4 inputs (Business Value, Time Criticality, Risk Reduction, Job Size) and a calculated output. GitHub Projects v2 has no calculated fields.

**Workaround:** Add numeric custom fields for each WSJF component, then run a scheduled GitHub Action that reads them, computes the score, and writes the result back to the Priority field. This Action is not yet included in the template — contributions welcome.

### 4. No PI Objectives construct

**Gap:** SAFE uses formal PI Objectives with Business Value scores agreed with business owners.

**Workaround:** Create a pinned issue per team per PI titled `PI-N Team Objectives`. Use a table in the body with columns: Objective, BV Score (planned), BV Score (actual), Status.

### 5. No capacity planning

**Gap:** SAFE sprint planning includes per-person capacity (accounting for leave, ceremonies, etc.) compared against story point commitments.

**Workaround:** Add capacity as a comment on the Iteration planning issue. The `Estimate` field sum per sprint can be read from the API for comparison.

### 6. Cross-project portfolio rollup

**Gap:** If you have multiple repos/teams with separate project boards, there is no native way to aggregate status at portfolio level.

**Workaround:** Create a dedicated portfolio project board and manually add cross-repo issues to it. Or script a nightly Action that queries each team board and posts a summary issue to the portfolio board.

---

## Metrics

### Velocity

```bash
# Story points completed in an iteration
gh project item-list PROJECT_NUM --owner OWNER --format json | \
  python3 -c "
import sys, json
items = json.load(sys.stdin)['items']
velocity = sum(
    int(i.get('estimate', 0) or 0)
    for i in items
    if i.get('status') == 'Done' and i.get('iteration') == 'Sprint N'
)
print('Velocity:', velocity)
"
```

### PI Predictability

```
Predictability = (Actual BV delivered / Planned BV committed) × 100%
```

Track planned vs actual BV on the PI Objectives issue.

### Flow metrics

The `pi-report.yml` Action generates a weekly snapshot of per-Status counts (Todo / Ready / In Progress / In Review / Done / Awaiting Decision). For flow efficiency and cycle time, export the board data and analyse in a spreadsheet or BI tool using the `Created` and `Closed` date fields.
