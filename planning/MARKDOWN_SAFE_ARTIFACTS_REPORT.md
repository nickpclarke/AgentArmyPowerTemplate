# Markdown SAFE Program & Project Artifacts Report

**Status:** Post-GitHub-Projects-Population  
**Date:** 2026-05-23  
**Prepared for:** Codebase rationalization and source-of-truth alignment

---

## Executive Summary

After migrating all 25 GitHub issues to the GitHub Projects board and establishing it as the source of truth for work tracking, the markdown SAFE program artifacts in the repository should be **rationalized to 9 core files**.

**Net result:** 9 lean, strategic markdown files + GitHub Projects board (source of truth for sprints, burndown, issue tracking)

---

## Deleted Artifacts (No Longer Needed)

These markdown files should be **deleted** because their content is now on the GitHub Projects board:

| File | Reason for Deletion | Location |
|---|---|---|
| **BACKLOG_ISSUES_INDEX.md** | Issue list, metadata, and field mappings now on board | `planning/backlog/` |
| **release-train-index.md** | RT1-RT4 issue lists and timelines now on board | `docs/release-trains/` |
| **board-population-checklist.md** | One-time setup artifact; no longer needed after board populated | `planning/backlog/` |

**Why:** These were workarounds for "waiting for GitHub Projects TOKEN access." Once issues are on the board, these markdown duplicates create drift and maintenance burden.

---

## Remaining Artifacts (Keep in Repo)

### TIER 1: Governance & Principles (Meta Layer)

| Artifact | Purpose | Owner | Location | Cadence |
|---|---|---|---|---|
| **ARMY_PRINCIPLES.md** | 7 foundational axioms enabling agent army operations: error escalation, knowledge feedback, skill scaffolding, hook integration, delegation direction, MECE, observable decisions | Architecture Lead | `planning/meta/principles/` | Quarterly review + continuous incident feedback |
| **AGENT_ONBOARDING_RUBRIC.md** | Operational checklist for validating new agents before merge. Operationalizes ARMY_PRINCIPLES via pass/fail criteria. CI-enforced. | Governance | `planning/meta/decisions/` | Per-agent onboarding; quarterly audit |
| **SPOKE_META_PLANNING_TEMPLATE.md** | How Spoke repos (layer-specific implementations) inherit Hub principles and customize governance for their context without breaking MECE | Architects | `planning/meta/spoke-templates/` | Per-Spoke initialization |

**Why keep:** These define HOW the organization thinks about agent governance, architecture, and scaling. They are process/principle documents, not work tracking. GitHub Projects doesn't own governance axioms.

---

### TIER 2: Strategic Vision & Roadmap

| Artifact | Purpose | Owner | Location | Cadence |
|---|---|---|---|---|
| **PLATFORM_ROADMAP.md** | 6-month strategic vision for AgentArmy template platform evolution. Includes Wardley analysis, 5 strategic plays, Quarterly milestones, success criteria, cost/effort estimates | Product | `docs/roadmap/` | Quarterly update (end of each RT) |

**Why keep:** This is the *strategic narrative* and rationale for the 4 release trains. It explains WHY we're building what's on the board. GitHub Projects shows WHAT and WHEN; this shows WHY.

---

### TIER 3: Research & Synthesis

| Artifact | Purpose | Owner | Location | Cadence |
|---|---|---|---|---|
| **ARCKIT_SYNTHESIS.md** | Deep synthesis of ArcKit enterprise architecture patterns integrated into AgentArmy structure. Documents design decisions from external framework research | Architecture | `docs/synthesis/` | Quarterly review; update when new patterns discovered |

**Why keep:** This is the "working theory" document that justifies architectural decisions. Useful for onboarding, explaining design rationale, and evaluating new patterns. Not task-tracking.

---

### TIER 4: Process & Governance

