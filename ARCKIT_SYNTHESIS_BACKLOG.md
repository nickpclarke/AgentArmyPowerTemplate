# ArcKit-Informed AgentArmy Backlog Synthesis
## Integrating Enterprise Architecture Patterns into the Template Platform

---

## Executive Summary

ArcKit's approach to enterprise architecture governance provides three critical innovations that dramatically strengthen AgentArmy's template platform strategy:

1. **Hook-Driven Automation** — Every user prompt triggers context injection, validation, and provenance tracking. This is the infrastructure for Play 4 (Learning Loop).
2. **Project Context Graph** — Bidirectional dependency index injected on every session. Enables impact analysis, stale detection, orphan finding, and intelligent routing.
3. **Artifact Lifecycle Management** — Machine-readable manifest.json + multi-rendering (OWM primary / Mermaid secondary) = single source of truth + multiple audience formats.

These patterns apply directly to AgentArmy's routing, choreography, cost transparency, and especially the learning loop — transforming the 4 release trains from "document delivery" to "intelligent, self-healing platform."

---

## 1. Hook System Integration

ArcKit's hook architecture maps cleanly onto AgentArmy's routing & orchestration needs.

### Release Train 1: Foundation & Routing (Jun–Jul)

**New Feature: Claude Code Hook System for Template Platform**

| Hook | Trigger | AgentArmy Use Case | ArcKit Reference |
|------|---------|---|---|
| **SessionStart** | Session begins | Initialize routing graph, load board state | `arckit-session` |
| **UserPromptSubmit** | Every prompt | (1) Inject project context + routing edges, (2) validate routing intent, (3) detect if prompt mentions cost/tracing | `arckit-context` + `secret-detection` |
| **PreToolUse** | Before Write/Edit | Validate issue naming convention (must be linked to RT/Feature), check if change impacts multiple release trains | `validate-arc-filename` + `file-protection` |
| **PostToolUse** | After Write/Edit | Emit board-sync event; update `manifest.json`; trigger impact analysis | `update-manifest` + `PostToolUse` |
| **Stop** | Session ends | Log routing outcomes, agent performance SLIs, learning loop feedback | `session-learner` |

**Size:** L (hook infrastructure + config.toml wiring)  
**Routing:** `devops-engineer` (hooks/automation) + `tooling-engineer` (skill integration)

---

### Release Train 2: Operations & Quality (Jul–Aug)

**New Feature: Project Context Graph Injection**

Extends Play 4 (Learning Loop) with infrastructure that ArcKit uses for impact analysis:

```javascript
// Injected on every UserPromptSubmit:
ProjectContextGraph {
  currentScope: "Release Train N, Feature M, Story X",
  relatedIssues: [issues with bidirectional edges],
  staleArtifacts: [items not updated in 30+ days],
  orphanedIssues: [not linked to a Feature or RT],
  impactRadius: {
    direct: [immediately affected items],
    transitive: [indirectly affected via dependencies],
    estimate: "cost to rebase / re-review"
  }
}
```

**Size:** M (graph building + edge traversal)  
**Routing:** `architect-reviewer` (graph design) + `observability-engineer` (impact metrics)

---

### Release Train 3: Spoke Readiness (Aug–Oct)

**New Feature: Artifact Lifecycle & Manifest.json**

Replaces ad-hoc artifact tracking with machine-readable manifest:

```json
{
  "projects": {
    "rt-1": {
      "status": "released",
      "features": [
        {
          "id": "routing-policy-engine",
          "type": "feature",
          "createdDate": "2026-06-01",
          "lastModified": "2026-07-15",
          "status": "done",
          "size": "M",
          "health": "active",
          "depends_on": ["agent-specs-template"],
          "mentions_cost": false,
          "mentions_tracing": true
        }
      ]
    }
  }
}
```

**Size:** M (manifest schema + PostToolUse hook)  
**Routing:** `documentation-engineer` (schema design) + `devops-engineer` (automation)

---

## 2. Multi-Rendering Strategy (Dual Output)

ArcKit's primary/secondary rendering pattern (OWM → create.wardleymaps.ai | Mermaid wardley-beta) applies to **all major artifacts**, not just Wardley maps.

### Pattern: Every "Strategic" Artifact Gets Dual Format

