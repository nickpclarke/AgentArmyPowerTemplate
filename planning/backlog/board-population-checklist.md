# Board Population Runbook

How to load issues onto a GitHub Projects v2 board and set their SAFE fields via `gh`.

> **Hub status: done.** The Hub board is already populated — RT1–RT4 issues (#17–41) are on the board with `Type`, `PI`, `Size`, `Estimate`, `Priority`, and dates set, and Features linked to their Epics. This runbook is kept as the reusable procedure for **forks/spokes** populating their own board, and for adding new batches of issues to the Hub.

For what each field means, see [docs/github-projects.md](../../docs/github-projects.md).

---

## Prerequisites

- A **classic PAT** with the `project` **and** `repo` scopes — `project` for board writes, `repo` for the issue/sub-issue writes in Step 3 (the default `GITHUB_TOKEN` cannot write Projects v2). Store it as `PROJECT_TOKEN` and export it: `export GH_TOKEN="$PROJECT_TOKEN"`.
- `gh` CLI **2.28+** authenticated (`gh auth status`).
- The issues already created in the repo, and the project created (`gh project list --owner OWNER`).

---

## Step 1 — Get the project + field IDs

`item-edit` needs the project node ID, each field's ID, and (for single-selects) the option ID.

```bash
OWNER=nickpclarke           # your user/org
REPO=AgentArmy              # your repo name
PROJECT_NUM=1               # your project number

# Project node ID (PVT_...)
gh project view $PROJECT_NUM --owner $OWNER --format json | jq -r .id

# Field IDs + single-select option IDs
gh project field-list $PROJECT_NUM --owner $OWNER --format json \
  | jq -r '.fields[] | "\(.name)\t\(.id)\t\([.options[]? | "\(.name)=\(.id)"] | join(", "))"'
```

> On Windows PowerShell (no `jq`): pipe to `ConvertFrom-Json` and inspect `.fields`.

---

## Step 2 — Add an issue and set its SAFE fields

`gh project item-edit` sets **one field per call**. Add the issue (capture the returned item ID), then set each field:

```bash
PID=PVT_xxxxx               # project node ID from Step 1
ISSUE=18

ITEM=$(gh project item-add $PROJECT_NUM --owner $OWNER \
  --url "https://github.com/$OWNER/$REPO/issues/$ISSUE" --format json | jq -r .id)

# Single-select fields use --single-select-option-id
gh project item-edit --id $ITEM --project-id $PID --field-id <TYPE_FIELD>     --single-select-option-id <FEATURE_OPT>
gh project item-edit --id $ITEM --project-id $PID --field-id <SIZE_FIELD>     --single-select-option-id <M_OPT>
gh project item-edit --id $ITEM --project-id $PID --field-id <PRIORITY_FIELD> --single-select-option-id <P1_OPT>
gh project item-edit --id $ITEM --project-id $PID --field-id <STATUS_FIELD>   --single-select-option-id <TODO_OPT>

# Text / number / date fields
gh project item-edit --id $ITEM --project-id $PID --field-id <PI_FIELD>       --text "PI-1"
gh project item-edit --id $ITEM --project-id $PID --field-id <ESTIMATE_FIELD> --number 5
gh project item-edit --id $ITEM --project-id $PID --field-id <START_FIELD>    --date 2026-06-01
gh project item-edit --id $ITEM --project-id $PID --field-id <TARGET_FIELD>   --date 2026-07-12
```

Loop over your issue list, substituting per-issue values. The Hub's RT1–RT4 issues are already populated — if you need their values as a reference, read them live from the board with `gh project item-list $PROJECT_NUM --owner $OWNER --format json`.

---

## Step 3 — Link Features to their Epic (sub-issues)

The board's `Parent issue` field reflects GitHub **sub-issues**, which `gh` doesn't set directly — use the GraphQL `addSubIssue` mutation with issue **node IDs** (`gh issue view N --json id -q .id`):

```bash
gh api graphql -f query='
  mutation($parent:ID!, $child:ID!) {
    addSubIssue(input:{issueId:$parent, subIssueId:$child}) { issue { number } }
  }' -F parent=<EPIC_NODE_ID> -F child=<FEATURE_NODE_ID>
```

---

## Step 4 — Create the views

Field data alone isn't a workspace — set up the saved **Views** (Backlog, Sprint Board, Roadmap, Release Trains, Decisions/HITL). Views can't be scripted; create them in the web UI per [docs/github-projects.md](../../docs/github-projects.md#board-views).

---

## Verify

```bash
gh project item-list $PROJECT_NUM --owner $OWNER --format json | jq '.items | length'
```

Then open the board and confirm Type/PI/Size/Estimate/Priority/dates are populated and Features nest under their Epics.