| Artifact | Purpose | Owner | Location | Cadence |
|---|---|---|---|---|
| **FILE_ORGANIZATION.md** | Folder strategy, naming conventions, artifact lifecycle, enforcement rules. Prevents clutter and establishes patterns for Spokes | Team | `planning/governance/` | Reference (update if structure changes) |
| **PLANNING_CEREMONIES.md** (planned) | Sprint planning, standups, PI planning, principle review cadence. Defines recurring meetings and decision points | Scrum Master | `planning/meta/ceremonies/` | Reference (timeless) |
| **INCIDENT_TO_PRINCIPLE_WORKFLOW.md** (planned) | Learning loop: production incident → error-coordinator → knowledge-synthesizer → KB → quarterly principle review → agent validation | Knowledge | `planning/meta/learning/` | Reference (timeless) |
| **DECISION_FRAMEWORK.md** (planned) | How we choose between trade-offs (build vs. buy, prioritization, risk acceptance). Standardizes decision criteria referenced by ARMY_PRINCIPLES (observable decisions) and HITL escalation | Architecture Lead | `planning/meta/decisions/` | Reference (timeless) |

**Why keep:** These define HOW we operate and make decisions, not WHAT work we're doing. GitHub Projects cannot express process/ceremony schedules or learning workflows.

---

## Mapping: GitHub Projects vs. Markdown

### GitHub Projects Board (Source of Truth for Work Tracking)

```
Issue tracking       ← 25 issues (#17-41), custom fields, relationships
Sprint planning      ← Iteration assignments, status, burndown
Timeline             ← Start date, target date, milestone
Velocity/metrics     ← Burndown, completion rate, cycle time
```

### Markdown Artifacts (Governance, Strategy, Learning)

```
Governance           ← ARMY_PRINCIPLES.md, AGENT_ONBOARDING_RUBRIC.md
Strategic vision     ← PLATFORM_ROADMAP.md
Research/rationale   ← ARCKIT_SYNTHESIS.md
Process definitions  ← FILE_ORGANIZATION.md, PLANNING_CEREMONIES.md, INCIDENT_WORKFLOW.md, DECISION_FRAMEWORK.md
Spoke templates      ← SPOKE_META_PLANNING_TEMPLATE.md
```

**Clear separation:** Board owns WHAT & WHEN. Markdown owns HOW, WHY, and PRINCIPLES.

---

## Final Artifact Count

| Category | Count | Change |
|---|---|---|
| Governance & Principles | 3 | No change |
| Strategic Vision | 1 | No change |
| Research & Synthesis | 1 | No change |
| Process & Governance | 4 | New (planned) |
| **Total Core Artifacts** | **9** | **+3 (planned)** |
| Deleted Workarounds | 3 | **DELETE** |
| **Net after cleanup** | **9** | **-3 workarounds** |

---

## Content Outline: The 9 Remaining Artifacts

### 1. ARMY_PRINCIPLES.md (16KB)
- 7 principles with implementation guidance
- Links to agent onboarding, spoke templates
- Quarterly review cadence
- Current status: ✅ Complete

### 2. AGENT_ONBOARDING_RUBRIC.md (12KB)
- 6-part rubric (MECE, error, delegation, skills, tools, spoke scalability)
- Decision matrix (PASS/DISCUSS/REJECT)
- CI enforcement rules
- Current status: ✅ Complete + CI-enforced

### 3. SPOKE_META_PLANNING_TEMPLATE.md (8KB)
- How to inherit ARMY_PRINCIPLES
- How to customize for layer-specific concerns
- Example for API Layer Spoke
- Checklist for fork initialization
- Current status: ✅ Complete

### 4. PLATFORM_ROADMAP.md (10KB)
- 6-month vision aligned to 4 RTs
- Wardley analysis (genesis → commodity positioning)
- 5 strategic plays sequenced across RTs
- Success criteria per RT
- Current status: ✅ Complete

### 5. ARCKIT_SYNTHESIS.md (12KB)
- 11 ArcKit patterns mapped to AgentArmy
- Hook system integration
- Multi-rendering strategy
- Risk mitigation from ArcKit lessons
- Current status: ✅ Complete