| Artifact | Primary Format | Secondary Format | When to Use |
|---|---|---|---|
| Wardley Map | OWM (create.wardleymaps.ai) | Mermaid `wardley-beta` + sourcing markers | Strategic landscape, evolution positioning |
| Release Train Roadmap | Markdown narrative + structured YAML | Mermaid Gantt + dependency graph | Timeline, dependencies, play sequencing |
| Feature Decomposition | GitHub issue hierarchy + acceptance criteria | Mermaid flowchart + capability tree | Scope definition, choreography design |
| Decision Record | MADR v4.0 narrative | Mermaid decision flow diagram | Architecture decisions, trade-offs |
| Routing Policy | YAML machine-readable rules | Mermaid decision tree diagram | Routing logic, ambiguity resolution |

**Implementation in Release Train 1/2:**
- Template for each artifact type (markdown primary + script to generate secondary)
- Hook that auto-generates Mermaid secondary from structured primary
- Both formats committed (primary is source of truth; secondary is audience-specific view)

**Size:** M (templates + generation scripts)  
**Routing:** `documentation-engineer` (template design) + `tooling-engineer` (generation)

---

## 3. Skill System Enhancement

ArcKit has 128+ skills with standardized SKILL.md frontmatter. AgentArmy's 11 agent categories should become **modular skills** that compose into **Skill Recipes** (like ArcKit's command-chaining).

### New Structure: Skills + Recipes

**Skill Metadata (frontmatter):**
```yaml
---
name: agent-routing-policy-engine
description: "Build executable routing policy from CLAUDE.md table"
category: "02-language-specialists / meta-orchestration"
prerequisites: ["wardley-map", "agent-specs"]
estimated_duration: "3-5 days"
model_recommendation: "Sonnet (routing needs reasoning)"
token_budget: "50k-100k"
success_metrics:
  - "Routing is deterministic and testable"
  - "No routing ambiguity > 2% of tasks"
  - "Audit trail shows reasoning"
---
```

**Skill Recipes (ArcKit pattern):**
```yaml
recipe: "template-platform-foundation"
skills:
  - agent-distinctiveness-advocate [audit existing agents]
  - wardley-strategist [map the landscape]
  - architect-reviewer [design policy engine]
  - tooling-engineer [build executor]
  - observability-engineer [instrument telemetry]
sequence: "linear (each depends on prior)"
estimated_total: "6 weeks"
rollback_strategy: "each skill is independently revertible"
```

**Size:** M (skill taxonomy + recipe system)  
**Routing:** `architect-reviewer` (skill design) + `tooling-engineer` (composition)

---

## 4. Learning Loop Infrastructure (Play 4 Enhancement)

ArcKit's `session-learner` hook (Stop event) inspires AgentArmy's learning loop:

### Enhanced Learning Loop Architecture

**On every session end:**
1. **Emit learning event** via Stop hook with:
   - What was delegated (task, estimated cost, agent(s) used)
   - What succeeded / failed
   - Rework rate (% of tasks that came back for revision)
   - Cost vs. estimate (token budget vs. actual)
   - Routing decision rationale (why this agent?)

2. **Accumulate in Knowledge Base:**
   ```json
   {
     "incidents": [
       {
         "date": "2026-07-15",
         "delegated_task": "create-routing-policy-engine",
         "assigned_to": ["architect-reviewer", "tooling-engineer"],
         "estimated_cost": "100k tokens",
         "actual_cost": "87k tokens",
         "rework_rate": 0.15,
         "root_causes": [
           "missing context on agent definitions",
           "scope creep on acceptance criteria"
         ],
         "remedy": "updated agent-specs template to include routing-policy signature",
         "impact": "next 3 similar tasks reduced rework by 40%"
       }
     ],
     "anti_patterns": [
       "delegating to single-agent when task spans 2+ agent categories",
       "not binding story acceptance criteria to routing policy"
     ],
     "competency_trends": {
       "architect-reviewer": {
         "tasks_completed": 12,
         "success_rate": 0.92,
         "avg_rework_cycles": 1.3,
         "trend": "improving (was 1.8 on first 3 tasks)"
       }
     }
   }
   ```

3. **Close the feedback loop:**
   - Every 2 weeks: pattern analysis (`knowledge-synthesizer` agent)
   - Update prompts/routing rules based on lessons
   - Publish "lessons from this sprint" to team

**Size:** L (infrastructure + telemetry schema + analysis)  
**Routing:** `knowledge-synthesizer` + `observability-engineer` + `prompt-engineer`

---

## 5. Enhanced Backlog Structure (All Release Trains)

### New Backlog Conventions (Borrowed from ArcKit)

