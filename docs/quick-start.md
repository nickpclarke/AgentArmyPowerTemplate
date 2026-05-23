# Quick Start

Get up and running with AgentArmy in 5 minutes.

## 1. Fork the Repository

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/AgentArmy.git
cd AgentArmy
```

## 2. Configure GitHub Projects

1. Go to your repository's **Projects** tab
2. Create a new **Project (beta)** called "AgentArmy"
3. Set up these custom fields:
   - **Type** (single select): Epic, Feature, Story, Enabler, Bug, Spike, Decision
   - **PI** (single select): PI-1, PI-2, etc.
   - **Size** (single select): XS, S, M, L, XL
   - **Estimate** (number): Story points
   - **Priority** (single select): P0, P1, P2

## 3. Set up GitHub Actions

1. Create a **classic Personal Access Token** with `project`, `repo`, `workflow`, and `read:org` scopes: [GitHub Settings](https://github.com/settings/tokens)
2. Add it as a secret: **Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret**
   - Name: `PROJECT_TOKEN`
   - Value: Your PAT
3. Add the project number as a variable: **Settings -> Secrets and variables -> Actions -> Variables -> New repository variable**
   - Name: `PROJECT_NUMBER`
   - Value: `1` unless your board uses a different number

Command-line equivalent:

```bash
gh secret set PROJECT_TOKEN --repo YOUR-USERNAME/AgentArmy
gh variable set PROJECT_NUMBER --repo YOUR-USERNAME/AgentArmy --body "1"
```

## 4. Create Your First Issue

```bash
gh issue create \
  --title "Setup: Configure project board" \
  --body "Initialize the GitHub Projects v2 board with fields and views" \
  --label "Enabler"

gh project item-add 1 \
  --owner YOUR-USERNAME \
  --url "https://github.com/YOUR-USERNAME/AgentArmy/issues/1"
```

## 5. Choose Your First Agent

Pick a task and delegate to the right specialist:

| Task | Agent |
|------|-------|
| Bug fix (XS/S) | `copilot-task` label → Copilot Coding Agent |
| Large feature | `backend-developer`, `frontend-developer`, etc. |
| Architecture | `architect-reviewer` |
| Data pipeline | `dlt-engineer` |
| Security review | `/security-review` skill |

## Next Steps

- **[Onboarding Sanity Check](onboarding.md)** - Verify local auth, runner secrets, project access, and auto-add
- **[Agent Roster](agents.md)** — Find specialists for your work
- **[GitHub Projects](github-projects.md)** — Master the coordination plane
- **[SAFe Framework](safe.md)** — Plan your first PI
