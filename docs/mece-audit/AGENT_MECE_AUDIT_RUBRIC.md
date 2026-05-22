# Agent Army MECE Audit Rubric

## Purpose

This rubric ensures the agent roster is **Mutually Exclusive** (no task should route unambiguously to two agents) and **Collectively Exhaustive** (every task type has a clear home). Semantic distinctiveness of agent *descriptions* is the primary tool for achieving this.

---

## Part A: Foundational MECE Principles

### Definition
- **Mutually Exclusive**: Each agent owns exactly one decision artifact or action type. A realistic task cannot legitimately route to two agents without explicit disambiguation.
- **Collectively Exhaustive**: Together, all agents cover the full problem domain. No task type should fall through the cracks.

### Why It Matters for Agents
- **Routing precision**: Users and automation should determine the right agent without consulting a second reference
- **Role clarity**: Each agent's description must unambiguously signal when to invoke it
- **Delegation confidence**: Team leads need to know that assigning work to an agent won't create hidden overlap with another role

### Common Violations
1. **Scope creep**: Agent A's description says "build React components"; Agent B says "optimize React apps" — both own React work
2. **Diagonal overlap**: Agent A owns "language-level work" (TypeScript); Agent B owns "concern-level work" (type safety) — they converge on the same artifact
3. **Granularity mismatch**: One agent is scoped to a framework (Next.js); another to a layer (backend); they collide on next-backend-for-api
4. **Boundary vagueness**: No explicit rule for "does frontend-developer or react-specialist own this task?"

---

## Part B: Semantic Distinctiveness Rubric

### Dimension 1: Primary Deliverable

**What it tests**: Each agent's description should signal the artifact they produce or modify.

| Grade | Criteria | Example |
|-------|----------|---------|
| **MECE** | Artifact is singular and non-overlapping with other agents | `api-designer` → OpenAPI specs; `backend-developer` → server code + architecture |
| **Overlap** | Artifact is shared with another agent (diagonal or direct) | `react-specialist` and `frontend-developer` both produce React components |
| **Vague** | Artifact is implicit or shared across multiple interpretations | `architect-reviewer`: does it produce ADRs, reviews, or something else? |

**Scoring**:
- Score each agent's primary deliverable
- Map deliverables across agents: duplicates = overlap
- Document the explicit rule separating overlapping agents

**Example Fix** (for `react-specialist` vs `frontend-developer`):
```
BEFORE (overlap):
  - react-specialist: "optimize React applications for performance"
  - frontend-developer: "build complete frontend applications across React, Vue, Angular"

AFTER (MECE):
  - react-specialist: "optimize existing React codebases for performance, state mgmt, hooks"
  - frontend-developer: "build complete multi-framework frontends from scratch; architecture & integration"
  → Rule: frontend-developer owns cross-framework choices; react-specialist owns React internals only
```

---

### Dimension 2: Routing Test (The Gold Standard)

**What it tests**: Can a realistic task route unambiguously to one agent?

**Methodology**:
1. Write 20 realistic task descriptions across your domain
2. Ask: "Which agent should own this?"
3. Count ambiguities: tasks that could legitimately go to 2+ agents signal overlap
4. Any ambiguity >5% = MECE violation

**Example tasks to test**:
- "Improve React component render performance"  
  → react-specialist or performance-engineer? (diagonal overlap)
- "Build a Node.js API that calls a database"  
  → backend-developer or node-specialist? (needs boundary rule)
- "Set up CI/CD for deploying Docker containers"  
  → devops-engineer, deployment-engineer, docker-expert? (three-way overlap)

**Current roster gaps from research**:
- `react-specialist` vs `frontend-developer` vs `performance-engineer` — 30-40% task ambiguity
- `backend-developer` vs `node-specialist` vs `fastapi-developer` — framework-vs-layer confusion
- DevOps agents (`devops-engineer`, `deployment-engineer`, `sre-engineer`, `platform-engineer`) — 4 agents, high collision rate on "automate infrastructure"

---

### Dimension 3: Decision Rule Clarity

**What it tests**: For agents that share territory, is the boundary explicit?

**Template**:
```
[Agent A] owns X when: [explicit condition]
[Agent B] owns X when: [explicit condition]
Edge case [scenario] routes to: [Agent name, with reason]
```

