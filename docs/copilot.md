# GitHub Copilot Integration

This document covers how GitHub Copilot agents work alongside Claude Code in the AgentArmy workflow — the two-army architecture, what each handles, and how they coordinate through GitHub Projects.

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
│ • Test strategy                 │    │ • Board queries (@board-manager) │
│ • Large refactors               │    │ • Natural language issue lookup  │
└────────────┬────────────────────┘    └────────────┬────────────────────┘
             │                                       │
             └──────────────┬────────────────────────┘
                            │
                   GitHub Projects v2
                (shared coordination plane)
```

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
| 2. Deep review (large PRs) | Claude Code | `/review-pr` skill, triggered by `needs-deep-review` label |
| 3. Security audit | Claude Code `security-auditor` | `/security-review` skill on any security-sensitive PR |

### Routing labels

| Label | Meaning |
|-------|---------|
| `copilot-task` | Assign to Copilot coding agent — bounded, well-defined tasks |
| `agent-army-task` | Handle with Claude Code — complex, architectural, multi-file |
| `needs-deep-review` | Auto-applied by `copilot-review.yml` on PRs > 200 lines — triggers Claude Code `/review-pr` |

---

## GitHub Actions

### `copilot-review.yml`

Triggers on every non-draft PR:
1. Adds Copilot as a reviewer (requires Copilot code review enabled in repo Settings → Copilot)
2. Applies `needs-deep-review` label to PRs with > 200 lines changed

**Prerequisite:** Enable Copilot code review at repo Settings → Copilot → Code review. If set to "Automatic", Copilot reviews every PR without needing this workflow.

### `copilot-coding-agent.yml`

Triggers when `copilot-task` or `agent-army-task` label is applied to an issue:
- `copilot-task` → assigns to Copilot coding agent + posts instructions
- `agent-army-task` → posts Claude Code instructions to the issue

**Prerequisite:** Enable Copilot coding agent at repo Settings → Copilot → Coding agent.

---

## The `@board-manager` Copilot Extension

A custom Copilot Extension that lets you query and manage the AgentArmy project board using natural language inside GitHub Copilot Chat.

### What it does

```
@board-manager status
@board-manager what's in the sprint?
@board-manager show blocked items
@board-manager PI-1 progress
@board-manager show P0 items
@board-manager create a story for user login
```

### How it works

```
VS Code / github.com
    │ @board-manager <query>
    ▼
GitHub Copilot Chat
    │ POST /agent (SSE stream)
    ▼
board-manager server (extensions/board-manager/)
    │ parse intent → query GitHub Projects v2 GraphQL API
    ▼
Formatted response streamed back to chat
```

### Deploy to Vercel (recommended)

```bash
cd extensions/board-manager
cp .env.example .env
# fill in GITHUB_OWNER, GITHUB_REPO, PROJECT_NUMBER

npm install
vercel deploy
```

Note the deployed URL (e.g. `https://board-manager-xxx.vercel.app`).

### Register as a GitHub App

1. Go to `https://github.com/settings/apps` → New GitHub App
2. Set:
   - **GitHub App name**: `AgentArmy Board Manager`
   - **Homepage URL**: your Vercel URL
   - **Callback URL**: `https://github.com/login/oauth/authorize`
   - **Webhook URL**: your Vercel URL + `/agent`
   - **Copilot** section → Check "Copilot Extensions" → Agent type: **Agent**
   - **Permissions**: Repository → Issues (read), Projects (read)
3. Install the app on your repository
4. Set environment variables in Vercel from the GitHub App credentials

### Local development

```bash
cd extensions/board-manager
npm install
cp .env.example .env
npm run dev

# In another terminal, forward to localhost with GitHub's smee proxy:
npx smee-client --url https://smee.io/YOUR_CHANNEL --target http://localhost:3000/agent
```

---

## Extension Roadmap

The `board-manager` extension is a scaffold. Planned additions:

| Extension | What it does | Status |
|-----------|-------------|--------|
| `@board-manager` | Board queries, sprint status, PI progress | ✅ Built |
| `@safe-planner` | PI planning, story decomposition, WSJF scoring | Planned |
| `@arch-guide` | Architecture Q&A against your ADRs | Planned |
| `@security-guide` | Domain-specific security policy checks | Planned |

To build additional extensions, copy the `extensions/board-manager/` directory and customise the `route()` function in `server.js`.

---

## Copilot Plan Requirements

| Feature | Required plan |
|---------|--------------|
| Copilot code review | Copilot for Business or Enterprise |
| Copilot coding agent | Copilot Pro+ or Business/Enterprise |
| Copilot Extensions (custom) | Copilot Business or Enterprise |
| `@board-manager` extension | Copilot Business or Enterprise |

Verify your org's plan at `https://github.com/organizations/YOUR_ORG/settings/copilot`.
