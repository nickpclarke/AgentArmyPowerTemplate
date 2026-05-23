# Agent Onboarding Rubric

Operational checklist for validating new agents before merge. This rubric operationalizes ARMY_PRINCIPLES.md into specific, pass/fail criteria.

**Who uses this:** `agent-distinctiveness-advocate` (automated), architects (manual review), PR reviewers.  
**When to use:** Before merging any new agent definition file.  
**Exit criteria:** All items must be PASS for merge approval.

---

## Quick Approval Path (Green Light)

Agent gets merged immediately (no AR discussion) if it passes **ALL** of:

- ✅ Description is unique (no overlap with existing agents)
- ✅ No UP-delegation (doesn't call generalists)
- ✅ Boundary rules present and actionable (if overlap exists, rule disambiguates)
- ✅ Model tier is appropriate (complexity ↔ model size)
- ✅ Tools list is reasonable (not overly broad)

If ANY of above fail → go to full rubric (below).

---

## Full Rubric (Architecture Review Required)

### Section A: MECE (Principle 6)

**A1: Distinctiveness**
- [ ] Agent description does NOT use phrases from existing agents' descriptions
- [ ] Agent's primary scope is different from all existing agents
- [ ] If overlap exists with 1–2 agents, clear boundary rules disambiguate
- [ ] If overlap exists with 3+ agents, reconsider scope (agent may be too broad)

**A2: Boundary Rules (if applicable)**
- [ ] If similar agent(s) exist, description includes explicit "use me for X; use AgentY for Y" language
- [ ] Boundary rule is condition-based (not subjective): e.g., "if codebase exists" or "for optimization" not "when you feel"
- [ ] Similar agent's description also updated (bidirectional boundary rule)

**A3: Category Fit**
- [ ] Agent's primary domain matches its assigned category
- [ ] If agent spans multiple categories (unlikely), document why it's in THIS one
- [ ] No agent miscategorized (e.g., technical agent in Business category)

**Example (PASS):** New agent `database-cursor-optimizer` with description:
> "Optimize cursor-based pagination across PostgreSQL, MySQL, and Oracle using query analysis and index tuning. Use `database-optimizer` for generic DB tuning across systems; use `postgres-pro` for advanced PostgreSQL features beyond cursors."

**Example (FAIL):** Agent with description:
> "Optimize database performance"
> (Too similar to `database-optimizer` and `database-administrator` without boundary rule)

---

### Section B: Error & Learning (Principles 1, 2)

**B1: Error Escalation**
- [ ] Agent description mentions failure handling
- [ ] If agent can fail (most do), description includes: "On error, escalates to `error-coordinator`"
- [ ] If agent is `error-coordinator` itself, skip (it's the escalation endpoint)
- [ ] Agent body documents failure types (timeout, permission denied, external API failure, etc.)

**B2: Knowledge Feedback**
- [ ] Agent description mentions knowledge capture (or skip if agent is lightweight)
- [ ] If agent completes complex work, description includes: "Feeds insights to `knowledge-synthesizer` after task completion"
- [ ] Examples of what agent would feed back are listed (anti-patterns, performance observations, etc.)

**Example (PASS):** Backend agent:
> "On database query failures, escalates to `error-coordinator`. After successful API implementation, feeds performance observations to `knowledge-synthesizer`."

**Example (FAIL):** Agent with no mention of error handling or feedback.

---

### Section C: Delegation (Principle 5)

**C1: Delegation Direction**
- [ ] Agent does NOT delegate UP (to more-generalist agents)
- [ ] All delegation targets are listed in description
- [ ] Delegation direction is SAME-level or DOWN-the-hierarchy (specialist ← specialist, not specialist ← generalist)

**C2: No Circular Dependencies**
- [ ] Agent does not delegate to any agent that delegates back to it
- [ ] If Agent A → B → A cycle would form, reject or reroute

**C3: Delegation Clarity**
- [ ] Description lists agents this one delegates to (if any)
- [ ] Explanation given for WHY (e.g., "delegates to python-pro for backend implementation")

**Example (PASS):** Fullstack design agent:
> "Delegates to `backend-developer` for implementation, `database-optimizer` for schema design, `frontend-developer` for UI implementation. All are specialist-to-specialist delegation."

**Example (FAIL):** 
> "Delegates to `architect-reviewer` for validation"
> (UP-delegation: specialist to generalist)

---

### Section D: Skills & Hooks (Principles 3, 4)

**D1: Skill Exposure**
- [ ] If agent exposes reusable skills (e.g., CLI commands, recipes), they are documented
- [ ] Skill names follow pattern: `{agent-name}-{capability}` (e.g., `wardley-analysis`)
- [ ] Skill parameters and output format specified (for composability)
- [ ] If agent doesn't expose skills, mark "not applicable"

**D2: Hook Integration**
- [ ] If agent listens to Claude Code hooks, they are listed in description
- [ ] Common hooks: `Stop` (learning capture), `SessionStart` (context init), `PostToolUse` (logging)
- [ ] If agent doesn't use hooks, mark "not applicable"

**Example (PASS):** Wardley specialist:
> "Exposes `wardley-analysis` skill (parameters: domain, depth; output: JSON OWM syntax). Listens to `Stop` hook for learning capture."

**Example (FAIL):** Agent with no mention of skills or hooks (acceptable if lightweight, but should be noted).

---

### Section E: Model & Tools (Implementation Quality)

**E1: Model Tier Appropriateness**
- [ ] Opus agents: complex reasoning (architecture, security, strategy, cross-service orchestration)
- [ ] Sonnet agents: implementation, design, multi-step problem-solving
- [ ] Haiku agents: lightweight tasks, simple routing, fast responses
- [ ] Assignment matches agent complexity

**E2: Tools Assignment**
- [ ] Tools list is necessary and sufficient (not overly broad)
- [ ] If agent lists 10+ tools, assess if it's actually multiple agents
- [ ] Dangerous tools (Bash with shell commands) only assigned to infra/DevOps agents, with justification

**E3: No Generalist Overlap**
- [ ] If agent model is Sonnet, it is NOT a "general purpose" agent (those are rare — e.g., `claude`)
- [ ] Tools don't span unrelated domains (e.g., a React specialist shouldn't have Bash tools)

**Example (PASS):**
- `wardley-strategist`: Opus (complex reasoning), tools: Read, Write, Edit, Bash (for diagram generation)
- `python-pro`: Sonnet (implementation), tools: Read, Write, Edit, Bash

**Example (FAIL):**
- Haiku agent with Bash and GPU tools (mismatch)
- Sonnet agent listed as "general purpose backend developer" (too broad)

---

### Section F: Spoke Scalability (Principle 6 extended)

**F1: Spoke Inheritance Safe**
- [ ] Agent does NOT assume Hub repo structure (e.g., references to `.claude/agents/` should be relative)
- [ ] If agent needs Hub-specific files, it documents dependency clearly
- [ ] Agent can function in Spoke without modification

**F2: No Hard-coded Owner/Org References**
- [ ] Agent description does not hard-code `nickpclarke` or `AgentArmy` org name
- [ ] Agent names don't assume Hub context (good: `python-pro`, avoid: `hubagentarmy-python`)

**Example (PASS):** Agent describes tools relative to repo: "Validates SKILL.md frontmatter in `.claude/agents/`"

**Example (FAIL):** "Works with AgentArmy template at https://github.com/nickpclarke/AgentArmy"

---

## Scoring & Decision

### Must-Have Failures (Block Merge)

If ANY of these fail, reject the agent:

- ❌ **A1 or A2**: No boundary rules when overlap exists → MECE violation
- ❌ **B1**: No error escalation documented → fails Principle 1
- ❌ **C1**: UP-delegation exists → violates delegation hierarchy
- ❌ **C2**: Circular delegation detected → blocks execution
- ❌ **E2**: Tools list is dangerous or overly broad without justification → security/scope risk
- ❌ **E1**: Model tier mismatch (Haiku doing Opus-level reasoning, or vice versa) → quality risk

### Nice-to-Have Issues (Request Changes, May Merge)

If these fail, request improvements but allow merge if agent is otherwise valuable:

- ⚠️ **B2**: No knowledge feedback documented → learning loop not closed, but agent still functional
- ⚠️ **D1/D2**: No skills or hooks exposed → agent is OK as pure specialist
- ⚠️ **E3**: Agent is broader than peers (but not generalist) → request scope refinement in future PR

### Decision Matrix

| MECE | Error | Delegation | Tools | Model | Skills/Hooks | Decision |
|---|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **APPROVE** (Green light) |
| ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | **APPROVE** (Request enhancements in future) |
| ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | **DISCUSS** (Scope discussion, likely approve) |
| ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | **DISCUSS** (Delegation review needed) |
| ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | **DISCUSS** (Boundary rule refinement) |
| ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | **REJECT** (Rewrite without MECE violation) |
| ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | **REJECT** (Must document error handling) |
| ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | **REJECT** (Fix delegation direction) |

---

## Automated Checks (CI/CD)

The following checks run automatically on every agent PR:

```bash
# MECE overlap detection
grep -i "optimize" *.md | wc -l  # Flag if 3+ agents mention "optimize"

# Missing boundary rules
grep "use me for\|use Agent" *.md  # Warn if boundary rule not found

# UP-delegation detection
parse_delegation_targets(agent.md) | foreach target {
  if target.is_more_generalist_than(agent) {
    fail("UP-delegation detected")
  }
}

# Circular dependency detection
build_delegation_graph() | find_cycles()  # Fail if cycle found

# Model tier consistency
if model == "haiku" and tool_count > 5: fail("Haiku with too many tools")
```

These checks provide immediate feedback (no waiting for humans).

---

## Example: Full Onboarding

**New agent:** `kubernetes-specialist`

**Proposed description:**
> "Optimize Kubernetes cluster configurations and workload deployments. Handles cluster design, YAML optimization, and troubleshooting. Delegates to `cloud-architect` for multi-cloud strategy and `infrastructure-engineer` for lower-level provisioning."

**Rubric Review:**

| Section | Check | Result | Notes |
|---|---|---|---|
| **A1** | Distinctiveness | ✅ PASS | Different from `devops-engineer`, `infrastructure-engineer`, `kubernetes-expert` (hypothetical) |
| **A2** | Boundary rules | ⚠️ PARTIAL | Missing rule vs. `cloud-architect`: "use me for cluster-level optimization; use cloud-architect for multi-cloud strategy" |
| **B1** | Error escalation | ❌ FAIL | No mention of `error-coordinator` |
| **C1** | Delegation direction | ✅ PASS | Delegates to generalists appropriately (cloud-architect for strategy) |
| **D1/D2** | Skills/Hooks | ✅ PASS | Lists `kubernetes-optimization` skill; listens to `Stop` |
| **E1** | Model tier | ✅ PASS | Sonnet (complex reasoning, but implementation-focused) |
| **Decision** | **REQUEST CHANGES** | Requires: (1) boundary rule vs. cloud-architect, (2) error-coordinator reference |

**Required fixes before merge:**
1. Add to description: "On configuration errors, escalates to `error-coordinator`"
2. Add to description: "Use me for cluster optimization; use `cloud-architect` for multi-cloud strategy and `infrastructure-engineer` for provisioning"

---

## How to Use This Rubric

1. **Automated**: CI runs MECE overlap and circular dependency checks on every agent PR. Instant feedback.
2. **Manual**: `agent-distinctiveness-advocate` reviews full rubric pre-merge.
3. **Quarterly**: Architecture review runs the full rubric on all agents to identify new overlaps or drift.

---

**Last Updated:** 2026-05-23  
**Related:**
- `ARMY_PRINCIPLES.md` — principles this operationalizes
- `agent-distinctiveness-advocate` — agent that runs this rubric
- `.claude/agents/` — where agent definitions live

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