**Example (solid boundary)**:
```
performance-engineer: Owns bottleneck identification and measurement across ANY layer (app/db/infra)
database-optimizer: Owns query tuning and indexing for databases specifically
Edge case "slow database query": performance-engineer first (diagnosis), 
  then database-optimizer (implementation)
```

**Example (needs work - current state)**:
```
frontend-developer: "building complete frontend applications across React, Vue, Angular"
react-specialist: "optimizing existing React applications"
→ AMBIGUOUS on "build a new React app" — does the developer choose? Does one agent always precede the other?
→ FIX: Explicit rule needed: "frontend-developer for greenfield or multi-framework selection; react-specialist for existing React codebases only"
```

---

### Dimension 4: Behavioral Divergence

**What it tests**: Do agents suggest different actions for the same task?

**Methodology**:
- Run the same task through two agents you suspect overlap
- Log suggestion counts by action type (design, implement, optimize, refactor, etc.)
- Correlation >0.8 = behavioral homogeneity = MECE violation

**Research finding**: Agents with diagonal overlap (same artifact, different focus) show 0.75–0.85 suggestion correlation, indicating redundancy.

---

## Part C: Assessment Rubric (Scoring Checklist)

### Level 1: Description Quality ✓/✗

For each agent, verify the description answers all of:

| Question | Semantic Test | Pass if |
|----------|---|---|
| **1. What artifact does this agent produce or modify?** | Primary deliverable clarity | Deliverable is named explicitly (e.g., "SQL query optimization", "OpenAPI specification", "Helm charts") |
| **2. What problem does it solve that no other agent solves?** | Uniqueness test | The answer is distinct from ≥2 similar agents' answers |
| **3. When should a user invoke this agent (not another)?** | Boundary condition test | Description includes a "use when" clause that disambiguates from adjacent agents |
| **4. What decision does this agent make?** | Decision ownership test | The description clarifies whether it decides (e.g., "design architectures") or implements (e.g., "build microservices") |
| **5. What tools/skills does it rely on?** | Scope boundary test | Tools are listed and are distinct from adjacent agents' tools |

**Scoring**: 
- 5/5 → **MECE-ready**: description is sufficient for unambiguous routing
- 3–4/5 → **Boundary clarification needed**: add explicit decision rules or examples
- 1–2/5 → **Major overlap**: merge or redefine scope

---

### Level 2: Intra-Category Coherence ✓/✗

Within a single category (e.g., "02-language-specialists"), verify:

| Check | What it tests | Pass criteria |
|-------|---|---|
| **Scope axis consistency** | Are agents scoped to the same dimension? (language, framework, concern, or layer?) | All agents in category share the same primary axis. E.g., "02" is language-first (Python, Go, Kotlin, etc.) |
| **Granularity uniformity** | Do agents have similar "size" (scope breadth)? | None is 2x–10x the scope of others. E.g., `typescript-pro` should not subsume `nextjs-developer` |
| **Edge cases covered** | Are there implicit sub-cases the category doesn't cover? | List 5 realistic sub-tasks; verify ≥1 agent owns each |

---

### Level 3: Cross-Category Alignment ✓/✗

Across the full 11 categories, verify:

| Check | What it tests | Pass criteria |
|-------|---|---|
| **No diagonal overlaps** | Do agents from different categories (e.g., "01" frontend vs "02" React) collide? | Diagonal pairs have an explicit rule (e.g., "react-specialist owns component internals; frontend-developer owns framework selection") |
| **Completeness** | Does the roster cover all major problem domains? | For your known backlog, every incoming agent has a clear home category or signals a coverage gap |
| **Model allocation** | Are models assigned consistently? | Agents with similar scope (e.g., specific language specialists) use the same model tier; orchestrators use Opus |

---

## Part D: Current Roster Findings

### High-Confidence MECE ✓
- **Enterprise Architecture** (Category 11): Clear TOGAF phase separation; no overlaps
- **Language Specialists** (Category 02): Well-scoped per language; minimal framework-level collision
- **Infrastructure** (Category 03): Layer-based (cloud, container, k8s, network); mostly distinct

