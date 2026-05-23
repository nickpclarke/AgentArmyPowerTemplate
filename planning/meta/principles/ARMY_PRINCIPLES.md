# Army Operations Principles

Foundational axioms for how the AgentArmy agent ecosystem operates. These principles enable the whole army to function as a coherent system — not just a collection of agents.

**Status:** Established baseline (2026-05-23)  
**Review Cadence:** Quarterly (Q2, Q3, Q4, Q1)  
**Last Reviewed:** 2026-05-23  
**Approved By:** Architecture Review  

---

## Principle 1: Error Escalation to Coordinator

**Statement:** Every agent, when encountering a failure it cannot locally resolve, escalates to `error-coordinator` for distributed error analysis and recovery orchestration.

**Why this matters:** Without escalation, isolated agents fail in silence. With escalation, the army learns from failures and prevents cascades.

**How it works:**
- Agent executes task
- Failure occurs (exception, timeout, insufficient permissions, external API error)
- Agent captures failure context: what was attempted, what failed, constraints violated
- Agent invokes `error-coordinator` with failure context
- `error-coordinator` analyzes: Is this a known pattern? Is there a workaround? Does this block other agents?
- `error-coordinator` either fixes the error, escalates to human, or documents for learning

**Agent responsibility:**
- Do NOT silently return error to user
- Do NOT attempt unbounded retries
- Do NOT work around errors that suggest a deeper issue
- DO escalate failures that suggest:
  - Missing permissions or credentials
  - External API unavailable
  - Resource exhaustion
  - Configuration error
  - Unknown/unexpected state

**Governance:**
- New agents must document their failure escalation path in their description
- Agent descriptions should include: "On failure, escalates to error-coordinator"
- CI check: grep agent descriptions for "error" — if mentioned without error-coordinator reference, flag for review

---

## Principle 2: Knowledge Feedback to Synthesizer

**Statement:** Agents feed insights, patterns, and lessons learned to `knowledge-synthesizer` after completing work, enabling organizational learning.

**Why this matters:** Without feedback, each agent solves problems in isolation. With feedback, the army accumulates knowledge and improves its decision-making.

**What counts as "knowledge":**
- Anti-patterns discovered (e.g., "routing this agent instead of that one causes 10s latency")
- Success patterns (e.g., "this dependency order prevents merge conflicts")
- Data observations (e.g., "this skill was invoked 47 times, mostly for X use case")
- Incident insights (e.g., "the learning loop failed because KB was stale")
- Feedback from humans (e.g., "user said this agent's output was confusing")

**How it works:**
- Agent completes primary task
- Agent extracts relevant insights into structured KB entry
- Agent invokes `knowledge-synthesizer` with:
  - `pattern_type`: (e.g., "routing-anti-pattern", "success-pattern", "performance-insight")
  - `description`: human-readable summary
  - `evidence`: (optional) metrics, logs, reproduction steps
  - `recommended_action`: what should change as a result
- `knowledge-synthesizer` aggregates entries, identifies trends
- Quarterly principle review reads synthesized insights and updates ARMY_PRINCIPLES.md if needed

**Agent responsibility:**
- After task completion, spend 1–2 minutes documenting what you learned
- Focus on insights that would help OTHER agents (not just this task)
- Be specific: "agent X was slow" is not useful; "agent X took 30s parsing YAML" is useful
- DO feed back on: unexpected failure modes, surprising success factors, resource bottlenecks

**Governance:**
- KB entries are queryable by `knowledge-synthesizer` and visible in learning reports
- Quarterly principle review reads aggregated KB to identify principle evolution needs
- If a pattern is observed 3+ times, it triggers a principle update decision

---

## Principle 3: Skill Scaffolding & Composability

**Statement:** Agents expose reusable, versioned skill capabilities that can be combined into larger workflows without requiring re-implementation.

**Why this matters:** Without scaffolding, each specialized agent is an island. With scaffolding, agents become composable building blocks for larger solutions.

**What counts as a "skill":**
- A slash command that encapsulates a well-defined capability (e.g., `/wardley [domain]` runs full Wardley analysis)
- A documented execution pattern that other agents can invoke (e.g., `contract-test-engineer` knows how to "run full Pact verification")
- A step in a recipe (e.g., "PR review" = lint + type-check + security-scan)

**Structure:**
- Each agent category (or agent) MAY expose 1–3 skills in `/\.claude/commands/` or documented in the agent description under "Available Skills"
- Each skill has: name, parameters, expected output format
- Skills are discoverable via `agent-installer` or CLI help
- Skills can be composed into recipes (sequences of skills with data flow between them)

**Examples:**
- `security-engineer` exposes `security-scan` skill (parameters: repo path, severity threshold; output: JSON findings)
- `prompt-engineer` exposes `prompt-optimize` skill (parameters: prompt text; output: improved prompt)
- Recipes: `code-review` = `lint-skill` → `type-check-skill` → `security-scan` → `performance-analyze-skill`

