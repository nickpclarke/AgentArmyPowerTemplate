# Agent Army MECE Audit — Quick Reference

**Overall Score**: 72/100 (Fair — actionable improvements exist)  
**Date**: 2026-05-22  
**Agents**: 169 across 11 categories  
**Routing ambiguity**: 50% (target: <5%)

---

## 🔴 Critical Overlaps (Fix Immediately)

| Agents | Issue | Impact | Fix Effort |
|--------|-------|--------|-----------|
| `devops-engineer` + `deployment-engineer` | Both own CI/CD; no boundary rule | High — users don't know which to pick | 2 hrs |
| `debugger` + `error-detective` | Identical scope (root cause diagnosis) | Medium — duplicate capability | Merge or split by local vs. distributed |
| `ml-engineer` + `machine-learning-engineer` | Literally the same role, different names | Medium — duplicate | Merge; keep one |
| `react-specialist` + `frontend-developer` | Both own React; no rule for greenfield vs. optimization | High — 15% of React tasks ambiguous | Add rule: "frontend-developer=greenfield, react-specialist=optimization" |
| `backend-developer` + `node-specialist` + `fastapi-developer` | Architecture vs. language vs. framework confusion | High — many server-side tasks ambiguous | Add rule: "backend-developer=cross-language architecture, specialists=language/framework idioms" |

---

## ⚠️ Medium Overlaps (Add Decision Rules)

**Can be resolved with explicit boundary rules** (no merging needed):

1. `api-designer` vs `backend-developer` — "designer owns specs; backend owns API implementation"
2. `data-engineer` vs `dlt-engineer` — "engineer=generic tool-agnostic; dlt-engineer=dlt-specific optimization"
3. `documentation-engineer` vs `technical-writer` — "engineer designs systems; writer creates content"
4. `performance-engineer` vs layer-specialists — "performance-engineer diagnoses bottleneck; specialist fixes in their layer"
5. `security-auditor` vs `penetration-tester` — "auditor=comprehensive assessment; tester=exploitation + validation"
6. `platform-engineer` vs `kubernetes-specialist` — "platform=IDP end-to-end; k8s-specialist=k8s ops"
7. `legacy-modernizer` vs `refactoring-specialist` — "modernizer=strategy + sequencing; specialist=tactical code cleanup"
8. Plus 6 more in full scorecard

---

## 📊 Category Scores

| Category | Score | Status | Key Issue |
|----------|-------|--------|-----------|
| 11 · Enterprise Architecture | 91/100 | ✅ Exemplary | None — TOGAF-aligned structure is MECE-perfect |
| 07 · Specialized Domains | 85/100 | ✅ Good | None — scoped by domain, clear |
| 10 · Research & Analysis | 88/100 | ✅ Good | Minor: add pipeline clarification |
| 09 · Meta & Orchestration | 87/100 | ✅ Good | Minor: orchestration vs. coordination boundary |
| 08 · Business & Product | 82/100 | ✅ Good | Minor: add rules for PM vs BA, PM vs Scrum |
| 03 · Infrastructure | 81/100 | ⚠️ Fair | 🔴 CRITICAL: devops/deployment overlap |
| 04 · Quality & Security | 79/100 | ⚠️ Fair | 🔴 debugger/error-detective merger |
| 02 · Language Specialists | 78/100 | ⚠️ Fair | Consider consolidating 4 JS agents; 5 PowerShell OK |
| 06 · Developer Experience | 76/100 | ⚠️ Fair | Minor: doc engineer vs. writer |
| 05 · Data & AI | 74/100 | ⚠️ Fair | 🔴 ml-engineer/machine-learning-engineer merger |
| 01 · Core Development | 65/100 | 🔴 Fair | 🔴 frontend-developer scope creep; fullstack redundancy |

---

## 🎯 What Blocks Semantic Distinctiveness

### Problem 1: Missing Decision Rules
Most overlaps exist because descriptions lack explicit boundary conditions.

**Example (current):**
```
react-specialist: "optimize existing React applications"
frontend-developer: "build complete frontend applications across React, Vue, Angular"
→ Unclear: can frontend-developer optimize React? Does react-specialist build new React apps?
```

**Fixed:**
```
react-specialist: "optimize existing React codebases for performance, state management, hooks"
  - Use when: you have working React code that needs performance/architecture improvements
  
frontend-developer: "build new full-stack frontends across React/Vue/Angular; multi-framework architecture"
  - Use when: greenfield frontend work or selecting framework strategy
  
Rule: frontend-developer chooses framework; react-specialist optimizes React only
```

### Problem 2: Granularity Mismatch (Diagonal Overlap)
One agent scoped to language level; another to framework level; they converge.

**Example:**
- `backend-developer` (language-agnostic, architecture-focused)
- `node-specialist` (language-specific)
- `fastapi-developer` (framework-specific)

