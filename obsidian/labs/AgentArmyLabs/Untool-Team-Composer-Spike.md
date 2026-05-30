---
title: Untool — Right-Sized Team Composer Spike (v0)
status: ready-for-spike
created: 2026-05-30
session: awesome-yonath-f38cd6
related-adrs: [ARC-ADR-044]
related-notes: [[Untool-Ontology-Orchestrated-Swarm-Intelligence]], [[Ontology-Pipeline]], [[Reification-and-Hyperedges]]
tags: [untool, spike, team-composer, swarm, ontology]
---

# Untool — Right-Sized Team Composer Spike (v0)

> **Purpose.** Falsify the design *before* we commit to it. Build the smallest possible team composer (set cover over typed holons) in ~50 lines, run it against three hand-stubbed scenarios, see if the team it produces is the team a human architect would choose.

This is the cheapest experiment that can kill the design or green-light ARC-ADR-044 for build work.

---

## Hypothesis

**H1.** A typed-holon ontology + set-cover query produces *good* team compositions for at least 3-of-3 realistic AgentArmy goal scenarios, with hand-tuned weights and no learned components.

**H2.** When the composer produces a team different from what a human architect would choose, the disagreement is **legible** — we can trace it back to a specific capability/cost/trust score that, if adjusted, would converge the outputs.

**H3.** The model expresses every constraint we need. If we hit a goal scenario where the ontology *can't represent* what we want, that's a stronger signal than performance — it forces us to revise the Kind/Relator inventory.

If H1 fails: weights are tuneable, no architectural problem.
If H2 fails: the model is opaque; we need richer explanation surface before build.
If H3 fails: the data model is wrong; revise before any production code touches it.

---

## Scope (what we build in the spike)

- **Storage:** ArcadeDB (already in fleet). Single graph. Hand-stubbed.
- **Stub holons:** 5 Agents, 10 Tools, 3 Skills, 3 Capability types. (~30 nodes total)
- **Composer:** TypeScript or Python, ~50 lines, set cover with cost + trust constraints.
- **Scenarios:** 3 hand-authored goals, each with expected team and rationale.

### NOT in scope

- Real ecosystem federation (single-source for the spike)
- Emission DAG (not needed to test team composition)
- JIT attachment runtime (separate concern)
- Trust propagation (use static trust grades)
- Temporal pulse (single time slice)
- Credentials broker (assume all auth pre-resolved)

If the spike succeeds, those become the v1 build buckets in priority order.

---

## Stub data model

### Agent holons

| id | kind | capabilities | cost/call | trust | ecosystem |
|----|------|--------------|-----------|-------|-----------|
| `a:researcher`         | ResearcherAgent     | [web-search, summarize, cite-source]            | 0.1 | 0.8 | claude |
| `a:code-reviewer`      | CodeReviewerAgent   | [code-review, diff-analysis, security-scan]     | 0.2 | 0.9 | claude |
| `a:architect`          | ArchitectAgent      | [design, adr-author, decision-tree]             | 0.3 | 0.9 | claude |
| `a:ops`                | OpsAgent            | [deploy, monitor, incident-response, rollback]  | 0.2 | 0.7 | fleet |
| `a:scribe`             | ScribeAgent         | [summarize, format, persist]                    | 0.05 | 0.9 | claude |

### Tool holons

| id | capability | cost/call | trust | binding |
|----|------------|-----------|-------|---------|
| `t:wpcom-availability` | check-domain        | 0.0  | 0.9  | mcp |
| `t:github-search`      | code-search          | 0.0  | 1.0  | mcp |
| `t:semgrep`            | security-scan        | 0.0  | 0.9  | cli |
| `t:postman-mock`       | contract-mock        | 0.0  | 0.9  | http |
| `t:arcadedb-query`     | graph-query          | 0.0  | 1.0  | http |
| `t:llm-gateway`        | embed                | 0.01 | 1.0  | mcp |
| `t:public-mcp-foo`     | summarize            | 0.0  | 0.3  | mcp |   ← low trust (community)
| `t:public-mcp-bar`     | web-search           | 0.0  | 0.4  | mcp |   ← low trust (community)
| `t:azure-keyvault`     | resolve-secret       | 0.0  | 1.0  | sdk |
| `t:azure-aca`          | deploy               | 0.05 | 1.0  | sdk |

### Capability types (the "common vocabulary")

`web-search`, `summarize`, `cite-source`, `code-review`, `diff-analysis`, `security-scan`, `design`, `adr-author`, `decision-tree`, `deploy`, `monitor`, `incident-response`, `rollback`, `format`, `persist`, `check-domain`, `code-search`, `contract-mock`, `graph-query`, `embed`, `resolve-secret`

### Stub goal scenarios

**Scenario 1 — "Check brand-name availability and write a one-pager."**
Required caps: `check-domain`, `summarize`, `format`, `persist`
*Expected team:* `a:researcher` (calls `t:wpcom-availability`) + `a:scribe`. Cost 0.15. Should NOT pick `t:public-mcp-foo` for summarize because in-house Agent capability dominates.

**Scenario 2 — "Review PR #367 for security and architectural fit."**
Required caps: `code-review`, `diff-analysis`, `security-scan`, `decision-tree`
*Expected team:* `a:code-reviewer` + `a:architect`. Two agents because no single agent covers both `security-scan` and `decision-tree`. Cost 0.5.