### Diagonal Overlaps (Need Boundary Rules) ⚠️
| Agents | Issue | Recommendation |
|--------|-------|---|
| `frontend-developer` + `react-specialist` | Both own React code; unclear when to choose | Add: "frontend-developer for greenfield multi-framework; react-specialist for optimization of existing React only" |
| `backend-developer` + `node-specialist` + `fastapi-developer` | All build server-side services; language-vs-layer confusion | Clarify: "language-specialist owns language-idiomatic patterns; backend-developer owns cross-language architecture" |
| `performance-engineer` + `database-optimizer` + `react-specialist` | All optimize; different layers | Add explicit boundary: "performance-engineer diagnoses bottleneck; layer-specialist (db/react) fixes" |
| `devops-engineer` + `deployment-engineer` + `sre-engineer` + `platform-engineer` | 4 agents on "infrastructure automation"; roles are unclear | Separate by concern: devops=pipelines; deployment=releases; sre=reliability; platform=developer experience |

### Incomplete Categories (Backlog Candidates) 📝
- **Mobile** (01): `mobile-developer` (cross-platform) exists; gap on native iOS/Android specialists
- **Data** (05): `data-engineer` (pipelines) and `dlt-engineer` (ELT) exist; no "data quality" or "governance" specialist
- **Quality** (04): Good coverage; consider "observability" specialist as complement to `performance-engineer`

---

## Part E: MECE Audit Workflow

### Step 1: Description Audit
For each agent, score dimensions 1–4 (Deliverable, Routing, Decision, Scope).
```bash
# Score each agent: 1=vague, 2=needs work, 3=clear, 4=exemplary
agent_name | deliverable | routing | decision | scope | overall | notes
```

### Step 2: Routing Test
Select 20 realistic tasks from your backlog. For each:
```
task_description | primary_agent | secondary_agent | ambiguity_flag | resolution_rule
```

If ambiguity_flag >0, add a decision rule to the agent descriptions.

### Step 3: Intra-Category Coherence
For each category, verify all agents share the same primary axis.
```
category | axis | agents | outliers | action
```

### Step 4: Cross-Category Alignment
Build a 2D matrix: agent name vs primary axis (language, framework, layer, concern, domain, etc.).
Diagonal overlaps appear as cells with >1 agent.

### Step 5: Iteration
1. Draft improved descriptions addressing overlaps
2. Re-run routing test on 5–10 ambiguous tasks
3. Document decision rules in AGENTS.md / CLAUDE.md

---

## Part F: Template for New Agents (Backlog)

When adding a new agent, answer all of Part B before writing code:

```yaml
---
name: [agent-name]
description: "[USE when [decision/artifact]. Invoke for [specific sub-tasks]. Route to [sibling agent] instead when [boundary condition].]"
tools: [list, specific, tools]
model: [sonnet|opus|haiku — same as similar agents]
category: [xx-name — which category? if new, why?]
---

## MECE Self-Check
Primary deliverable: [artifact or decision type]
Overlaps with: [list agents with same or adjacent deliverable]
Boundary rule vs. [overlapping agent]: [explicit decision rule]
Routing test (5 tasks): [can each route unambiguously?]
```

---

## Part G: Scoring Thresholds

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Description clarity (Dimension 1) | 90%+ agents score ≥3/4 | ~70% | ⚠️ Needs improvement |
| Routing test ambiguity rate | <5% of tasks ambiguous | ~15% (diagonal overlaps) | ⚠️ Fix boundaries |
| Cross-category overlap pairs | ≤3 agents per problem domain | 4–5 in DevOps/backend | ⚠️ Consolidate or clarify |
| Decision rule explicitness | 100% of overlapping pairs have rules | ~40% | ❌ Major gap |

---

## Implementation Checklist

- [ ] **Audit descriptions** using Part E, Step 1
- [ ] **Run routing test** on 20 realistic tasks (Part E, Step 2)
- [ ] **Map current overlaps** (Part D findings above)
- [ ] **Draft boundary rules** for top 5 overlapping pairs
- [ ] **Publish revised descriptions** in agents.md with decision rules
- [ ] **Test new agents** against the rubric (Part F) before merging
- [ ] **Review semi-annually** or when adding 5+ new agents

---

## References

- **MECE Principle**: Barbara Minto, McKinsey; Pyramid Principle (2009)
- **Role design**: Hollenbeck, Humphrey & Morgeson, "The Evolution of Work"
- **Multi-agent routing**: Li et al., "Intelligent Task Delegationin Multi-Agent Systems" (arXiv 2602.11865)
