# File Organization Strategy for AgentArmy Template

This document is the **authoritative guide** for where to put planning, strategy, and architectural documents in the AgentArmy template repository and its spokes.

## Problem This Solves

**Before:** Strategic planning files cluttered the root directory alongside essential files (README.md, LICENSE, CLAUDE.md), creating confusion about what's permanent vs. working, what's for users vs. internal planning.

**After:** Clear folder separation with naming conventions prevent clutter as the template system scales to support multiple spokes (UI layer, API layer, worker layer, etc.).

---

## Three Categories of Documents

### 1. **Essential Root Files** (Keep at repo root)
These are the absolute minimum needed at the root level.

```
README.md          # Public introduction to the template
CLAUDE.md          # AI agent working guidance
LICENSE            # Legal
.gitignore         # Git rules
mkdocs.yml         # Documentation build config
```

**Rule:** If it's not essential for repository bootstrap, it doesn't live at root.

### 2. **Planning & Strategy** (durable → `/docs/`, hub-internal → `/planning/`)

As of 2026-05-25, **durable strategy that agents and users should read lives in `/docs/`** so it
publishes to GitHub Pages — spoke microVM agents can only reach the published docs site + their own
repo, so plans buried in `/planning/` were invisible to them. **Hub-internal coordination** stays
in `/planning/` (not published).

```
/docs/                    # PUBLISHED to Pages
├── roadmap/              # platform vision, quarterly milestones
├── release-trains/       # RT1–RT5 planning + the release-train index
├── synthesis/            # patterns, integrations, spikes (ArcKit, verification levels)
└── plans/                # cross-layer initiative plans (e.g. CopilotKit generative UI)

/planning/                # HUB-INTERNAL (not published)
├── backlog/              # GitHub Issues index, board population (the board is source of truth)
├── governance/           # process, naming conventions, artifact lifecycle (this doc)
├── meta/                 # army principles, agent validation, learning loops
└── ideas/                # early/raw ideas not yet promoted
```

**Goes in `/docs/` (published) if** it describes platform evolution, is strategic/roadmap-level,
synthesizes patterns/frameworks, or coordinates release trains — anything agents/users should read.

**Stays in `/planning/` (hub-internal) if** it's the board backlog index, governance/process, army
meta, or raw ideas not yet promoted.

**Examples:**
- ✅ `/docs/roadmap/PLATFORM_ROADMAP.md` (how AgentArmy evolves)
- ✅ `/docs/synthesis/ARCKIT_SYNTHESIS.md` (patterns integration)
- ✅ `/docs/release-trains/` (release train plans + index)
- ✅ `/docs/plans/` (cross-layer initiative plans)
- ➡️ `/planning/backlog/`, `/planning/governance/`, `/planning/meta/` (hub-internal coordination)
- ❌ Specific feature implementation (belongs in application code)

### 3. **User-Facing Documentation** (→ `/docs/`)
Guides, tutorials, reference material for people adopting or extending AgentArmy.

```
/docs/
├── guides/              # How-to docs (setup, contributing, etc.)
├── reference/           # Stable reference (agents, routing, conventions)
├── capabilities/        # Concept exploration (Wardley, capabilities, SAFE)
├── integrations/        # External system integration guides
└── agents-glossary/     # Auto-generated agent descriptions
```

**Move here if:**
- It's user-facing guidance (new users need it)
- It's stable reference material (API docs, routing matrix)
- It explains how to USE AgentArmy (not how we IMPROVE it)
- It's meant for external audiences or documentation sites

**Examples:**
- ✅ quick-start.md (how to get started)
- ✅ agents.md (roster of available agents)
- ✅ setup.md (installation & configuration)
- ❌ RT2 release train plan (belongs in `/planning/`)
- ❌ ArcKit synthesis work (belongs in `/docs/synthesis/`)

---

## Naming Conventions

### Release Train Documents
**Format:** `RT<N>-<LIFECYCLE>-<TITLE>.md`

Location: `/docs/release-trains/`