**Scenario 3 — "Deploy backend-core, monitor, and roll back on failure."**
Required caps: `deploy`, `monitor`, `incident-response`, `rollback`
*Expected team:* `a:ops` solo. All four capabilities are in one agent. Cost 0.2.

**Stretch — "Research a question using only high-trust sources (trust ≥ 0.8), summarize, and cite."**
Required caps: `web-search`, `summarize`, `cite-source` with `min-trust = 0.8`
*Expected team:* `a:researcher` only. The composer must REJECT `t:public-mcp-foo` and `t:public-mcp-bar` despite them satisfying capability — trust filter binds.

---

## Composer signature (the ~50 lines)

```ts
// untool/spike/composer.ts
//
// Right-sized team composer — set cover over typed holon graph
// with cost, trust, and coordination constraints.

type Capability = string
type Trust = number            // 0..1
type Cost = number             // dimensionless

interface AgentHolon {
  id: string
  capabilities: Capability[]
  cost: Cost
  trust: Trust
  ecosystem: string
}

interface Goal {
  capabilitiesRequired: Capability[]
  minTrust: Trust              // floor each agent must clear
  budget: Cost
  preferredEcosystem?: string  // soft preference (small bonus)
}

interface Team {
  agents: AgentHolon[]
  cost: Cost
  coverage: Map<Capability, AgentHolon>
  unmet: Capability[]
}

// Greedy set cover with constraints — sufficient for spike scale (<20 agents)
export function composeTeam(goal: Goal, agents: AgentHolon[]): Team {
  const eligible = agents.filter(a => a.trust >= goal.minTrust)

  const team: AgentHolon[] = []
  const coverage = new Map<Capability, AgentHolon>()
  let runningCost = 0

  const remaining = () =>
    goal.capabilitiesRequired.filter(c => !coverage.has(c))

  while (remaining().length > 0 && runningCost <= goal.budget) {
    // Pick the agent maximizing (newly-covered caps) / cost,
    // with a small bonus for preferred ecosystem.
    const open = remaining()
    const ranked = eligible
      .filter(a => !team.includes(a))
      .map(a => {
        const newlyCovered = a.capabilities.filter(c => open.includes(c)).length
        if (newlyCovered === 0) return null
        const ecoBonus = a.ecosystem === goal.preferredEcosystem ? 0.05 : 0
        const score = (newlyCovered / Math.max(a.cost, 0.01)) + ecoBonus
        return { agent: a, score, newlyCovered }
      })
      .filter(Boolean)
      .sort((a, b) => b!.score - a!.score)

    if (ranked.length === 0) break  // no more useful agents

    const pick = ranked[0]!.agent
    team.push(pick)
    runningCost += pick.cost
    for (const cap of pick.capabilities) {
      if (open.includes(cap) && !coverage.has(cap)) coverage.set(cap, pick)
    }
  }

  return {
    agents: team,
    cost: runningCost,
    coverage,
    unmet: remaining()
  }
}
```

This is ~45 lines of body. Hits all four constraints (capability cover, trust floor, budget, soft preference). Greedy is fine at spike scale; the production composer can use a proper ILP solver if needed.

**Note on intentional limitations of the spike:**
- Trust is a static field, not propagated through the DAG (deferred — separate concern).
- Tools-as-holons are stubbed but the spike composer only considers Agent holons; Tool/Capability binding happens at the JIT-provisioning step (separate spike).
- No temporal pulse — single time slice.
- No emission generation — composer just returns a team plan.

---

## Run plan

1. Hand-load the stub data into ArcadeDB (or in-memory map for v0.5).
2. Author the composer (~50 lines).
3. Run all 3 scenarios + the stretch.
4. For each scenario, compare composer output to expected. Note:
   - Match exactly → ✓
   - Different team but legible cost/trust/coverage rationale → ⚠ (good enough; tune weights)
   - Different team with opaque rationale → ✗ (model issue; revise before build)
   - Composer can't represent constraint → ✗✗ (data-model issue; revise OntoUML Kinds before build)
5. Write spike outcome to `obsidian/labs/AgentArmyLabs/Untool-Team-Composer-Spike-Results.md`.
6. Use spike outcome to refine ARC-ADR-044 before any production code references the design.

---

## Success criteria

| Outcome | What it means | Next action |
|---|---|---|
| 3/3 + stretch match exactly | Model + weights look right | Green-light ADR-044 for build |
| 3/3 match with one weight tweak | Model is right, weights need tuning | Document weight tuning in ADR; green-light build |
| 2/3 match, one fails on trust filter | Trust mechanic needs more depth | Add trust propagation to v1 scope; green-light build with caveat |
| 1/3 match | Model is too coarse | Revise Kinds/Relators; re-spike |
| 0/3 — composer can't express required constraint | Data model wrong | Revise ontology before any production code |

---

## Time budget

- Stub data + load: 1 hour
- Composer: 1 hour
- Run + write up: 1 hour

**Total: ~half a day.** Cheapest possible falsification of a multi-sprint design.

---

## See also

- [[Untool-Ontology-Orchestrated-Swarm-Intelligence]] — the full design this spike validates
- ARC-ADR-044 — the formal decision record
- [[Reification-and-Hyperedges]] — data-model substrate
- [[Factory-Loop-Test-Infrastructure]] — the broader test-loop pattern this fits into