**Agent responsibility:**
- Document 1–3 skills your agent provides (even if they're just CLI commands you wrap)
- Version your skills (e.g., skill v1 vs. skill v2) if behavior changes
- Ensure output format is structured (JSON, YAML) so other agents can parse it
- DO compose other agents' skills if it improves your work (don't re-implement)

**Governance:**
- New agents must document skills (if any) in their SKILL.md frontmatter
- Skill naming convention: `{agent-name}-{capability}` (e.g., `wardley-analysis`, `security-scan`)
- Skill versioning follows semver (breaking changes = v2)

---

## Principle 4: Hook Integration & Lifecycle Awareness

**Statement:** Agents listen to Claude Code session hooks and react to lifecycle events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`) to coordinate with other agents.

**Why this matters:** Without hooks, agents operate on a per-call basis. With hooks, agents can maintain context across the session, validate preconditions, and capture learnings at session end.

**Hook types available:**

| Hook | When | Agent Use Case |
|---|---|---|
| `SessionStart` | Session initialized | Initialize agent-specific context, load KB, check permissions |
| `UserPromptSubmit` | User submits prompt | Validate prompt routing, inject context graph, suggest better agent |
| `PreToolUse` | Before a tool executes | Validate tool invocation, check permissions, inject secrets |
| `PostToolUse` | After tool completes | Log tool behavior, track execution metrics, feed back to KB |
| `Stop` | Session ends | Capture incident if failure, extract lessons, update KB |

**How it works:**
- Session starts → `SessionStart` fires for all agents that have registered listeners
- User submits prompt → `UserPromptSubmit` fires; agents can evaluate routing fitness
- Tool is about to execute → `PreToolUse` fires; agents can validate/inject context
- Tool finishes → `PostToolUse` fires; agents can observe results
- Session ends or user stops → `Stop` fires; agents extract lessons and feed to KB

**Agent responsibility:**
- Declare which hooks you listen to in your agent definition: `hooks: ["Stop"]` (for learning capture)
- If you listen to `Stop`, implement incident capture: "did the task fail? what was the failure?"
- If you listen to `PreToolUse`, validate the tool invocation (security, permissions, sanity)
- If you listen to `SessionStart`, initialize your context (KB state, cached decisions)

**Governance:**
- Agent definitions must document hooks in a `hooks:` field (if applicable)
- `error-coordinator` must listen to `Stop` hook to capture failures
- `knowledge-synthesizer` must listen to `Stop` hook to extract learnings
- Core agents that should NOT listen to hooks: language specialists, infrastructure engineers (low benefit)

---

## Principle 5: Delegation Direction & Circular-Dependency Prevention

**Statement:** Agents delegate DOWN the hierarchy (from generalist to specialist) or ACROSS to peers of equal scope. Never UP (specialist to generalist). No circular delegation.

**Why this matters:** Without delegation discipline, agents create call loops, split responsibilities, and fail unpredictably. With direction, delegation is a clear signal of task reframing.

**Delegation directions:**

```
Design-time specialists (architect-reviewer, api-designer, solution-architect)
  ↓ delegate to
Implementation specialists (backend-developer, frontend-developer, etc.)
  ↓ delegate to
Language specialists (python-pro, golang-pro, etc.)
  ↓ delegate to
(No further delegation; language specialists are leaves)

Orchestrators (multi-agent-coordinator, codebase-orchestrator, enterprise-architect)
  ↓ delegate to
Any specialist (via explicit routing)

