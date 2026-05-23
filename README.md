# AgentArmy

A GitHub repository template for AI-powered software development using a coordinated fleet of Claude Code agents, with GitHub Projects v2 as the shared project management backbone.

## What Is This?

AgentArmy deploys **two coordinated AI armies** against your codebase, unified by GitHub Projects v2 as the shared coordination plane:

| Layer | What it does |
|---|---|
| **Claude Code army** | 100+ specialist sub-agents running locally — deep work, architecture, SAFE planning, complex implementation, security |
| **GitHub Copilot army** | GitHub-native agents — inline PR review, simple task coding, IDE suggestions, natural language board queries |
| **GitHub Projects v2** | Shared source of truth for all tasks, stories, and features — both armies read and write here |
| **GitHub Actions** | Automation that routes issues to the right army and keeps the board in sync |
| **MemPalace** | Cross-session persistent memory — Claude retains context across conversations via Stop and PreCompact hooks |

The two armies divide work by complexity and context: Copilot handles fast, bounded, GitHub-integrated tasks; Claude Code handles deep, strategic, multi-file work. See [docs/copilot.md](docs/copilot.md) for the full division of duties.

## Concept

AgentArmy scales beyond a single repo using a universal **N-Layer Hub & Spoke model**: keep this template as the **Hub**, then stamp out a separate **Spoke repo per layer** (UI, API, worker, mobile, infra, etc.). Spokes run in isolated AI sandboxes and stay decoupled through **contract-driven development** (OpenAPI/GraphQL/AsyncAPI/shared types).

See [docs/n-layer-architecture.md](docs/n-layer-architecture.md) for the end-to-end contract-first workflow.

```
You / Team
    │
    ├─────────────────────────────────────────────────────────────┐
    ▼                                                             ▼
Claude Code (local)                              GitHub Copilot (github-native)
    │                                                             │
    ├── Design-time agents                        ├── PR inline review (all PRs)
    │     product-manager · architect-reviewer    ├── Coding agent (copilot-task label)
    │     business-analyst · scrum-master         ├── IDE autocompletion
    │                                             └── @board-manager extension
    ├── Build-time agents
    │     frontend-developer · backend-developer
    │     typescript-pro · python-pro · ...
    │
    ├── Quality agents
    │     code-reviewer · security-auditor
    │     qa-expert · performance-engineer
    │
    └── Operations agents
          devops-engineer · sre-engineer
          cloud-architect · deployment-engineer
    │                                                             │
    └─────────────────────┬───────────────────────────────────────┘
                          │
                 GitHub Projects v2
          (shared board · Type · PI · Iteration)
                routing labels: copilot-task / agent-army-task
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

### 4. Install MemPalace

```bash
pip install mempalace
mempalace init
```

The hooks are already wired — Claude will automatically save and load context across sessions.

### 5. Install Claude Code plugins

Open Claude Code in this directory and run:

```
/plugin
/reload-plugins
```

### 6. Set the PROJECT_TOKEN secret

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
| `copilot-review` | PR opened | Requests Copilot first-pass review; flags large PRs for deep review |
| `copilot-coding-agent` | Issue labelled | Routes `copilot-task` to Copilot, `agent-army-task` to Claude Code |
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

**EA skills** (local commands in `.claude/commands/`):

| Skill | What it does |
|---|---|
| `/wardley [domain]` | Full Wardley analysis pipeline — value chain, map (OWM), doctrine, climate, gameplay |
| `/ea-adr [decision]` | Architecture Decision Record in MADR v4.0 format |
| `/capability-map [domain]` | Business capability model + investment heat map |

### Board slash commands (no hosting required)

Comment on any issue or PR to query the board — no server, no registration needed:

```
/board-status       → Todo / In Progress / Done + % complete
/sprint             → items in the current iteration
/blocked            → open issues with blocked-by label
/p0                 → open P0 priority items
/pi PI-1            → progress for a specific Program Increment
/board-help         → command reference
```

For the same queries inside GitHub Copilot Chat (`@board-manager`), `extensions/board-manager/` contains an Azure-deployable Copilot Extension. See [docs/copilot.md](docs/copilot.md).

### Agent roster

110+ specialist agents available out of the box across 11 categories, including a dedicated **Enterprise Architecture** category (11 agents) covering TOGAF ADM, Wardley Mapping, business capabilities, data architecture, platform engineering, and US regulatory compliance (FedRAMP, FISMA, HIPAA, CMMC, SOX, CCPA).

See [docs/agents.md](docs/agents.md) for the full categorised roster and agent-chaining patterns.

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
│   └── settings.local.json        # Claude Code permissions (gitignore in your fork)
├── .github/
│   └── workflows/
│       ├── auto-add-to-project.yml
│       ├── auto-status.yml
│       ├── board-commands.yml         # /board-status /sprint /blocked /p0 /pi
│       ├── copilot-review.yml         # Copilot first-pass + deep-review flagging
│       ├── copilot-coding-agent.yml   # Issue routing: copilot-task / agent-army-task
│       ├── label-pr-size.yml
│       ├── pi-report.yml
│       └── stale.yml
├── extensions/
│   └── board-manager/             # @board-manager Copilot Extension (optional, Azure-deployable)
│       ├── server.js
│       ├── package.json
│       ├── Dockerfile
│       └── .env.example
├── docs/
│   ├── agents.md                  # Agent roster and usage guide
│   ├── copilot.md                 # Two-army architecture and Copilot setup
│   ├── github-projects.md         # Board field reference
│   ├── mempalace.md               # MemPalace install, rooms, MCP tools, troubleshooting
│   ├── safe.md                    # SAFE workflow guide
│   └── setup.md                   # Detailed setup instructions
├── CLAUDE.md                      # AI assistant guidance (read by Claude Code)
└── README.md                      # This file
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
- [GitHub Copilot integration & two-army architecture](docs/copilot.md)
- [GitHub Projects field reference](docs/github-projects.md)
- [MemPalace setup](docs/mempalace.md)
- [SAFE workflow guide](docs/safe.md)
