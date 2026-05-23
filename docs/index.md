# AgentArmy

**AI-powered software development template** with coordinated armies of specialized AI agents.

AgentArmy deploys two coordinated armies through a shared GitHub Projects v2 board:

- **Claude Code army** — local, deep, strategic: architecture, complex features, SAFE planning, security audits, data pipelines (via `dlt-engineer` specialist)
- **GitHub Copilot army** — GitHub-native, fast, lightweight: PR review, simple task coding, board queries via `@board-manager`

All significant work is tracked as GitHub issues on the project board. Agents operate as specialists — delegate to the right agent, in the right army, rather than doing everything generalist.

## Quick Navigation

<div class="grid cards" markdown>

- :rocket: **Getting Started**
  
  Set up your AgentArmy fork and configure GitHub Projects, Actions, and Copilot Chat.
  
  [Setup Guide →](setup.md)

- :white_check_mark: **Onboarding Check**

  Verify local auth, runner secrets, Project v2 access, and optional auto-add behavior before real work starts.

  [Run Sanity Check →](onboarding.md)

- :busts_in_silhouette: **Agent Roster**
  
  Specialist agent definitions across 11 categories. Find the right expert for your task.
  
  [View All Agents →](agents.md)

- :octocat: **GitHub Copilot Army**
  
  Lightweight, GitHub-native automation for PR review, simple coding, and board queries.
  
  [Copilot Guide →](copilot.md)

- :clipboard: **GitHub Projects**
  
  Shared coordination plane for all armies. Issue types, fields, status workflow.
  
  [Projects Guide →](github-projects.md)

- :spiral_calendar: **SAFe Framework**
  
  Program Increments (PIs), sprints, Definition of Ready/Done, velocity tracking.
  
  [SAFe Guide →](safe.md)

- :brain: **Memory Palace**
  
  Organizational memory system for preserving context and learnings across agent sessions.
  
  [Learn More →](mempalace.md)

- :busts_in_silhouette: **Human-in-the-Loop**

  Decision Artifacts surface creative and architectural forks to humans (or AI apps) via the board, without blocking parallel work.

  [HITL Guide →](hitl.md)

</div>

## Key Concepts

### Two Armies

Each army has distinct strengths:

| Army | Strength | Use For |
|------|----------|---------|
| **Claude Code** | Deep thinking, complex architecture, multi-file refactors | Requirements analysis, system design, large features, security audits, data pipelines |
| **GitHub Copilot** | Fast turnaround, PR-native review, lightweight automation | Bug fixes, simple features (XS/S), inline PR feedback |

### SAFE Planning

AgentArmy uses Scaled Agile Framework (SAFe) for predictable delivery:

- **PI (Program Increment)** = ~10 weeks of work
- **Sprint** = 2-week iterations
- **Definition of Ready** = Type, PI, Size, Estimate set + acceptance criteria
- **Definition of Done** = PR merged with `Closes #N` link

### GitHub Projects v2

Single source of truth for all work:

- **Type** field: Epic, Feature, Story, Enabler, Bug, Spike, Decision
- **Status** workflow: Todo → Ready → In Progress → In Review → Done (plus Awaiting Decision for HITL holds)
- **PI** field: Links issues to Program Increments
- **Size** & **Estimate**: T-shirt size + story points

## Repository Structure

```
.claude/agents/categories/    → specialist agent definitions (11 categories)
.claude/commands/             → local slash commands (/wardley, /ea-adr, /capability-map)
.github/workflows/            → GitHub Actions: auto-status, routing, board commands, docs build
docs/                         → This documentation
extensions/board-manager/     → Azure-deployable Copilot Chat extension
pipelines/                    → dlt data pipeline toolkit
```

## Getting Help

- **Agent routing questions?** See [Agent Roster](agents.md) and [Setup Guide](setup.md)
- **GitHub Projects setup?** See [GitHub Projects Guide](github-projects.md)
- **Runner token or setup validation?** See [Onboarding Sanity Check](onboarding.md)
- **SAFE planning?** See [SAFe Framework](safe.md)
- **Copilot Chat?** See [Copilot Army Guide](copilot.md)

## Links

- [GitHub Repository](https://github.com/nickpclarke/AgentArmy)
- [GitHub Projects v2 Board](https://github.com/users/nickpclarke/projects/1)