**Every issue gets:**
1. **Artifact ID** — RT-1-FEAT-001 format (Release Train, Feature #)
2. **Health Status** — active | draft | stale | orphaned (auto-tagged via hook)
3. **Cost Metadata** — estimated tokens, model recommendation, external dependencies
4. **Traceability** — parent Feature/Epic + related decisions (ADRs), research, vendor evaluation
5. **Manifest Entry** — auto-added to manifest.json on creation (PostToolUse hook)

**Epic Example:**
```markdown
# RT1-EPIC-001: Foundation & Routing (Release Train 1)

## Metadata
- Status: in-progress
- PI: PI-1
- Type: Epic
- Size: L (sum of children)
- Health: active
- Cost: ~300k tokens (estimated)
- Model: Opus/Sonnet mix
- Depends On: [none]
- Enables: RT2-FEAT-*, Play 2, Spoke Init

## Features (Children)
- RT1-FEAT-001: Agent Spec Template + Capability Matrix
- RT1-FEAT-002: Executable Routing Decision Tree (YAML)
- RT1-FEAT-003: Claude Code Hook System
- RT1-FEAT-004: Telemetry Instrumentation (OTel spans)
- RT1-FEAT-005: Few-Shot Prompt Library Phase 1

## Acceptance Criteria
- [ ] All features merged
- [ ] Routing policy testable (>90% deterministic)
- [ ] Telemetry shows >500 calls instrumented
- [ ] No routing ambiguity > 5% of tasks
- [ ] Learning loop infrastructure ready for RT2

## Related Artifacts
- ADR-001: Why policy-engine over static table
- Wardley Map: Platform evolution landscape
- RFC-001: Hook system design
```

---

## 6. Enhanced Release Train Descriptions

### Release Train 1: Foundation & Routing (Jun 1 – Jul 12)
**Theme:** Make platform intelligence explicit; instrument everything.

**ArcKit Integration:**
- ✅ Hook system for UserPromptSubmit (context injection)
- ✅ PreToolUse validation of artifact naming (ARC-pattern)
- ✅ Project context graph injected on every prompt
- ✅ Manifest.json machinery ready
- ✅ Telemetry spans for every delegation decision

**New Features (Total: 5)**
1. Agent Spec Template + Capability Matrix
2. Executable Routing Decision Tree (YAML + validator)
3. **[NEW]** Claude Code Hook System (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop)
4. **[NEW]** Project Context Graph Injection
5. Telemetry Instrumentation (OTel spans, cost tracking)
6. Few-Shot Prompt Library (Phase 1)

**Outcome:** Routing is testable, observable, auditable.

---

### Release Train 2: Operations & Quality (Jul 12 – Aug 23)
**Theme:** Formalize handoffs; close the learning loop.

**ArcKit Integration:**
- ✅ Artifact lifecycle (PreToolUse validation + PostToolUse stamping)
- ✅ Manifest.json auto-maintained
- ✅ Multi-rendering templates (primary + secondary formats)
- ✅ Impact analysis powered by project context graph

**New Features (Total: 5 + carry-forward)**
1. Multi-Agent Choreography (Saga patterns, state machines)
2. Agent Evaluation Gates (DoD rubrics, SLI/SLO)
3. Skill Scaffolding & Composition
4. **[NEW]** Learning Loop Runtime (error-coordinator + knowledge-synthesizer)
5. **[NEW]** Artifact Manifest & Multi-Rendering Templates
6. Cost Visibility & Provider Abstraction (Helicone integration)

**Outcome:** Failures are teachable; artifacts are discoverable.

---

### Release Train 3: Spoke Readiness (Aug 23 – Oct 4)
**Theme:** Spoke teams self-serve; context travels with them.

**ArcKit Integration:**
- ✅ Manifest.json drives spoke onboarding (what artifacts are needed)
- ✅ Project context graph embedded in spoke template
- ✅ Routing policy exported as JSON + Mermaid diagram for spoke adaptation

**New Features (Total: 4 + carry-forward)**
1. Hub→Spoke Onboarding Playbook (checklists, hooks, pre-commit validation)
2. Cost & Capacity Model (unit economics, showback)
3. **[NEW]** Artifact Manifest Export (spoke gets manifest.json + all templates)
4. Observability Dashboard (MTTR, success rate, cost per delegation)
5. Spoke-Specific Prompt Adaptation (greenfield vs. legacy)

**Outcome:** Spoke can initialize with full context.

---

### Release Train 4: Learning & Advanced Observability (Oct 4 – Nov 15)
**Theme:** Accumulate and share lessons; iterate on routing.

**ArcKit Integration:**
- ✅ Stop hook feeds lesson-learned KB
- ✅ Competency trends auto-calculated from telemetry
- ✅ Anti-patterns library emerges from incident analysis

**New Features (Total: 4 + carry-forward)**
1. Agent Lesson-Learned KB (incident log, anti-patterns library)
2. **[NEW]** Request Tracing & Decision Audit Log (end-to-end visibility)
3. **[NEW]** Feedback Integration (PR reviews → routing/prompt refinement)
4. Competency Evolution Tracking (agent performance trends)

**Outcome:** Platform learns from its own use.

---

## 7. ArcKit Patterns Mapping to AgentArmy

| ArcKit Pattern | AgentArmy Analog | Release Train | Benefit |
|---|---|---|---|
| Hook system (SessionStart/Stop) | Agent lifecycle (initialize/finalize) | RT1 | Automate context setup, learning capture |
| UserPromptSubmit context injection | Routing graph injection | RT1 | Every prompt has full routing context |
| PreToolUse validation | Issue naming + traceability validation | RT1 | Prevent orphaned work |
| PostToolUse manifest update | Board sync + artifact index | RT1-3 | Single source of truth |
| Project context graph | Release train dependency graph | RT2 | Impact analysis, stale detection |
| Multi-rendering (OWM + Mermaid) | Primary artifact + secondary views | RT2 | Different audiences, same source |
| Artifact lifecycle metadata | Issue health + cost tracking | RT1-3 | Governance + financial visibility |
| Session-learner Stop hook | Learning loop telemetry | RT4 | Closed feedback loop |
| Skill + Recipe system | Agent categories + composition | RT2-3 | Reusable patterns, skill discovery |

---

## 8. Implementation Roadmap (By Week)

### RT1: Foundation & Routing (Weeks 1–6)

| Week | Feature | Dependencies | Deliverable |
|---|---|---|---|
| 1–2 | Agent Spec Template + Capability Matrix | None | Template doc + validation schema |
| 2–3 | Routing policy engine (YAML + validator) | Agent specs | `routing-policy.yaml` + test suite |
| 3–4 | Hook system wiring (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop) | Routing policy | `hooks.json` + hook implementations |
| 4–5 | Project context graph injection | Routing policy + hooks | Graph injected on every UserPromptSubmit |
| 5–6 | Telemetry instrumentation (OTel spans) | Hooks + context graph | Spans emitted for every delegation |
| 1–6 (concurrent) | Prompt library Phase 1 | Agent specs | Few-shot examples per category |

**Validation Gate:** All 5 features merged; no new issues filed without RT-X-FEAT linking.

---

### RT2: Operations & Quality (Weeks 7–12)

| Week | Feature | Dependencies | Deliverable |
|---|---|---|---|
| 7–8 | Multi-Agent Choreography | Routing policy | Saga patterns + state machines (YAML) |
| 8–9 | Agent Evaluation Gates + rubrics | Choreography | DoD matrix + SLI/SLO framework |
| 9–10 | Skill scaffolding & recipes | Agent registry | Skill SKILL.md template + recipe schema |
| 10–11 | Learning Loop runtime | Evaluation gates | error-coordinator + knowledge-synthesizer ops |
| 11–12 | Artifact manifest + multi-rendering | Learning loop | `manifest.json` schema + template generation |
| 11–12 (concurrent) | Cost visibility integration | None | Helicone adapter + estimate surface |

**Validation Gate:** Learning loop processes ≥10 incident records; manifest.json auto-generated on every artifact Write.

---

### RT3: Spoke Readiness (Weeks 13–18)

| Week | Feature | Dependencies | Deliverable |
|---|---|---|---|
| 13–14 | Onboarding playbook + hooks | Manifest schema | Checklist + pre-commit hook suite |
| 14–16 | Cost model + capacity planning | Cost visibility | Unit economics calculator |
| 16–17 | Manifest export for spokes | Artifact manifest | Spoke template includes manifest.json |
| 17–18 | Observability dashboard | Telemetry + cost | MTTR + cost-per-delegation visualization |
| 13–18 (concurrent) | Spoke prompt adaptation | Prompt library Phase 1 | Greenfield vs. legacy prompt variants |

**Validation Gate:** ≥1 spoke instantiated with full manifest + hooks running.

---

### RT4: Learning & Intelligence (Weeks 19–24)

| Week | Feature | Dependencies | Deliverable |
|---|---|---|---|
| 19–20 | Lesson-Learned KB structure | Learning loop | Incident schema + anti-patterns taxonomy |
| 20–21 | Request tracing (end-to-end) | Telemetry + hooks | Tracing spans from issue → route → PR → merge |
| 21–22 | Feedback integration | Tracing + KB | PR comments → routing/prompt rules update |
| 22–24 | Competency evolution tracking | All telemetry | Agent performance trends + self-healing |

**Validation Gate:** Platform has ≥50 incident records; competency trends show agent X improved Y% on task Z.

---

## 9. Cost & Capacity Estimate (With ArcKit Patterns)

| Release Train | Duration | Team | Agent Routing | Notes |
|---|---|---|---|---|
| **RT1** | 6 weeks | 3.0 FTE | architect-reviewer, observability-engineer, tooling-engineer, prompt-engineer | Hook system is new complexity but enables everything downstream |
| **RT2** | 6 weeks | 3.5 FTE | workflow-orchestrator, observability-engineer, knowledge-synthesizer, tooling-engineer, prompt-engineer | Learning loop runtime requires careful design |
| **RT3** | 6 weeks | 2.5 FTE | platform-engineer, finops-engineer, prompt-engineer, observability-engineer | Spoke validation gates capacity |
| **RT4** | 6 weeks | 2.0 FTE | knowledge-synthesizer, observability-engineer, prompt-engineer | Continuous improvement cycle |
| **Total** | 24 weeks (6 months) | ~2.75 FTE avg | 15–20 agents across 4 categories | ArcKit patterns add ~15% overhead but enable 40%+ faster learning cycle |

---

## 10. Success Criteria (Enhanced with ArcKit Metrics)

### RT1
- ✅ Routing policy is deterministic (>90% of decisions match policy)
- ✅ Telemetry spans emitted for ≥500 delegations
- ✅ Zero orphaned issues (all linked to RT/Feature)
- ✅ Manifest.json auto-generated on artifact creation
- ✅ **[NEW]** Project context graph injected on every prompt (>95% injection success)
- ✅ **[NEW]** Hook system stable (zero timeouts, <5ms overhead)

### RT2
- ✅ Learning loop closes: failures → KB entry → lesson captured
- ✅ ≥10 incident records in KB with root causes + remedies
- ✅ Agent evaluation rubrics reduce rework by ≥20%
- ✅ Skill recipes are discoverable + composable
- ✅ **[NEW]** Multi-rendering templates adopted for all strategic artifacts
- ✅ **[NEW]** Manifest.json maintained for 100% of artifacts

### RT3
- ✅ Spoke instantiation takes <2 hours (was manual, now scripted)
- ✅ Spoke teams inherit full routing policy + cost model
- ✅ ≥1 real spoke deployed with hooks running
- ✅ **[NEW]** Manifest.json export includes all necessary artifacts
- ✅ **[NEW]** Observability dashboard shows spoke-specific metrics

### RT4
- ✅ Lesson-Learned KB has ≥50 incidents with trending
- ✅ Anti-patterns library has ≥15 documented patterns
- ✅ Agent competency trends show improvement on ≥3 task types
- ✅ **[NEW]** Request tracing shows full path (issue → route → PR → merge)
- ✅ **[NEW]** Feedback loop closes: PR comments → routing rule update → next task uses updated rule

---

## 11. Risk Mitigation (ArcKit Lessons)

| Risk | ArcKit Mitigation | AgentArmy Application |
|---|---|---|
| Hooks become bottleneck | ArcKit limits hook timeout to 10s; async where possible | Implement timeout + fallback |
| Manifest.json drift | PostToolUse hook *always* updates; version-controlled | Similar pattern: hook is source of truth |
| Graph injection overhead | Graph is lazy-loaded; only for relevant prompts | Cache graph, invalidate on board change |
| Skill proliferation | ArcKit has 128 skills but strict taxonomy + MECE governance | Apply `agent-distinctiveness-advocate` audit quarterly |
| Learning loop noise | ArcKit filters incidents by severity + root cause; requires human review | Implement incident severity scoring + auto-triage |

---

## Next Steps

1. **Review this synthesis** — Does the ArcKit integration feel right? Any concerns?
2. **Create GitHub issues** from sections 5–8 (Release Train 1-4 breakdown)
3. **Add to project board** with Type, PI, Size, Estimate, routing guidance
4. **Kick off RT1** — Week of Jun 1

**Estimated time to full synthesis:** 2–3 hours (review + issue creation + board population)

---

**Document prepared:** 2026-05-23  
**Based on:** ArcKit-codex analysis + AgentArmy Wardley analysis + Strategic Plays framework  
**Next review:** After RT1 completion (mid-July)
