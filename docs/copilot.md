# GitHub Copilot Integration

How GitHub Copilot agents work alongside Claude Code — the two-army architecture, what each handles, and how they coordinate through GitHub Projects.

## Two-Army Architecture

```
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│     CLAUDE CODE ARMY            │    │     GITHUB COPILOT ARMY          │
│     (local, deep, strategic)    │    │     (github-native, fast, light) │
├─────────────────────────────────┤    ├─────────────────────────────────┤
│ • Architecture decisions        │    │ • Inline PR suggestions          │
│ • Complex multi-file features   │    │ • First-pass code review         │
│ • SAFE planning (PI, sprints)   │    │ • Simple bug fixes & stories     │
│ • Deep security audits          │    │ • IDE autocomplete               │
│ • Test strategy                 │    │ • Board slash commands           │
│ • Large refactors               │    │ • Issue routing automation       │
└────────────┬────────────────────┘    └────────────┬────────────────────┘
             │                                       │
             └──────────────┬────────────────────────┘
                            │
                   GitHub Projects v2
                (shared coordination plane)
```

## N-Layer Hub & Spoke Coordination

AgentArmy is designed to scale to **N parallel layer repos** (“spokes”) created from the template. A single **GitHub Projects v2** board can coordinate work across all spokes at once because project items can span multiple repositories.

Practical implications:

- Keep contracts (OpenAPI/GraphQL/AsyncAPI/shared types) as the synchronization mechanism between spokes.
- Configure each spoke’s GitHub Actions to point at the same Project board so routing and `auto-status` stay consistent.
- Use Copilot for small, well-scoped issues inside a single spoke; use Claude Code when changes are cross-layer or contract-level.

See [docs/n-layer-architecture.md](n-layer-architecture.md) for the contract-first parallel execution workflow.

## Division of Duties

### By issue type

| Type | Size | Assign to | Why |
|------|------|-----------|-----|
| Bug | XS, S | Copilot (`copilot-task`) | Bounded, well-scoped, fast turnaround |
| Story | XS, S | Copilot (`copilot-task`) | Clear acceptance criteria, limited scope |
| Story | M, L, XL | Claude Code (`agent-army-task`) | Multi-file, context-heavy |
| Feature | Any | Claude Code | Needs architecture context |
| Enabler | Any | Claude Code | Technical depth required |
| Spike | Any | Claude Code | Open-ended exploration |
| Epic | Any | Claude Code (product-manager + architect) | Strategic planning |

### By PR review phase

| Phase | Who | Tool |
|-------|-----|------|
| 1. Automated first-pass | GitHub Copilot | Auto on every PR via `copilot-review.yml` |
| 2. Deep review (large PRs) | Claude Code | `/review-pr` skill — triggered by `needs-deep-review` label |
| 3. Security audit | Claude Code `security-auditor` | `/security-review` skill on security-sensitive PRs |

### Routing labels

| Label | Meaning |
|-------|---------|
| `copilot-task` | Assign to Copilot coding agent — bounded, well-defined tasks |
| `agent-army-task` | Handle with Claude Code — complex, architectural, multi-file |
| `needs-deep-review` | Auto-applied on PRs > 200 lines — run `/review-pr` in Claude Code |

---

## GitHub Actions

### `board-commands.yml` — Slash commands on issues and PRs

Comment on any issue or PR to query the board:

| Command | What you get |
|---------|-------------|
| `/board-status` | Status breakdown + % complete |
| `/sprint` | Items in the current iteration |
| `/blocked` | Open issues with `blocked-by` label |
| `/p0` | Open P0 priority items |
| `/pi PI-1` | Progress for a specific Program Increment |
| `/board-help` | Command reference |

The workflow reacts with 👀, runs a Python script against the Projects v2 GraphQL API using `PROJECT_TOKEN`, and posts a formatted reply comment. Works on both issues and PRs. Non-collaborators are ignored.