(Specialists do NOT delegate UP to orchestrators)
```

**Allowed delegation patterns:**
- ✅ Architect → Implementation specialist (different scope)
- ✅ Backend specialist → Python specialist (same feature, different layer)
- ✅ Orchestrator → Any agent (orchestrators have god's-eye view)
- ✅ Agent → error-coordinator on failure (escalation, not delegation)

**Disallowed patterns:**
- ❌ Python specialist → Architect (UP the hierarchy)
- ❌ Agent A → Agent B → Agent A (circular)
- ❌ Two agents both delegating to each other

**How it works:**
- When Agent A needs Agent B's capability, Agent A checks: "Is B at a deeper/different scope than me?"
- If yes, delegate: "Hey B, can you handle the Python implementation?"
- If no, re-assess the task split

**Agent responsibility:**
- Document your delegation targets in your description
- Never delegate UP (to a more-generalist agent)
- If you're delegating to multiple agents, ensure they don't form a loop

**Governance:**
- `codebase-orchestrator` audits delegation graphs to prevent cycles
- New agent descriptions must list delegation targets (if any)
- CI check: parse agent descriptions for delegation; flag if circular or UP-delegation

---

## Principle 6: Non-Overlapping Responsibility Zones (MECE)

**Statement:** Each agent occupies a distinct, non-overlapping responsibility zone. If two agents can both handle the same task, there is a boundary rule that disambiguates routing.

**Why this matters:** Without MECE, routing is ambiguous. With MECE, users and automations can route with high confidence.

**How it works:**
- Agent definitions must include boundary rules in the description: "use me for X; use AgentY for Y"
- Boundary rules must be actionable: condition-based ("if the codebase already exists..."), not vague
- Overlap is documented in centralized taxonomy (TAXONOMY.md per category) and propagated back to agent descriptions

**Current defects identified in audit:**
- `debugger` vs `error-detective`: Both descriptions say "diagnose failures" with no boundary rule
- `mobile-developer` vs `mobile-app-developer`: Two agents, nearly identical descriptions
- `database-administrator` vs `database-optimizer` vs `postgres-pro`: Three agents, overlapping "optimize" language

**Fix (in progress):**
All boundary rules are being propagated back to agent descriptions. Example from `devops-engineer` (the gold standard):
> "Owns the pipelines and platform; use `deployment-engineer` for release/rollout strategy (canary, blue-green, rollback)"

**Agent responsibility:**
- Your description must include a "use me when..." clause
- If there is a similar agent, your description must reference it with a clear boundary rule
- Example template: "Use me for X (condition A); use AgentY for X (condition B)"

**Governance:**
- Every new agent must pass MECE audit before merge
- `agent-distinctiveness-advocate` runs pre-merge validation
- Quarterly principle review audits for new overlaps in the roster

---

## Principle 7: Observable Decision-Making

**Statement:** Agents log their routing decisions, tool selections, and reasoning in a structured, queryable format that enables post-hoc analysis and feedback.

**Why this matters:** Without observability, we don't know why agents make decisions. With observability, we can debug misrouting, identify training opportunities, and tune agent selection.

**What gets logged:**
- **Route decision**: "User asked for X; I routed to Agent Y because condition Z"
- **Tool selection**: "Task requires API integration; I selected tool Z over alternatives"
- **Reasoning**: "I chose Agent Y over Agent Z because..."
- **Confidence**: routing decision confidence (high/medium/low)

**Format:** Structured logging (JSON with fields: timestamp, agent, decision_type, decision, reasoning, confidence)

**How it flows:**
- All routing decisions → observability system (via PostToolUse hook or direct log)
- Queries enable: "Which routing decisions had low confidence?" "Which agents are frequently delegated to?"
- Learning loop: unexpected-decision patterns → principle review → principle/training update

**Agent responsibility:**
- If you make a routing decision (choosing another agent), log it: agent name, reason, confidence
- If you're uncertain, mark confidence as "medium" or "low"

**Governance:**
- Observability is instrumented at the architecture level (not per-agent)
- `observability-engineer` owns the logging infrastructure
- Decision logs are queryable by learning loop automation

---

## Application: Agent Onboarding Checklist

When onboarding a new agent, validate:

- [ ] **Principle 1**: Describe failure escalation path (if any); reference `error-coordinator`
- [ ] **Principle 2**: Document what insights you feed back to `knowledge-synthesizer`
- [ ] **Principle 3**: Document any skills/recipes you expose
- [ ] **Principle 4**: Declare hooks you listen to (if any)
- [ ] **Principle 5**: List delegation targets (if any); no UP-delegation; no circular
- [ ] **Principle 6**: Include boundary rules in description; reference similar agents
- [ ] **Principle 7**: Ensure decision-making is observable/loggable

---

## Application: Spoke Inheritance

When a Spoke forks AgentArmy, it inherits these principles. Spoke-specific customization:

1. **Principle 1** (Error Escalation): Spokes MAY add spoke-specific error handlers; all must ultimately escalate to `error-coordinator`
2. **Principle 2** (Knowledge Feedback): Spokes MAY have layer-specific KB topics (e.g., "UI layer incident patterns"); same feedback pattern
3. **Principle 3** (Skill Scaffolding): Spokes MAY add layer-specific skills; naming convention: `myapp-{layer}-{skill}`
4. **Principle 4** (Hooks): Same hook types available; spokes MAY add custom hook listeners
5. **Principle 5** (Delegation): Spokes MUST respect Hub delegation direction; MAY add spoke-local delegation between new agents
6. **Principle 6** (MECE): Spoke agents MUST not overlap with Hub MECE; internal spoke MECE audited locally
7. **Principle 7** (Observability): All spoke decisions logged to same observability infrastructure (via shared logging)

---

## Revision History

| Date | Change | Approved By |
|---|---|---|
| 2026-05-23 | Initial establishment (7 principles) | Architecture Review |

---

**Last Updated:** 2026-05-23  
**Next Scheduled Review:** Q3 2026 (after RT2 completion)  
**Feedback:** File an issue with tag `principle-review` to propose updates

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
