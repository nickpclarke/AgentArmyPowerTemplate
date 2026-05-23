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
  --single-select-options "Epic,Feature,Story,Enabler,Bug,Spike"

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
  OPT_IN_PROGRESS: <your "In progress" option ID>
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

## Optional: Azure Static Web Apps

This repo includes `swa-cli.config.json` for Azure SWA deployment. To enable:

```bash
npm install -g @azure/static-web-apps-cli
swa deploy --deployment-token YOUR_SWA_TOKEN
```

## Checklist

- [ ] Repo forked and cloned
- [ ] `gh auth` has `project` scope
- [ ] GitHub Project board created with Type and PI fields
- [ ] Workflow files updated with your username and project IDs
- [ ] `PROJECT_TOKEN` secret set
- [ ] `PROJECT_NUMBER` variable set
- [ ] MemPalace installed (`pip install mempalace && mempalace init`)
- [ ] Docs tooling installed (`python3 -m pip install -r requirements-docs.txt`)
- [ ] Claude Code plugins installed (`/plugin` + `/reload-plugins`)
- [ ] `.claude/settings.local.json` configured and gitignored
- [ ] Optional Codex local config kept outside committed `.codex/config.toml`
- [ ] Local onboarding sanity check passes
- [ ] Template sanity check workflow passes
