# Agent Audit & MECE Validation

Validate new agents for MECE compliance, diagnose routing ambiguity, or conduct semi-annual roster audits.

## Usage

```
/agent-audit validate <agent-name> <description> <category>
/agent-audit diagnose "<task-description>"
/agent-audit audit [semi-annual|full|category-N]
```

## Examples

**Validate a new agent before merge:**
```
/agent-audit validate fastapi-plus-developer "Advanced FastAPI patterns, async streaming, background tasks" 02-language-specialists
```

**Diagnose routing confusion:**
```
/agent-audit diagnose "I have a slow React component. Should I use react-specialist or performance-engineer?"
```

**Run semi-annual governance audit:**
```
/agent-audit audit semi-annual
```

**Audit a specific category:**
```
/agent-audit audit category-02
```

## What This Does

Invokes the `agent-distinctiveness-advocate` agent to enforce MECE (Mutually Exclusive, Collectively Exhaustive) principles:

### Validate
- ✅ Primary deliverable distinct from ≥3 existing agents?
- ✅ Boundary conditions vs. overlapping agents explicit in description?
- ✅ 5-task routing test: does this agent win unambiguously?
- ✅ Correct category tier (language vs. framework vs. platform in 02)?
- ✅ Follows agent description template?

**Output**: Approval checklist or required clarifications before merge.

### Diagnose
- ✅ Is description vague? (suggest wording improvements)
- ✅ Are two agents genuinely overlapping? (merge or add boundary rule?)
- ✅ Is distinction real but poorly communicated? (add examples)

**Output**: Root cause analysis + fix recommendation.

### Audit
- ✅ New overlaps (description drift since last audit)
- ✅ Coverage gaps (domains with no specialist agent)
- ✅ Boundary rule decay (documented rules still being followed?)
- ✅ Tier violations (category 02 unauthorized new tiers)

**Output**: Audit report with defects + prioritized backlog.

## When to Use

- **Before merging new agents** — prevent distinctiveness regressions
- **On routing confusion reports** — diagnose why users can't pick an agent
- **Scheduled governance** — May & November semi-annual audits
- **Boundary disputes** — when two agents claim the same task

## Source Material

The advocate reads from:
- `docs/mece-audit/AGENT_MECE_AUDIT_RUBRIC.md` — 7-part framework for assessment
- `docs/mece-audit/AGENT_MECE_AUDIT_SCORECARD.md` — baseline findings
- `.claude/agents/categories/02-language-specialists/TAXONOMY.md` — tier definitions & routing rules
- `AGENTS.md`, `CLAUDE.md` — current roster & documented boundaries

## Context

Replaces ad-hoc judgment calls with a structural framework. Works proactively (pre-merge) and reactively (ambiguity diagnosis). Maintains agent distinctiveness as the roster scales.