```
RT1-FOUNDATION-ROUTING.md
RT2-OPERATIONS-QUALITY.md
RT3-SPOKE-READINESS.md
RT4-LEARNING-INTELLIGENCE.md
RT1-FOUNDATION-ROUTING-WEEKLY-PROGRESS.md  # Weekly status
```

### Backlog & Issues
**Format:** `<TYPE>-<NUMBER>-<TITLE>.md` or descriptive name

Location: `/planning/backlog/`

```
BACKLOG_ISSUES_INDEX.md          # Master index of all issues
ISSUES_CREATED.md                # Log of created issue numbers
board-population-checklist.md    # GitHub Projects setup guide
```

### Working Synthesis Documents
**Format:** `<SUBJECT>-<DATE-or-QUARTER>-<STAGE>.md` OR descriptive name

Location: `/docs/synthesis/`

**Include dates for drafts, drop them for stable documents:**

```
ARCKIT_SYNTHESIS.md              # Stable (dated internally if needed)
hook-system-design.md            # Stable, evolving
project-context-graph-2026-05-draft.md  # Draft (has date)
learning-loop-Q2-synthesis.md    # Quarterly snapshot
```

### Roadmap & Strategy
**Format:** `<TOPIC>.md` (no dates for permanent artifacts)

Location: `/docs/roadmap/`

```
PLATFORM_ROADMAP.md              # 6-month platform vision
quarterly-milestones.md          # Q1, Q2, Q3, Q4 targets
competitive-landscape.md         # Market positioning
```

### User Documentation
**Format:** `<TOPIC>.md` (no dates, no draft suffix)

Location: `/docs/guides/`, `/docs/reference/`, etc.

```
quick-start.md
setup.md
routing-matrix.md
agents.md
contributing.md
```

---

## Artifact Lifecycle

Documents flow through these phases. Where they live changes as they mature.

### Phase 1: Discovery (Internal, Drafting)
- **Where:** `/docs/synthesis/` or `/planning/backlog/`
- **Naming:** Include date or "draft" suffix
- **Example:** `hook-system-2026-05-draft.md`
- **Status:** Open to major revision
- **Audience:** Contributors, planning team
- **Lifespan:** Days to weeks
- **Next:** Move to Specification when direction is decided

### Phase 2: Specification (Internal, Decided)
- **Where:** `/docs/release-trains/` or `/docs/roadmap/`
- **Naming:** No draft suffix, may include RT# or quarter
- **Example:** `RT1-FOUNDATION-ROUTING.md`
- **Status:** Team has decided; tactical adjustments OK
- **Audience:** Entire team, board reference
- **Lifespan:** Duration of release train (weeks to months)
- **Next:** Move to Public when user-facing (or Archive)

### Phase 3: Public (External, Stable)
- **Where:** `/docs/`
- **Naming:** Topic name only, no date
- **Example:** `setup.md`, `agents.md`
- **Status:** Production-ready guidance
- **Audience:** New users, external community
- **Lifespan:** Ongoing, versioned with releases
- **Next:** Move to Archive or keep updated

### Phase 4: Archive (Reference, Superseded)
- **Where:** `/planning/archive/` (created as needed)
- **Naming:** `<RT>-<TOPIC>-YYYY-completed.md` or descriptive
- **Example:** `RT1-FOUNDATION-ROUTING-2026-07-completed.md`
- **Status:** Reference only, don't update
- **Audience:** Historical context, retrospectives
- **Lifespan:** Permanent (for learning)
- **Next:** None; stays archived

---

## Decision Rules: Where Does This Go?

**Decision Tree:**

```
Is it about the AgentArmy TEMPLATE PLATFORM (not an app)?
├─ YES → Goes to /planning/ (or /docs/ if user-facing)
└─ NO → Goes to /docs/ or application code

Is it strategy/roadmap for the TEMPLATE?
├─ YES → /docs/roadmap/ or /docs/release-trains/
└─ NO → Keep asking...

Is it working synthesis or drafting for the TEMPLATE?
├─ YES → /docs/synthesis/
└─ NO → Keep asking...

Is it GitHub Issues management for the TEMPLATE?
├─ YES → /planning/backlog/
└─ NO → Keep asking...

Is it USER-FACING GUIDANCE or REFERENCE?
├─ YES → /docs/
└─ NO → Check with team; might belong elsewhere
```