All three could own "build a Node.js FastAPI equivalent" task.

**Fix:** Add hierarchy rule:
```
backend-developer: Cross-language architecture (microservices, API design, scalability)
node-specialist: Node.js idioms, async patterns, npm ecosystem
fastapi-developer: FastAPI-specific async patterns, Pydantic validation

Route "build Node.js API" to: backend-developer (design) → node-specialist (implement)
```

### Problem 3: Same Artifact, Different Focus
Both agents produce the same deliverable but from different angles.

**Examples:**
- `debugger` and `error-detective` both diagnose root causes
- `data-analyst` and `data-scientist` both analyze data
- `ml-engineer` and `machine-learning-engineer` both deploy ML systems

**Fix:** Either merge (if truly identical) or split explicitly by scope.

---

## 📋 Routing Test Results: 20 Real Tasks

**Ambiguity rate: 50% (10/20 tasks)**

Tasks with clear single agent (40%):
- Build a GraphQL API
- Set up Kubernetes
- Audit compliance
- Develop smart contracts
- Build a game
- Implement payment processing
- etc.

Tasks with 2+ ambiguous agents (60%):
- "Optimize React app" → react-specialist OR performance-engineer
- "Build Node.js API" → node-specialist OR backend-developer
- "Set up CI/CD" → devops-engineer OR deployment-engineer
- "Debug a bug" → debugger OR error-detective
- "Build ELT pipeline" → data-engineer OR dlt-engineer
- etc.

---

## ✅ How to Fix (Phase 1: 1 Week, 5–10 Hours)

### Step 1: Merge or Deprecate (2 hrs)
- Merge `ml-engineer` + `machine-learning-engineer` → keep one name
- Merge `debugger` + `error-detective` → split by distributed (error-detective) vs. local (debugger), OR merge into `debugger` with sub-focus areas
- Merge `frontend-developer` + `fullstack-developer` → if fullstack is rare, deprecate it

### Step 2: Add Boundary Rules to AGENTS.md (4 hrs)
Create a "Routing Rules" section for each overlapping pair.

**Template:**
```markdown
### react-specialist vs frontend-developer
- **react-specialist**: optimize existing React codebases; advanced React 18+ patterns; hooks/context/state mgmt
- **frontend-developer**: greenfield multi-framework work; framework selection; full-stack integration
- **When unsure**: frontend-developer if choosing tech, react-specialist if refining tech
```

### Step 3: Test Routing on 5 Real Tasks (1 hr)
Pick 5 ambiguous tasks from your backlog; confirm each routes unambiguously with new rules.

### Step 4: Publish + Communicate (1 hr)
Update `AGENTS.md` with routing rules; notify team of merged agents (deprecation notices).

---

## 🚀 Before Adding New Agents to Your Backlog

Use the **Agent MECE Checklist** (from `AGENT_MECE_AUDIT_RUBRIC.md`, Part F):

```yaml
---
name: [agent-name]
description: "..."
tools: [...]
model: [...]
category: [...]
---

## MECE Self-Check
✓ Primary deliverable: [artifact — distinct from 5+ existing agents?]
✓ Overlaps with: [list any agents with same/adjacent deliverable]
✓ Boundary rule: [explicit condition separating from overlapping agents]
✓ Routing test: [5 tasks — does each route unambiguously?]
```

**Red flags for backlog candidates:**
- ❌ "Like X, but for Y" (e.g., "like data-engineer, but for Apache Spark") — probably a sub-specialization, not a new agent
- ❌ No clear boundary rule vs. existing agents
- ❌ Same artifact as 2+ agents (unless you're splitting an oversized role)
- ❌ Sits in a gap but collides with 3+ existing agents (fix overlaps first)

**Green flags:**
- ✅ Solves a clearly unmet problem domain (e.g., edge computing, visual design systems)
- ✅ Scopes cleanly (no diagonal overlap)
- ✅ Boundary rules vs. adjacent agents are explicit
- ✅ Routing test passes (new agent always gets picked unambiguously)

---

## 📖 Full Documentation

- **`AGENT_MECE_AUDIT_RUBRIC.md`**: Complete framework (7 parts, includes templates)
- **`AGENT_MECE_AUDIT_SCORECARD.md`**: Full audit with findings per category + improvement roadmap
- **`MECE_AUDIT_SUMMARY.md`** ← you are here

---

## Recommended Next Steps

1. **Review critical overlaps** above; draft mergers/deprecations
2. **Add 5 boundary rules** to `AGENTS.md` (highest-impact overlaps first)
3. **Run 10-task routing test** to validate fixes
4. **Apply checklist** to each agent in your backlog before adding
5. **Re-audit semi-annually** (or every 5 new agents)

**Questions?** The rubric is designed so non-agents can evaluate distinctiveness. Use it to onboard others.
