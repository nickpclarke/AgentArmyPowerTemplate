# GitHub Projects Board Population Checklist

Step-by-step guide to populate the GitHub Projects v2 board with all 25 AgentArmy template platform issues.

**Status:** All 25 issues created (#17–41). Awaiting GitHub Projects TOKEN configuration.

---

## Prerequisites

Before running the board population script, you need:

- [ ] **GitHub Classic PAT Token** with `project` scope
  - Go to https://github.com/settings/tokens
  - Create new classic token
  - ✅ Check `repo` (includes public_repo, repo:status)
  - ✅ Check `project` (required for Projects v2)
  - Copy token value
- [ ] **Token stored in environment variable**
  ```bash
  export PROJECT_TOKEN="ghp_xxxxxxxxxxxx"
  ```
- [ ] **`gh` CLI installed and authenticated**
  ```bash
  gh auth status
  ```
- [ ] **Project exists** at https://github.com/nickpclarke/AgentArmy/projects/1

---

## Step 1: Verify All 25 Issues Exist

Run this to confirm all issues are created:

```bash
gh issue list --repo nickpclarke/AgentArmy --label Epic,Feature --limit 100 | grep -E "^[[:space:]]*(#17|#18|#19|#20|#21|#22|#23|#24|#25|#26|#27|#28|#29|#30|#31|#32|#33|#34|#35|#36|#37|#38|#39|#40|#41)"
```

Expected output: 25 issues (1 epic per RT, 4–6 features per RT)

✅ **Checkoff:** Issues verified  
```bash
# Sample output to expect:
#17  RT1-EPIC-001: Foundation & Routing        ...
#18  RT1-FEAT-001: Agent Spec Template + ...    ...
#19  RT1-FEAT-002: Executable Routing ...       ...
...
#41  RT4-FEAT-004: Competency Evolution ...     ...
```

---

## Step 2: Add All 25 Issues to the Project Board

Use the batch script provided in BACKLOG_ISSUES_INDEX.md, or run these commands:

```bash
#!/bin/bash
PROJECT_ID="1"
OWNER="nickpclarke"
REPO="AgentArmy"

# Authenticate with TOKEN
export GH_TOKEN="$PROJECT_TOKEN"

# RT1 Issues (#17–23)
for issue in 17 18 19 20 21 22 23; do
  echo "Adding #$issue to board..."
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

# RT2 Issues (#24–30)
for issue in 24 25 26 27 28 29 30; do
  echo "Adding #$issue to board..."
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

# RT3 Issues (#31–36)
for issue in 31 32 33 34 35 36; do
  echo "Adding #$issue to board..."
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

# RT4 Issues (#37–41)
for issue in 37 38 39 40 41; do
  echo "Adding #$issue to board..."
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$OWNER/$REPO/issues/$issue"
done

echo "✅ All 25 issues added to project board!"
```

✅ **Checkoff:** All 25 issues on board

---

## Step 3: Set Custom Fields — RT1 Issues (#17–23)

Set fields for each Release Train 1 issue:

```bash
# Helper function to set fields
set_fields() {
  local issue=$1
  local type=$2      # Epic or Feature
  local pi=$3        # PI-1, PI-2, etc.
  local size=$4      # XS, S, M, L, XL
  local estimate=$5  # Story points (1, 2, 3, 5, 8, 13)
  
  gh project item-edit $issue \
    --project-id=$PROJECT_ID \
    --owner=$OWNER \
    --field="Type" --field-value="$type" \
    --field="PI" --field-value="$pi" \
    --field="Size" --field-value="$size" \
    --field="Estimate" --field-value="$estimate" \
    --field="Status" --field-value="Backlog" \
    --field="Priority" --field-value="P1"
}

# RT1 Epic
set_fields 17 "Epic" "PI-1" "L" "34"

# RT1 Features
set_fields 18 "Feature" "PI-1" "M" "5"
set_fields 19 "Feature" "PI-1" "L" "8"
set_fields 20 "Feature" "PI-1" "L" "13"
set_fields 21 "Feature" "PI-1" "L" "8"
set_fields 22 "Feature" "PI-1" "M" "5"
set_fields 23 "Feature" "PI-1" "M" "3"
```

✅ **Checkoff:** RT1 fields set

---

## Step 4: Set Custom Fields — RT2 Issues (#24–30)

```bash
# RT2 Epic
set_fields 24 "Epic" "PI-2" "L" "41"

# RT2 Features
set_fields 25 "Feature" "PI-2" "L" "8"
set_fields 26 "Feature" "PI-2" "M" "5"
set_fields 27 "Feature" "PI-2" "M" "5"
set_fields 28 "Feature" "PI-2" "L" "8"
set_fields 29 "Feature" "PI-2" "M" "5"
set_fields 30 "Feature" "PI-2" "M" "5"
```

✅ **Checkoff:** RT2 fields set

---

## Step 5: Set Custom Fields — RT3 Issues (#31–36)

```bash
# RT3 Epic
set_fields 31 "Epic" "PI-2" "L" "25"

# RT3 Features
set_fields 32 "Feature" "PI-2" "M" "5"
set_fields 33 "Feature" "PI-2" "M" "5"
set_fields 34 "Feature" "PI-2" "S" "2"
set_fields 35 "Feature" "PI-2" "M" "5"
set_fields 36 "Feature" "PI-2" "S" "3"
```

✅ **Checkoff:** RT3 fields set

---

## Step 6: Set Custom Fields — RT4 Issues (#37–41)

```bash
# RT4 Epic
set_fields 37 "Epic" "PI-3" "L" "20"

# RT4 Features
set_fields 38 "Feature" "PI-3" "M" "5"
set_fields 39 "Feature" "PI-3" "M" "5"
set_fields 40 "Feature" "PI-3" "M" "5"
set_fields 41 "Feature" "PI-3" "M" "5"
```

✅ **Checkoff:** RT4 fields set

---

## Step 7: Create Iterations (Sprints)

Create 12 sprints (2-week iterations) for the 6-month timeline:

```bash
# RT1 Sprints (Jun–Jul)
gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 1 (Jun 1–14)" --field-type="date" \
  --start-date="2026-06-01" --end-date="2026-06-14"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 2 (Jun 15–28)" --field-type="date" \
  --start-date="2026-06-15" --end-date="2026-06-28"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 3 (Jun 29–Jul 12)" --field-type="date" \
  --start-date="2026-06-29" --end-date="2026-07-12"

# RT2 Sprints (Jul–Aug)
gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 4 (Jul 13–26)" --field-type="date" \
  --start-date="2026-07-13" --end-date="2026-07-26"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 5 (Jul 27–Aug 9)" --field-type="date" \
  --start-date="2026-07-27" --end-date="2026-08-09"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 6 (Aug 10–23)" --field-type="date" \
  --start-date="2026-08-10" --end-date="2026-08-23"

# RT3 Sprints (Aug–Oct)
gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 7 (Aug 24–Sep 6)" --field-type="date" \
  --start-date="2026-08-24" --end-date="2026-09-06"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 8 (Sep 7–20)" --field-type="date" \
  --start-date="2026-09-07" --end-date="2026-09-20"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 9 (Sep 21–Oct 4)" --field-type="date" \
  --start-date="2026-09-21" --end-date="2026-10-04"

# RT4 Sprints (Oct–Nov)
gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 10 (Oct 5–18)" --field-type="date" \
  --start-date="2026-10-05" --end-date="2026-10-18"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 11 (Oct 19–Nov 1)" --field-type="date" \
  --start-date="2026-10-19" --end-date="2026-11-01"

gh project field-create --project-id=$PROJECT_ID \
  --name="Sprint 12 (Nov 2–15)" --field-type="date" \
  --start-date="2026-11-02" --end-date="2026-11-15"
```

✅ **Checkoff:** Iterations created

---

## Step 8: Set Parent Issues (Epic Relationships)

Link each feature to its parent epic:

```bash
# RT1 Features → Epic #17
for feature in 18 19 20 21 22 23; do
  gh issue edit --repo nickpclarke/AgentArmy $feature --add-project "1" --set-parent "17"
done

# RT2 Features → Epic #24
for feature in 25 26 27 28 29 30; do
  gh issue edit --repo nickpclarke/AgentArmy $feature --add-project "1" --set-parent "24"
done

# RT3 Features → Epic #31
for feature in 32 33 34 35 36; do
  gh issue edit --repo nickpclarke/AgentArmy $feature --add-project "1" --set-parent "31"
done

# RT4 Features → Epic #37
for feature in 38 39 40 41; do
  gh issue edit --repo nickpclarke/AgentArmy $feature --add-project "1" --set-parent "37"
done
```

✅ **Checkoff:** Parent issues set

---

## Step 9: Set Start & Target Dates

Set release train timeline dates:

```bash
# RT1: Jun 1 – Jul 12
for issue in 17 18 19 20 21 22 23; do
  gh issue edit --repo nickpclarke/AgentArmy $issue \
    --field="Start Date" --field-value="2026-06-01" \
    --field="Target Date" --field-value="2026-07-12"
done

# RT2: Jul 12 – Aug 23
for issue in 24 25 26 27 28 29 30; do
  gh issue edit --repo nickpclarke/AgentArmy $issue \
    --field="Start Date" --field-value="2026-07-12" \
    --field="Target Date" --field-value="2026-08-23"
done

# RT3: Aug 23 – Oct 4
for issue in 31 32 33 34 35 36; do
  gh issue edit --repo nickpclarke/AgentArmy $issue \
    --field="Start Date" --field-value="2026-08-23" \
    --field="Target Date" --field-value="2026-10-04"
done

# RT4: Oct 4 – Nov 15
for issue in 37 38 39 40 41; do
  gh issue edit --repo nickpclarke/AgentArmy $issue \
    --field="Start Date" --field-value="2026-10-04" \
    --field="Target Date" --field-value="2026-11-15"
done
```

✅ **Checkoff:** Dates set

---

## Step 10: Verify Board Setup

Check that the board is properly populated:

```bash
gh project view --project-id=1 \
  --owner="nickpclarke" \
  --format=json | jq '.items | length'

# Expected: 25 items
```

View the board: https://github.com/nickpclarke/AgentArmy/projects/1

✅ **Checkoff:** Board verification complete

---

## Final Verification Checklist

- [ ] All 25 issues appear on the board
- [ ] Each issue has correct Type (Epic or Feature)
- [ ] PI field set correctly (PI-1, PI-2, PI-3)
- [ ] Size field set (S, M, L)
- [ ] Estimate field set (story points)
- [ ] Priority set to P1
- [ ] Status set to "Backlog"
- [ ] Parent issues linked (features → epics)
- [ ] Iterations created (12 sprints)
- [ ] Start & Target dates set per RT
- [ ] No errors in gh CLI output

---

## Troubleshooting

### Issue: TOKEN rejected
```bash
# Verify token has 'project' scope
gh auth status

# Re-authenticate if needed
gh auth login
```

### Issue: Project not found
```bash
# Check project ID
gh project list --owner nickpclarke

# Update PROJECT_ID variable if needed
```

### Issue: Field not recognized
```bash
# List available fields in this project
gh project view --project-id=1 --owner=nickpclarke --format=json | jq '.fields'
```

### Issue: `gh project item-add` not working
```bash
# Minimum gh version: 2.28+
gh version

# Upgrade if needed
gh upgrade
```

---

## Next Steps

Once board is populated:

1. **Review RT1 backlog** — assign owners, start Sprint 1
2. **Create RT1 milestone** in GitHub (Jun 1 – Jul 12)
3. **Schedule sprint planning** — Jun 1 kickoff
4. **Create acceptance criteria** links from issues → docs
5. **Set up board views** — by PI, by release train, by priority
6. **Configure automation** — auto-move on PR, auto-close on merge

---

**Last Updated:** 2026-05-23  
**Status:** Ready to execute (pending TOKEN config)  
**See Also:**
- `/planning/release-trains/release-train-index.md` — RT overview
- `/planning/governance/FILE_ORGANIZATION.md` — File organization strategy
- BACKLOG_ISSUES_INDEX.md — Issue metadata reference

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