### 6. FILE_ORGANIZATION.md (8KB)
- Root vs. /planning/ vs. /docs/ rules
- Naming conventions (RT#, FEAT#, SYNTHESIS)
- Artifact lifecycle (Discovery → Specification → Public → Archive)
- Spoke inheritance patterns
- Current status: ✅ Complete

### 7. PLANNING_CEREMONIES.md (4KB) — PLAN TO CREATE
- Sprint planning (2 weeks)
- Daily standup
- PI planning (quarterly)
- Principle review (quarterly)
- Retrospectives (end of RT)
- Current status: 🔄 Planned

### 8. INCIDENT_TO_PRINCIPLE_WORKFLOW.md (4KB) — PLAN TO CREATE
- Production incident capture (Stop hook)
- error-coordinator analysis
- knowledge-synthesizer aggregation
- Quarterly principle review
- KB-to-training feedback
- Current status: 🔄 Planned

### 9. DECISION_FRAMEWORK.md (4KB) — PLAN TO CREATE
- Decision criteria (build vs. buy, prioritization, risk acceptance)
- Trade-off scoring and tie-breakers
- When to escalate to HITL (hitl-coordinator)
- Links to ARMY_PRINCIPLES (observable decisions)
- Current status: 🔄 Planned

---

## Execution: Rationalization Sequence

### Phase 1: Board Population (Run Locally with gh CLI + TOKEN)
1. Run BOARD_POPULATION_EXECUTION_GUIDE.md script
2. Verify all 25 issues on board
3. Confirm custom fields and parent relationships

### Phase 2: Markdown Cleanup (After Board Verified)
```bash
# Delete workarounds (they're now on the board)
git rm planning/backlog/BACKLOG_ISSUES_INDEX.md
git rm docs/release-trains/release-train-index.md
git rm planning/backlog/board-population-checklist.md

# Commit
git commit -m "Delete markdown workarounds - all issues on GitHub Projects board

Board is now source of truth for:
- 25 issues (#17-41) with custom fields
- Sprint tracking and burndown
- Epic-to-feature relationships
- Timeline and milestones

Remaining markdown artifacts (9 files) focus on governance, strategy, and learning loops."

git push origin main
```

### Phase 3: Create Missing Governance Docs (Optional But Recommended)
1. Create `PLANNING_CEREMONIES.md` (sprint/PI/retrospective cadence)
2. Create `INCIDENT_TO_PRINCIPLE_WORKFLOW.md` (learning loop process)
3. Create `DECISION_FRAMEWORK.md` (decision criteria & trade-off framework)

---

## Validation Checklist

After rationalization:

- [ ] GitHub Projects board has all 25 issues with correct fields
- [ ] 3 markdown workarounds deleted (BACKLOG_ISSUES_INDEX, release-train-index, board-population-checklist)
- [ ] 9 core governance/strategy/process artifacts remain
- [ ] No issue tracking or sprint data in markdown (all on board)
- [ ] CLAUDE.md references board for work tracking
- [ ] SPOKE_META_PLANNING_TEMPLATE.md points fork users to board + governance
- [ ] Documentation updated: `/docs/github-projects.md` explains board structure

---

## Risk Mitigation

**Risk:** Markdown and GitHub Projects drift (both sources of truth)  
**Mitigation:** Clear separation of concerns:
- GitHub Projects = WHAT & WHEN (work tracking, timeline)
- Markdown = HOW, WHY, PRINCIPLES (governance, strategy, learning)

**Risk:** New contributors don't understand which source to trust  
**Mitigation:** CLAUDE.md section explains three-layer structure:
- GitHub Projects (task tracking)
- `/docs/release-trains/` (strategy)
- `/planning/meta/` (governance)

---

## Summary

| Artifact Type | Count | Location |
|---|---|---|
| **Governance Principles** | 3 | `/planning/meta/` |
| **Strategic Vision** | 1 | `/docs/roadmap/` |
| **Research & Architecture** | 1 | `/docs/synthesis/` |
| **Process Definitions** | 4 | `/planning/meta/{ceremonies,learning,decisions}/` (planned) |
| **Total Markdown SAFE Artifacts** | **9** | **Core, permanent** |
| **GitHub Projects Board** | 25 issues | **Source of truth for work** |

---

**After this rationalization, the repository is lean, focused, and maintainable. Markdown owns principles, strategy, and learning. GitHub Projects owns work tracking.**

---

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
