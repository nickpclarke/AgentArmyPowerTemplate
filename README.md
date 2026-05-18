# AgentArmy

A GitHub repository template for AI-powered software development using a coordinated fleet of Claude Code agents, with GitHub Projects v2 as the shared project management backbone.

## What Is This?

AgentArmy wires three things together:

| Layer | What it does |
|---|---|
| **Claude Code** | AI coding assistant with 100+ specialised sub-agents — frontend, backend, security, devops, product, and more |
| **GitHub Projects v2** | Structured board used as the shared source of truth for all tasks, stories, and features |
| **GitHub Actions** | Automation that keeps the board and code in sync without manual triage |

The result is a development environment where specialist agents handle different concerns, work is tracked on a SAFE-aligned project board, and automation handles the mechanical housekeeping.

## Concept

```
You / Team
    │
    ▼
Claude Code
    │
    ├── Design-time agents
    │     product-manager · architect-reviewer · business-analyst
    │     scrum-master · ui-designer · ux-researcher
    │
    ├── Build-time agents
    │     frontend-developer · backend-developer · fullstack-developer
    │     typescript-pro · python-pro · react-specialist · ...
    │
    ├── Quality agents                          GitHub Projects v2
    │     code-reviewer · security-auditor  ◄──  Todo / In Progress / Done
    │     qa-expert · performance-engineer       Type · PI · Iteration · Priority
    │
    └── Operations agents
          devops-engineer · deployment-engineer
          sre-engineer · cloud-architect
```

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) — CLI or desktop app
- [GitHub CLI](https://cli.github.com) — `gh` in PATH, authenticated
- GitHub account with a project board attached to this repo

### 1. Fork and clone

```bash
gh repo fork nickpclarke/AgentArmy --clone
cd AgentArmy
```

### 2. Authenticate GitHub CLI with project scope

```bash
gh auth refresh -h github.com -s read:project,project
```

Complete the device flow at `https://github.com/login/device`.

### 3. Create your GitHub Project board

```bash
gh project create --owner YOUR_USERNAME --title "AgentArmy"

gh project field-create PROJECT_NUM --owner YOUR_USERNAME \
  --name "Type" --data-type "SINGLE_SELECT" \
  --single-select-options "Epic,Feature,Story,Enabler,Bug,Spike"

gh project field-create PROJECT_NUM --owner YOUR_USERNAME \
  --name "PI" --data-type "TEXT"
```

### 4. Install Claude Code plugins

Open Claude Code in this directory and run:

```
/plugin
/reload-plugins
```

### 5. Set the PROJECT_TOKEN secret

GitHub Actions need a PAT with `project` scope:

1. Go to `https://github.com/settings/tokens` → **Tokens (classic)**
2. Generate a token with only the **`project`** scope checked
3. Store it: `gh secret set PROJECT_TOKEN --repo YOUR_USERNAME/AgentArmy`

See [docs/setup.md](docs/setup.md) for the complete setup guide including updating the hardcoded owner/project references in the workflow files.

---

## What's Included

### GitHub Projects board — 21 fields

Key fields for SAFE:

| Field | Type | Purpose |
|---|---|---|
| Status | Single Select | Todo / In Progress / Done — auto-managed |
| **Type** | Single Select | Epic / Feature / Story / Enabler / Bug / Spike |
| **PI** | Text | Program Increment (e.g. `PI-1`) |
| Priority | Single Select | P0 / P1 / P2 |
| Size | Single Select | XS / S / M / L / XL |
| Estimate | Number | Story points |
| Iteration | Iteration | Sprint assignment |
| Start / Target date | Date | Sprint planning dates |
| Parent issue | — | Feature → Story hierarchy |

Full reference: [docs/github-projects.md](docs/github-projects.md)

### GitHub Actions (`.github/workflows/`)

| Workflow | Trigger | What it does |
|---|---|---|
| `auto-add-to-project` | Issue / PR opened | Adds every new item to the board automatically |
| `auto-status` | PR opened / merged | Moves linked issues to *In Progress* or *Done* |
| `stale` | Mondays 09:00 UTC | Warns at 14 days idle, closes at 21 (P0/Epic exempt) |
| `label-pr-size` | PR opened / synced | Labels PRs XS→XL by line count |
| `pi-report` | Fridays 08:00 UTC | Posts a Todo/In Progress/Done summary to Actions |

### Claude Code plugins (9 installed via `/plugin`)

| Plugin | Key skills |
|---|---|
| `commit-commands` | `/commit`, `/commit-push-pr`, `/clean_gone` |
| `pr-review-toolkit` | `/review-pr` — multi-agent PR review |
| `mempalace` | Cross-session memory palace for agent context |
| `claude-md-management` | `/revise-claude-md`, CLAUDE.md quality auditing |
| `skill-creator` | Build, test, and benchmark custom skills |
| `claude-code-setup` | Automation workflow recommender |
| `frontend-design` | Production-grade UI generation |
| `figma` | Figma ↔ code design translation |
| `playground` | Experimental sandbox |

Plus built-in Claude Code skills: `update-config`, `simplify`, `fewer-permission-prompts`, `loop`, `claude-api`, `init`, `review`, `security-review`.

### Agent roster

100+ specialist agents available out of the box. See [docs/agents.md](docs/agents.md) for the full categorised roster and agent-chaining patterns.

---

## SAFE Support

This template maps SAFE constructs onto GitHub's object model, working well at team and program level.

**What works well:**
- Sprint/iteration cadence via the Iteration field
- Feature → Story 2-level hierarchy via Parent issue
- PI tracking via Milestones + PI text field
- Priority and estimation fields
- Automated status flow via GitHub Actions

**Known limitations:**
- Hierarchy is max 2 levels — Epics tracked by label convention
- No native PI construct — use Milestones as the container
- No WSJF calculator — script it as a future Action
- No dependency graph — use linked issues + `blocked-by` label
- No capacity planning — tracked manually per sprint

Full guide including workarounds: [docs/safe.md](docs/safe.md)

---

## Security Notes

- `.claude/settings.local.json` contains personal permissions — **gitignore this in your fork**
- `.env` contains API keys — also gitignore
- `PROJECT_TOKEN` must never be committed — store as a repo secret only

---

## Repository Structure

```
.
├── .claude/
│   └── settings.local.json   # Claude Code permissions (gitignore in your fork)
├── .github/
│   └── workflows/
│       ├── auto-add-to-project.yml
│       ├── auto-status.yml
│       ├── label-pr-size.yml
│       ├── pi-report.yml
│       └── stale.yml
├── docs/
│   ├── agents.md             # Agent roster and usage guide
│   ├── github-projects.md    # Board field reference
│   ├── safe.md               # SAFE workflow guide
│   └── setup.md              # Detailed setup instructions
├── CLAUDE.md                 # AI assistant guidance (read by Claude Code)
└── README.md                 # This file
```

---

## Extending the Template

**Add a custom skill:**
```
/skill-creator
```

**Add a project board field:**
```bash
gh project field-create PROJECT_NUM --owner YOUR_USERNAME \
  --name "FIELD_NAME" --data-type "SINGLE_SELECT" \
  --single-select-options "opt1,opt2,opt3"
```

**Add a GitHub Action:** drop a `.yml` in `.github/workflows/`. Use `secrets.PROJECT_TOKEN` for any action that writes to the project board.

---

## Docs

- [Full setup guide](docs/setup.md)
- [Agent roster](docs/agents.md)
- [GitHub Projects field reference](docs/github-projects.md)
- [SAFE workflow guide](docs/safe.md)
