# Setup Guide

Complete step-by-step instructions for setting up AgentArmy from scratch.

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| Claude Code | AI agent runtime | [claude.ai/code](https://claude.ai/code) |
| Codex | Optional local AI agent runtime | Install from your Codex distribution |
| GitHub CLI | Project board, secrets, issues | [cli.github.com](https://cli.github.com) |
| Git | Version control | [git-scm.com](https://git-scm.com) |
| Python 3 | Used by some Actions scripts | system or [python.org](https://python.org) |

## Optional — Install local docs tooling

If you want to build or preview docs locally, install the existing MkDocs toolchain:

```bash
python3 -m pip install -r requirements-docs.txt
python3 -m mkdocs build
```

On Windows, `python3` may not exist even when Python is installed. Try these in order:

```powershell
python -m pip install -r requirements-docs.txt
python -m mkdocs build

py -m pip install -r requirements-docs.txt
py -m mkdocs build
```

In Codex desktop sessions, a bundled Python may be available even when system Python is not on PATH. Use the dependency loader or this typical runtime shape:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r requirements-docs.txt
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m mkdocs build
```

## Step 1 — Fork and clone

```bash
gh repo fork nickpclarke/AgentArmy --clone --remote
cd AgentArmy
```

## Step 2 — GitHub CLI auth for local setup

Local `gh` authentication is only for commands you run on your machine or inside a local agent session. It does not automatically flow into GitHub Actions or an external microVM runner.

Use the practical setup scopes for this template:

```bash
gh auth login -h github.com -p https -s repo,workflow,read:org,project
```

Complete the device flow: visit `https://github.com/login/device` and enter the code shown in your terminal.

Verify:

```bash
gh auth status
# Should show: 'project', 'read:org', 'repo', 'workflow' in Token scopes
```

If you are already logged in and only need to add missing scopes:

```bash
gh auth refresh -h github.com -s repo,workflow,read:org,project
```

## Step 3 — Create the GitHub Project board

```bash
# Create the project (note the project number in the output)
gh project create --owner YOUR_USERNAME --title "AgentArmy"

# Add SAFE-specific custom fields
gh project field-create PROJECT_NUM --owner YOUR_USERNAME \
  --name "Type" --data-type "SINGLE_SELECT" \
  --single-select-options "Epic,Feature,Story,Enabler,Bug,Spike,Decision"

gh project field-create PROJECT_NUM --owner YOUR_USERNAME \
  --name "PI" --data-type "TEXT"
```

The board comes pre-configured with Priority (P0/P1/P2), Size (XS/S/M/L/XL), Estimate, Iteration, Start date, and Target date fields from the GitHub template — verify these exist:

```bash
gh project field-list PROJECT_NUM --owner YOUR_USERNAME --format json
```

## Step 4 — Update workflow files

The workflows have the original owner and project number hardcoded. Update them:

```bash
# Replace owner references
sed -i 's/nickpclarke/YOUR_USERNAME/g' .github/workflows/*.yml

# Get your project field IDs for auto-status.yml
gh project field-list PROJECT_NUM --owner YOUR_USERNAME --format json
```

In `.github/workflows/auto-status.yml`, update the env block:

```yaml
env:
  PROJECT_ID: <your project node ID from GraphQL>
  STATUS_FIELD_ID: <your Status field ID>
  OPT_IN_PROGRESS: <your "In Progress" option ID>
  OPT_DONE: <your "Done" option ID>
```

To get the project node ID:

```bash
gh api graphql -f query='
  query($owner: String!, $number: Int!) {
    user(login: $owner) {
      projectV2(number: $number) { id }
    }
  }' \
  -f owner="YOUR_USERNAME" -F number=PROJECT_NUM \
  --jq '.data.user.projectV2.id'
```

## Step 5 — Create the PROJECT_TOKEN secret and PROJECT_NUMBER variable

GitHub Actions and microVM-style runners do not use your local `gh` keyring. They need their own token injected as an environment secret.

Use this naming exactly:

| Name | GitHub storage type | Sensitive? | Used by |
|---|---|---|---|
| `PROJECT_TOKEN` | Actions secret | Yes | Project-writing workflows and runner-side `GH_TOKEN` |
| `PROJECT_NUMBER` | Actions variable | No | Workflows that need to know which Project v2 board to use |

Do not store the PAT as a variable. Do not name it only `PAT` unless you also edit every workflow to read `secrets.PAT`.

For the default AgentArmy workflows, create a classic PAT with these practical scopes:

| Scope | Why it is needed |
|---|---|
| `project` | Read and write GitHub Projects v2 items and fields |
| `repo` | Create/comment/close issues and read private repo metadata |
| `workflow` | Support agent workflows that dispatch or update workflow automation |
| `read:org` | Read org-owned projects and org repository metadata when applicable |

1. Go to `https://github.com/settings/tokens`
2. Click **Generate new token (classic)**
3. Name it (e.g. `AgentArmy Actions`)
4. Check `project`, `repo`, `workflow`, and `read:org`
5. Generate and copy the token (shown once)

```bash
gh secret set PROJECT_TOKEN --repo YOUR_USERNAME/AgentArmy
# Paste your PAT when prompted

gh variable set PROJECT_NUMBER --repo YOUR_USERNAME/AgentArmy --body "PROJECT_NUM"
```

Verification:

```bash
gh secret list --repo YOUR_USERNAME/AgentArmy
# Should include PROJECT_TOKEN

gh variable list --repo YOUR_USERNAME/AgentArmy
# Should include PROJECT_NUMBER    PROJECT_NUM
```

In GitHub Actions steps that call `gh`, expose the secret as `GH_TOKEN`:

```yaml
env:
  GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
```

The built-in `GITHUB_TOKEN` can handle many repository operations, but it cannot access GitHub Projects v2 reliably. Use `PROJECT_TOKEN` for board automation.

### Two-token model — which workflows use what

AgentArmy's Actions use **two** token paths. Keep them straight:

| Token | Workflows | Why |
|---|---|---|
| `PROJECT_TOKEN` (classic PAT) | `auto-add-to-project`, `auto-status`, `board-commands`, `hitl-decision`, `pi-report`, `template-sanity-check` | GitHub **Projects v2** reads/writes — the built-in token can't do these reliably |
| `GITHUB_TOKEN` (built-in) | `label-pr-size`, `copilot-review`, `copilot-coding-agent`, `stale`, `board-commands` | Create/apply issue & PR labels, request reviewers, comment, close stale items |

### Let the built-in token write (Workflow permissions)

A fork's `GITHUB_TOKEN` defaults to **read-only**, which makes the label/PR workflows fail with `Resource not accessible by integration`. Fix it once:

**Settings → Actions → General → Workflow permissions → select _Read and write permissions_** (and tick *Allow GitHub Actions to create and approve pull requests* if you use PR-creating automation).

The PR-automation workflows (`label-pr-size`, `copilot-review`, `copilot-coding-agent`) also declare explicit least-privilege `permissions:` blocks, so they work even on a read-only default — but enabling read-write is the simplest catch-all and also covers `stale` and `board-commands`.

> Two failure signatures tell you this layer is misconfigured:
> - `Resource not accessible by integration` → token lacks label/issue/PR write → raise **Workflow permissions** above.
> - `fatal: not a git repository` → a `gh` step has no repo context → the template sets `GH_REPO: ${{ github.repository }}` to avoid this (no action needed).

If you use the Copilot workflows, also enable the matching features under **Settings → Copilot** (code review and/or coding agent). See [docs/copilot.md](copilot.md).

### Claude responder token (`CLAUDE_CODE_OAUTH_TOKEN`)

The `@claude` responder and the [autonomous review loop](pr-review-loop.md) need the Claude GitHub App plus a subscription token:

1. Install the **Claude GitHub App** on the repo: <https://github.com/apps/claude>
2. Generate an OAuth token from your Claude subscription and store it as a secret:

   ```bash
   claude setup-token
   gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo YOUR_USERNAME/AgentArmy
   # paste the token when prompted
   ```

Claude's `claude.yml` workflow pushes fix-commits with `PROJECT_TOKEN` (not the built-in `GITHUB_TOKEN`) so those commits re-trigger Gemini/Copilot reviews — that is what lets the review loop converge.

## Step 6 — Install and configure MemPalace

MemPalace provides cross-session memory for Claude Code and Codex. Install it once:

```bash
pip install mempalace
mempalace init
```

The hooks are already wired in `.claude/settings.json` for Claude Code and `.codex/hooks.json` for Codex. Verify MemPalace itself works:

```bash
mempalace --version
mempalace status
```

To also expose palace tools inside Claude Code as MCP tools, add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "mempalace": {
      "command": "mempalace",
      "args": ["mcp"]
    }
  }
}
```

See [docs/mempalace.md](mempalace.md) for the full MemPalace reference including room configuration, MCP tools, and troubleshooting.

## Step 7 — Install Claude Code plugins

Open Claude Code in the repo directory:

```
/plugin
```

This installs 9 community plugins. Reload when prompted:

```
/reload-plugins
```

### Plugins installed

| Plugin | What it adds |
|---|---|
| `commit-commands` | `/commit`, `/commit-push-pr`, `/clean_gone` |
| `pr-review-toolkit` | `/review-pr` multi-agent PR review |
| `mempalace` | Cross-session memory palace for agent context |
| `claude-md-management` | `/revise-claude-md`, `/claude-md-improver` |
| `skill-creator` | Build, test, and benchmark new skills |
| `claude-code-setup` | Automation workflow recommender |
| `frontend-design` | Production-grade UI generation |
| `figma` | Figma ↔ code translation |
| `playground` | Experimental sandbox |

## Step 8 — Configure Claude Code permissions

Create `.claude/settings.local.json` (gitignore this file — it's personal):

```json
{
  "permissions": {
    "allow": [
      "Bash(gh auth *)",
      "Bash(gh project *)",
      "Bash(gh issue *)",
      "Bash(gh pr *)",
      "Bash(gh api *)",
      "Bash(gh repo *)",
      "Bash(gh secret *)",
      "Bash(git add *)",
      "Bash(git commit -m *)",
      "Bash(git push *)"
    ]
  }
}
```

Add to `.gitignore`:

```
.claude/settings.local.json
.codex/config.local.toml
.env
```

## Optional - Configure Codex

Codex should read `AGENTS.md` first, then use `CLAUDE.md` and `.claude/agents/categories/` as shared AgentArmy routing context. The committed `.codex/config.toml` intentionally contains no provider API keys.

Keep machine-specific Codex settings in your user-level Codex config, environment variables, or an untracked `.codex/config.local.toml` file. See [Using Codex](codex.md) for the Codex-specific workflow and hook guidance.

### Recommended parallel-agent worktree strategy

When Claude Code and Codex are both active on the same PC, avoid pointing them at the same mutable checkout.

Recommended local model:

| Runtime | Preferred checkout |
|---|---|
| Claude Code | Main repository folder, for stewardship and integration work |
| Codex | A Codex UI-created worktree for isolated task work |
| Additional agents | Their own Codex UI-created worktree or equivalent isolated checkout |

Use the Codex desktop **New worktree** action instead of manually creating worktree folders. This keeps the branch/folder wiring visible in Codex and avoids one agent changing the branch or dirty state underneath another.

Before starting agent work, verify where the agent is standing:

```bash
git branch --show-current
git status --short --branch
git worktree list
```

## Step 9 — Run the onboarding sanity checks

```bash
# Confirm project board is accessible
gh project list --owner YOUR_USERNAME

# Confirm runner configuration names are set
gh secret list --repo YOUR_USERNAME/AgentArmy
gh variable list --repo YOUR_USERNAME/AgentArmy

# Confirm workflows are present
ls .github/workflows/
```

Run the local sanity script from the repository root:

```powershell
.\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber PROJECT_NUM
```

If Windows blocks local scripts, run the same check with an execution-policy override for this process:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber PROJECT_NUM
```

For a full end-to-end auto-add test, allow the script to create and close a temporary issue:

```powershell
.\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber PROJECT_NUM -CreateTestIssue
```

After pushing your fork, also run **Actions -> Template sanity check -> Run workflow**. This validates the runner-side `PROJECT_TOKEN` and `PROJECT_NUMBER`, which local `gh auth status` cannot prove.

See [AgentArmy Onboarding Sanity Check](onboarding.md) for the full checklist and troubleshooting table.

## What can be automated vs. what requires manual steps

Some setup steps require a human with browser access; others can run inside an agent session. Know which is which before delegating setup to Claude Code or Copilot.

| Step | Human required? | Can agent automate? | Notes |
|---|---|---|---|
| Fork + clone the repo | Yes (first time) | No | Needs GitHub account + browser for fork |
| `gh auth login` | Yes | No | Requires device-flow browser interaction |
| Create the Project board | Yes | Partially | `gh project create` works in an authed shell, but the board fields and views must be created in the web UI |
| Create `PROJECT_TOKEN` PAT | Yes | No | Token generation requires browser + 2FA |
| Set `PROJECT_TOKEN` / `PROJECT_NUMBER` | Yes | Yes (after auth) | `gh secret set` + `gh variable set` work in an authed shell |
| Update workflow files with username | No | Yes | `sed -i 's/nickpclarke/YOUR_USERNAME/g' .github/workflows/*.yml` |
| Create required labels | No | Yes | `gh label create` with appropriate colors + descriptions |
| Run onboarding sanity check | No | Yes | `.\scripts\onboarding-check.ps1 ...` or bash equivalent |
| Install MemPalace | No | Yes | `pip install mempalace && mempalace init` |
| Enable Workflow permissions (read/write) | Yes | No | Settings → Actions → General — browser only |
| Enable Copilot features | Yes | No | Settings → Copilot — browser only |
| Install Claude GitHub App | Yes | No | Browser install at github.com/apps/claude |

**Agent session checklist (what Claude Code or Copilot can do autonomously):**

```bash
# 1. Verify repo is a fork and has required files
git remote -v
ls .github/workflows/ CLAUDE.md

# 2. Update hardcoded owner references if the fork owner differs
grep -r "nickpclarke" .github/workflows/ --include="*.yml" -l

# 3. Verify secrets/variables are configured (will 401/404 if missing)
gh secret list --repo YOUR_USERNAME/AgentArmy
gh variable list --repo YOUR_USERNAME/AgentArmy

# 4. Create routing labels if missing
gh label create "agent-army-task" --description "Task routed to the Claude Code agent army" --color "7B61FF" --repo YOUR_USERNAME/AgentArmy
gh label create "copilot-task" --description "Task routed to the Copilot coding agent" --color "0075ca" --repo YOUR_USERNAME/AgentArmy
gh label create "hitl-decision" --description "Decision artifact requiring human or AI-app judgment" --color "e4e669" --repo YOUR_USERNAME/AgentArmy

# 5. Run the sanity check
.\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber PROJECT_NUM
```

## Agent-runtime onboarding path

When Claude Code (or another AI agent runtime) starts fresh in a forked AgentArmy repo — for example, during a remote cloud session or a CI-triggered agent run — it should self-verify before doing real work. The `SessionStart` hook in `.claude/settings.json` is the right place to wire this, but you can also run it manually:

```bash
# Quick sanity: is this a properly configured AgentArmy fork?
OWNER=$(gh repo view --json owner -q .owner.login 2>/dev/null || echo "UNKNOWN")
PROJECT_NUM=$(gh variable list --json name,value 2>/dev/null | \
  python3 -c "import json,sys; v=[x for x in json.load(sys.stdin) if x['name']=='PROJECT_NUMBER']; print(v[0]['value'] if v else 'NOT SET')")

echo "Owner:          $OWNER"
echo "Project number: $PROJECT_NUM"
echo "Branch:         $(git branch --show-current)"
echo "Workflows:      $(ls .github/workflows/*.yml 2>/dev/null | wc -l) files"
echo "Open RT1 items: $(gh issue list --label rt-1 --state open --json number -q length 2>/dev/null || echo '??')"
```

**What to check before delegating work in an agent session:**

1. `PROJECT_TOKEN` secret is set — if `gh project list` returns a 401, the board commands will fail silently. Escalate to a human to refresh the PAT.
2. The `agent-army-task` label exists — if it's missing, the routing workflow will not fire for Claude Code tasks. Create it with `gh label create` (see above).
3. The branch has not diverged unexpectedly — run `git status` and `git log --oneline -3` to confirm the working state.
4. Required workflow files are present — the `auto-status`, `auto-add-to-project`, and `claude` workflows must exist for the board automation to function.

## Optional: Azure Static Web Apps

This repo includes `swa-cli.config.json` for Azure SWA deployment. To enable:

## Optional: Azure Static Web Apps

This repo includes `swa-cli.config.json` for Azure SWA deployment. To enable:

```bash
npm install -g @azure/static-web-apps-cli
swa deploy --deployment-token YOUR_SWA_TOKEN
```

## Step 10 — Configure Google Cloud MCP & Codex Agent Sync

This repository supports official Google Cloud MCP servers (BigQuery, Storage, Observability, and Vertex AI Agent Registry) via HTTP/Streamable transport, and features automated synchronization of Claude agent definitions for Codex.

### 1. Google Cloud MCP Setup
To enable remote Google Cloud MCP servers for Claude Code or Codex, export the following environment variables in your local shell session:

```bash
# GCP Project, Region and Auth Configuration
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"
export GCP_BEARER_TOKEN=$(gcloud auth print-access-token)

# Remote HTTP MCP Server Endpoints
export GCP_BIGQUERY_MCP_URL="https://your-bigquery-mcp-server-url/mcp"
export GCP_STORAGE_MCP_URL="https://your-storage-mcp-server-url/mcp"
export GCP_OBSERVABILITY_MCP_URL="https://your-observability-mcp-server-url/mcp"
```

* **Claude Code**: Picks up these servers automatically at the project scope using [.mcp.json](file:///C:/dev/agentarmy/.mcp.json).
* **Codex**: Reads them via [.codex/config.toml](file:///C:/dev/agentarmy/.codex/config.toml).

### 2. Codex Agent Synchronization
The large library of specialist agents in `.claude/agents/categories/` is automatically synchronized into Codex-compatible TOML subagent definitions under `.codex/agents/` when a Codex session starts (via the `SessionStart` hook in `.codex/hooks.json`). 

You can also run the synchronization manually:
```bash
python scripts/sync_agents_to_codex.py
```

## Checklist

- [ ] Repo forked and cloned
- [ ] `gh auth` has `project` scope
- [ ] GitHub Project board created with Type and PI fields
- [ ] Workflow files updated with your username and project IDs
- [ ] `PROJECT_TOKEN` secret set
- [ ] `PROJECT_NUMBER` variable set
- [ ] Actions **Workflow permissions** set to read & write (lets the built-in `GITHUB_TOKEN` manage labels)
- [ ] `CLAUDE_CODE_OAUTH_TOKEN` secret set + Claude GitHub App installed (for `@claude` and the review loop)
- [ ] MemPalace installed (`pip install mempalace && mempalace init`)
- [ ] Docs tooling installed (`python3 -m pip install -r requirements-docs.txt`)
- [ ] Claude Code plugins installed (`/plugin` + `/reload-plugins`)
- [ ] `.claude/settings.local.json` configured and gitignored
- [ ] Optional Codex local config kept outside committed `.codex/config.toml`
- [ ] GCP MCP environment variables configured (optional)
- [ ] Codex custom agents synced via hook or manual script run
- [ ] Local onboarding sanity check passes
- [ ] Template sanity check workflow passes