---

## Scalability for Spokes

When a user forks AgentArmy into a Spoke (e.g., "AgentArmy-UI-Layer"), the folder structure **scales linearly** with these adaptations:

### Spoke Template Structure
```
/planning/
├── README.md                     # "This is the UI Layer spoke"
├── release-trains/
│   ├── SPOKE_DEVELOPMENT_ROADMAP.md  # Layer-specific roadmap
│   └── sprint-plans/                 # Sprint-level detail
├── backlog/
│   ├── ISSUES_INDEX.md              # This spoke's GitHub Issues
│   └── linked-hub-features.md       # References to Hub RTs
├── synthesis/
│   ├── openapi-contract-design.md  # API schema evolution
│   ├── dependency-map.md           # Dependencies on other spokes
│   └── integration-points.md       # How this layer connects
└── governance/
    └── FILE_ORGANIZATION.md         # Inherit + customize for spoke
```

### Key Differences (Spoke vs. Hub)
| Aspect | Hub | Spoke |
|---|---|---|
| **Focus** | Template platform evolution | This layer's implementation |
| **Roadmap** | 6-month platform vision | Layer-specific features |
| **Synthesis** | Patterns, frameworks, governance | Contracts (API schemas, types) |
| **Backlog** | Template work (25 issues) | Layer-specific work (N issues) |
| **Links** | GitHub Projects board | Cross-repo issue links to Hub |

### Migration Pattern (User Forking Template)
1. Clone AgentArmy template
2. Adapt `/planning/README.md` to state layer name ("This is the API Layer")
3. Remove Hub-specific planning OR archive it in `/planning/archive-hub/`
4. Add spoke-specific roadmap, contract design, dependency mapping
5. Link back to Hub board for cross-layer coordination
6. Keep `/planning/governance/FILE_ORGANIZATION.md` as reference

---

## Enforcement & Prevention

### Git Hooks (Future)
Add a pre-commit hook to warn about root-level .md files:

```bash
# .git/hooks/pre-commit
git diff --cached --name-only | grep -E '^[^/]*\.md$' && echo "⚠️  New .md at root?" || true
```

### Code Review Checklist
When reviewing PRs:
- [ ] New .md files go to `/planning/` (strategy) or `/docs/` (user docs), not root
- [ ] File naming follows conventions (RT#, SUBJECT, or topic name)
- [ ] Artifact is in the right lifecycle phase for its location
- [ ] Spokes inherit this structure without modification

### Naming Convention Linting (Future)
Script to check:
```bash
# Warn if synthesis/ contains non-date files without "draft" suffix
ls docs/synthesis/ | grep -v "draft\|SYNTHESIS\|design\|_" && echo "⚠️  Non-standard naming in synthesis/"
```

---

## Quick Reference Table

| What You're Writing | Location | Naming | Lifespan | Audience |
|---|---|---|---|---|
| 6-month platform vision | `/docs/roadmap/` | PLATFORM_ROADMAP.md | Months | Team |
| Release train plan | `/docs/release-trains/` | RT<N>-LIFECYCLE.md | Weeks–months | Team |
| Pattern synthesis | `/docs/synthesis/` | TOPIC.md or TOPIC-DATE-draft.md | Days–weeks | Contributors |
| GitHub Issues index | `/planning/backlog/` | BACKLOG_ISSUES_INDEX.md | Months | Board ops |
| User guide | `/docs/guides/` | topic.md | Ongoing | Users |
| API reference | `/docs/reference/` | topic.md | Ongoing | Users |
| Agent descriptions | `/docs/agents-glossary/` | (generated) | Ongoing | Users |

---

## Related Documents

- `/planning/README.md` — Purpose & scope of planning folder
- `/docs/release-trains/release-train-index.md` — Master index of all RTs
- `/planning/backlog/board-population-checklist.md` — GitHub Projects setup guide
- `/planning/governance/` — This folder (process & conventions)

---

**Last Updated:** 2026-05-23  
**Approved By:** Architecture Review  
**Applies To:** Hub template + all Spoke repos  

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