**Update for your fork:** change `OWNER` and `PROJECT_NUMBER` in the `env` block of `board-commands.yml`.

### `copilot-review.yml` — PR code review

Triggers on every non-draft PR:
1. Requests Copilot as a reviewer
2. Applies `needs-deep-review` label to PRs with > 200 lines changed

**Prerequisite:** Enable Copilot code review at repo Settings → Copilot → Code review. If set to "Automatic" mode, Copilot reviews every PR automatically.

### `copilot-coding-agent.yml` — Issue routing

Triggers when a routing label is applied:
- `copilot-task` → assigns to Copilot coding agent, posts instructions
- `agent-army-task` → posts Claude Code instructions to the issue

**Prerequisite:** Enable Copilot coding agent at repo Settings → Copilot → Coding agent.

---

## `@board-manager` Copilot Extension (Optional — Copilot Chat)

The board slash commands above work without any hosting. If you want the same queries available inside **GitHub Copilot Chat** in VS Code or github.com as `@board-manager`, the `extensions/board-manager/` directory contains a deployable Node.js server that implements the Copilot Extensions API.

This is **optional** — slash commands cover the same use cases without any infrastructure.

### When it's worth it

- Your team lives in VS Code Copilot Chat
- You want natural language queries mid-conversation (`@board-manager what's blocked?`)
- You're extending it with domain-specific knowledge (ADRs, architecture rules, etc.)

### Deploy to Azure Container Apps

```bash
cd extensions/board-manager
cp .env.example .env
# fill in GITHUB_OWNER, GITHUB_REPO, PROJECT_NUMBER

# Build and push
az acr build --registry YOUR_ACR --image board-manager .

# Deploy
az containerapp up \
  --name board-manager \
  --resource-group YOUR_RG \
  --image YOUR_ACR.azurecr.io/board-manager \
  --env-vars GITHUB_OWNER=... PROJECT_NUMBER=... GITHUB_REPO=...
```

Note the deployed URL — you'll need it for the GitHub App registration.

### Register as a GitHub App

1. Go to `https://github.com/settings/apps` → New GitHub App
2. Set:
   - **GitHub App name**: `AgentArmy Board Manager`
   - **Homepage URL**: your Azure Container App URL
   - **Callback URL**: `https://github.com/login/oauth/authorize`
   - **Webhook URL**: your Azure URL + `/agent`
   - **Copilot** section → Check "Copilot Extensions" → Agent type: **Agent**
   - **Permissions**: Repository → Issues (read), Projects (read)
3. Install the app on your repository
4. Add `GITHUB_OWNER`, `PROJECT_NUMBER`, `GITHUB_REPO` as environment variables in Azure

### Local development

```bash
cd extensions/board-manager
npm install
cp .env.example .env
npm run dev

# Forward local port via smee proxy for GitHub webhook delivery
npx smee-client --url https://smee.io/YOUR_CHANNEL --target http://localhost:3000/agent
```

---

## Extension Roadmap

| Extension | What it does | Status |
|-----------|-------------|--------|
| Board slash commands | Status, sprint, blocked, PI progress — via issue/PR comments | ✅ Actions-based, no hosting |
| `@board-manager` | Same queries in Copilot Chat (VS Code / github.com) | ✅ Extension scaffold, Azure-deployable |
| `@safe-planner` | PI planning, story decomposition, WSJF scoring | Planned |
| `@arch-guide` | Architecture Q&A against your ADRs | Planned |

---

## Copilot Plan Requirements

| Feature | Required plan |
|---------|--------------|
| Copilot code review | Copilot for Business or Enterprise |
| Copilot coding agent | Copilot Pro+ or Business/Enterprise |
| Board slash commands | Any plan (uses `GITHUB_TOKEN` + `PROJECT_TOKEN`) |
| `@board-manager` extension | Copilot Business or Enterprise |

Verify your org's plan at `https://github.com/organizations/YOUR_ORG/settings/copilot`.
