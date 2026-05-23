# Board Population & Markdown Rationalization

**Goal:** Migrate all 25 GitHub issues to GitHub Projects board, set custom fields, then rationalize markdown artifacts.

**Prerequisites:**
- GitHub Classic PAT token with `project` scope (stored in `$PROJECT_TOKEN`)
- `gh` CLI installed and authenticated
- Project exists: https://github.com/nickpclarke/AgentArmy/projects/1

---

## PART 1: Populate GitHub Projects Board (Run Locally)

### Quick Setup

```bash
export PROJECT_TOKEN="ghp_xxxxxxxxxxxx"  # Your classic PAT
export GH_TOKEN="$PROJECT_TOKEN"
export PROJECT_ID="1"
export OWNER="nickpclarke"
export REPO="AgentArmy"
```

### Add All 25 Issues to Board

```bash
#!/bin/bash
# Add all 25 issues to project

for issue in 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41; do
  echo "Adding #$issue to board..."
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

echo "✅ All 25 issues added to project board!"
```

### Set Custom Fields for All Issues

**RT1 (Issues #17–23):**
```bash
for issue in 17 18 19 20 21 22 23; do
  gh issue edit --repo $OWNER/$REPO $issue \
    --add-project "$PROJECT_ID" \
    --field="Type" --field-value="$([ $issue -eq 17 ] && echo 'Epic' || echo 'Feature')" \
    --field="PI" --field-value="PI-1" \
    --field="Priority" --field-value="P1" \
    --field="Status" --field-value="Backlog"
done
```

**RT2 (Issues #24–30):**
```bash
for issue in 24 25 26 27 28 29 30; do
  gh issue edit --repo $OWNER/$REPO $issue \
    --add-project "$PROJECT_ID" \
    --field="Type" --field-value="$([ $issue -eq 24 ] && echo 'Epic' || echo 'Feature')" \
    --field="PI" --field-value="PI-2" \
    --field="Priority" --field-value="P1" \
    --field="Status" --field-value="Backlog"
done
```

**RT3 (Issues #31–36):**
```bash
for issue in 31 32 33 34 35 36; do
  gh issue edit --repo $OWNER/$REPO $issue \
    --add-project "$PROJECT_ID" \
    --field="Type" --field-value="$([ $issue -eq 31 ] && echo 'Epic' || echo 'Feature')" \
    --field="PI" --field-value="PI-2" \
    --field="Priority" --field-value="P1" \
    --field="Status" --field-value="Backlog"
done
```

**RT4 (Issues #37–41):**
```bash
for issue in 37 38 39 40 41; do
  gh issue edit --repo $OWNER/$REPO $issue \
    --add-project "$PROJECT_ID" \
    --field="Type" --field-value="$([ $issue -eq 37 ] && echo 'Epic' || echo 'Feature')" \
    --field="PI" --field-value="PI-3" \
    --field="Priority" --field-value="P1" \
    --field="Status" --field-value="Backlog"
done
```

### Set Parent Issues (Epics)

```bash
# RT1 Features → Epic #17
for feature in 18 19 20 21 22 23; do
  gh issue edit --repo $OWNER/$REPO $feature --add-project "$PROJECT_ID" \
    --field="Parent" --field-value="#17"
done

# RT2 Features → Epic #24
for feature in 25 26 27 28 29 30; do
  gh issue edit --repo $OWNER/$REPO $feature --add-project "$PROJECT_ID" \
    --field="Parent" --field-value="#24"
done

# RT3 Features → Epic #31
for feature in 32 33 34 35 36; do
  gh issue edit --repo $OWNER/$REPO $feature --add-project "$PROJECT_ID" \
    --field="Parent" --field-value="#31"
done

# RT4 Features → Epic #37
for feature in 38 39 40 41; do
  gh issue edit --repo $OWNER/$REPO $feature --add-project "$PROJECT_ID" \
    --field="Parent" --field-value="#37"
done
```

### Verify Board Population

```bash
# Check all issues are on board
gh project view --project-id=$PROJECT_ID --owner=$OWNER --format=json | jq '.items | length'
# Expected: 25
```

---

## PART 2: Markdown Artifacts Rationalization (After Board Population)

Once board is populated, delete these markdown files (they're now in GitHub Projects):

### DELETE (Redundant - Now in GitHub Projects)

```bash
rm planning/backlog/BACKLOG_ISSUES_INDEX.md
rm planning/release-trains/release-train-index.md
```

**Reason:** These were workarounds for "waiting for TOKEN." Now that issues are on the board, these files are redundant. The board is source of truth for:
- Issue status, burndown, sprint tracking
- Custom fields (Type, PI, Size, Estimate, Priority)
- Parent-child relationships (Epic → Features)
- Timeline (start/target dates)

---

## PART 3: Markdown SAFE Artifacts to KEEP

After deletion, the remaining markdown SAFE program artifacts are:

| Artifact | Location | Purpose | Owner | Cadence |
|---|---|---|---|---|
| **ARMY_PRINCIPLES.md** | `/planning/meta/principles/` | Foundational governance axioms | Architecture | Quarterly review |
| **AGENT_ONBOARDING_RUBRIC.md** | `/planning/meta/decisions/` | New agent validation checklist | Governance | Per-agent |
| **SPOKE_META_PLANNING_TEMPLATE.md** | `/planning/meta/spoke-templates/` | Fork governance inheritance | Architects | Per-Spoke |
| **PLATFORM_ROADMAP.md** | `/planning/roadmap/` | 6-month strategic vision | Product | Quarterly update |
| **ARCKIT_SYNTHESIS.md** | `/planning/synthesis/` | ArcKit pattern integration research | Architects | Quarterly review |
| **FILE_ORGANIZATION.md** | `/planning/governance/` | Folder strategy & conventions | Team | Reference |
| **PLANNING_CEREMONIES.md** | `/planning/meta/ceremonies/` | Sprint/PI planning cadence | Scrum Master | Reference |
| **INCIDENT_WORKFLOW.md** | `/planning/meta/learning/` | Error → KB → principle update loop | Knowledge | Reference |

---

## PART 4: What Moves to GitHub Projects (Source of Truth)

**Issue Metadata** (now on board, not in markdown):
- ✅ Issue list & descriptions (#17-41)
- ✅ Custom fields: Type, PI, Size, Estimate, Priority
- ✅ Parent-child relationships (Epic → Features)
- ✅ Iteration/Sprint assignments
- ✅ Start/Target dates
- ✅ Status tracking (Backlog → In Progress → Done)
- ✅ Burndown/velocity reports
- ✅ Sprint planning views

**Markdown still owns:**
- ❌ NOT issue tracking (board owns this)
- ❌ NOT burndown/velocity (board owns this)
- ✅ YES governance principles (ARMY_PRINCIPLES)
- ✅ YES strategic vision (PLATFORM_ROADMAP)
- ✅ YES process definitions (PLANNING_CEREMONIES)
- ✅ YES learning workflows (INCIDENT_WORKFLOW)
- ✅ YES Spoke templates (SPOKE_META_PLANNING_TEMPLATE)

---

## Summary: Net Markdown SAFE Artifacts

**Before (with workarounds):**
- 12 markdown files (including issue index, release train index, board population checklist)

**After (source of truth shift):**
- **8 markdown files** (governance, strategy, process, learning)
- **GitHub Projects board** (25 issues, custom fields, timeline, burndown)

**Deleted (5 files):**
1. BACKLOG_ISSUES_INDEX.md
2. release-train-index.md
3. board-population-checklist.md
4. (2 others moved to planned deprecation)

---

## Execution Checklist

- [ ] Run board population script locally (with TOKEN + gh CLI)
- [ ] Verify all 25 issues appear on board at: https://github.com/nickpclarke/AgentArmy/projects/1
- [ ] Verify custom fields set correctly (Type, PI, Priority, Status)
- [ ] Verify parent-child relationships established
- [ ] Delete the 5 redundant markdown files (on branch)
- [ ] Commit deletion with message referencing board population completion
- [ ] Push to main
- [ ] Archive old markdown artifacts (if historical reference needed) in `/planning/archive/`

---

**After completion:**
- GitHub Projects board is source of truth for work tracking
- Markdown artifacts are lean (8 files) and strategic
- Governance principles live separately from task tracking
- Spoke templates enable systematic forking without confusion

---

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
