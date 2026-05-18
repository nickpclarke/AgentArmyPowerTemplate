# CLAUDE.md

AI assistant guidance for the AgentArmy template repository.

## What This Repo Is

AgentArmy is a starter template for AI-powered software development. It deploys two coordinated AI armies through a shared GitHub Projects v2 board:

- **Claude Code army** — local, deep, strategic: architecture, complex features, SAFE planning, security audits
- **GitHub Copilot army** — GitHub-native, fast, lightweight: PR review, simple task coding, board queries via `@board-manager`
- **GitHub Projects v2** — shared coordination plane both armies read and write
- **GitHub Actions** — routes issues to the right army, syncs board state, automates ceremonies
- **SAFE** — the planning model at team and program level

All significant work is tracked as GitHub issues on the project board. Agents operate as specialists — delegate to the right agent, in the right army, rather than doing everything generalist.

## Working in This Repo

### GitHub Projects is the task backbone

Before starting significant work, check whether an issue exists on the board. If not, create one and add it to the project. Use `gh` CLI:

```bash
# Create an issue and add to project
gh issue create --title "..." --body "..." --label "Feature"
gh project item-add 1 --owner OWNER --url "https://github.com/OWNER/AgentArmy/issues/N"
```

Set the `Type` and `PI` fields on items so they're properly categorised.

### Route work to the right army first, then the right agent

**Copilot army** — apply label and let automation handle it:

| Trigger | Label | Copilot does |
|---|---|---|
| Bug or Story, Size XS/S | `copilot-task` | Creates branch, implements, opens PR |
| Any PR | (automatic) | Inline first-pass review |
| Board question | `@board-manager` in Copilot Chat | Queries board, returns status |

**Claude Code army** — delegate to the right specialist:

| Concern | Agent |
|---|---|
| Requirements / user stories | `business-analyst` |
| Architecture decisions | `architect-reviewer` |
| Sprint / PI planning | `scrum-master` |
| Frontend implementation | `frontend-developer`, `react-specialist`, `typescript-pro` |
| Backend implementation | `backend-developer`, `python-pro`, `node-specialist` |
| Deep code review (large PRs, `needs-deep-review` label) | `/review-pr` skill |
| Security audit | `security-auditor` or `/security-review` skill |
| CI/CD | `devops-engineer`, `deployment-engineer` |
| Performance | `performance-engineer` |

Full roster: [docs/agents.md](docs/agents.md) | Copilot setup: [docs/copilot.md](docs/copilot.md)

### Issue type conventions

Label every issue with its SAFE type:

| Label | Meaning | Typical hierarchy |
|---|---|---|
| `Epic` | Large body of work (>1 PI) | Top level — no parent |
| `Feature` | Deliverable capability within a PI | Child of Epic milestone |
| `Story` | User-facing value, completable in 1 sprint | Sub-issue of Feature |
| `Enabler` | Technical infrastructure or exploration | Same level as Story |
| `Bug` | Defect | Same level as Story |
| `Spike` | Time-boxed research | Same level as Story |

### PR conventions

PR body must contain `Closes #N`, `Fixes #N`, or `Resolves #N` to trigger the `auto-status` workflow. This is what moves issues from *In Progress* to *Done* automatically.

## GitHub Projects Field Reference

| Field | When to set |
|---|---|
| `Status` | Auto-managed by Actions; only override manually if needed |
| `Type` | Set on creation |
| `PI` | Set to current Program Increment (e.g. `PI-1`) |
| `Priority` | P0 = must ship this sprint; P1 = should ship this PI; P2 = backlog |
| `Size` | T-shirt estimate: XS ≤ 0.5 day, S ≤ 1 day, M ≤ 3 days, L ≤ 1 week, XL > 1 week |
| `Estimate` | Story points (Fibonacci: 1, 2, 3, 5, 8, 13) |
| `Iteration` | Assign to the sprint when committed |
| `Start date` / `Target date` | Set during sprint planning |
| `Parent issue` | Link Stories to their parent Feature |

## SAFE Workflow Summary

- **PI** = Program Increment (~10 weeks / 5 sprints). Track with a GitHub Milestone.
- **Sprint** = 2-week iteration. Use the `Iteration` field.
- **Hierarchy**: Feature (parent issue) → Story (sub-issue). Epics live at the Milestone level.
- **PI Planning**: Create the next PI's Milestone, create Feature issues under it, break Features into Stories.
- **Definition of Ready**: Issue has Type, PI, Size, and Estimate set, and acceptance criteria in the body.
- **Definition of Done**: PR merged, issue auto-moved to Done, linked PR references the issue.

## Available Skills (Claude Code)

Run these with `/skill-name` in the Claude Code prompt:

| Skill | What it does |
|---|---|
| `/commit` | Stage and commit with a well-formed message |
| `/commit-push-pr` | Commit, push, and open a PR in one step |
| `/review-pr` | Multi-agent PR review |
| `/security-review` | Security audit of current branch changes |
| `/revise-claude-md` | Update this file with session learnings |
| `/simplify` | Review and clean up changed code |

## GitHub Actions in This Repo

| Workflow | Do not manually override |
|---|---|
| `auto-add-to-project` | Runs on every new issue/PR — don't manually add items |
| `auto-status` | Runs on PR open/merge — don't manually change Status unless correcting |
| `copilot-review` | Adds Copilot as reviewer and flags large PRs — don't remove `needs-deep-review` label |
| `copilot-coding-agent` | Routes labelled issues — trust the routing, don't reassign manually |

## Copilot Handoff Conventions

- When closing a `copilot-task` issue via PR, ensure the PR body contains `Closes #N` so `auto-status` fires correctly
- If Copilot's PR needs a deep review, add `needs-deep-review` label and run `/review-pr`
- If Copilot's implementation is wrong or too shallow, remove `copilot-task`, add `agent-army-task`, and handle with Claude Code

## Configuration Notes

- `secrets.PROJECT_TOKEN` — PAT with `project` scope, required by Actions that write to the board
- `secrets.GITHUB_TOKEN` — built-in, used by `stale` and `label-pr-size`
- `.claude/settings.local.json` — local permissions file; **should be gitignored in forks**
