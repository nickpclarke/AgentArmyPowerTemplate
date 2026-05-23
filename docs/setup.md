# Setup Guide

Complete step-by-step instructions for setting up AgentArmy from scratch.

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| Claude Code | AI agent runtime | [claude.ai/code](https://claude.ai/code) |
| GitHub CLI | Project board, secrets, issues | [cli.github.com](https://cli.github.com) |
| Git | Version control | [git-scm.com](https://git-scm.com) |
| Python 3 | Used by some Actions scripts | system or [python.org](https://python.org) |

## Optional — Install local docs tooling

If you want to build or preview docs locally, install the existing MkDocs toolchain:

```bash
python3 -m pip install -r requirements-docs.txt
python3 -m mkdocs build
```

## Step 1 — Fork and clone

```bash
gh repo fork nickpclarke/AgentArmy --clone --remote
cd AgentArmy
```

## Step 2 — GitHub CLI auth with project scope

The default OAuth scopes do not include Projects v2 write access:

```bash
gh auth refresh -h github.com -s read:project,project
```

Complete the device flow: visit `https://github.com/login/device` and enter the code shown in your terminal.

Verify:

```bash
gh auth status
# Should show: 'project', 'read:org', 'repo', 'workflow' in Token scopes
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

## Step 5 — Create the PROJECT_TOKEN secret

GitHub Actions need a PAT with `project` scope because the built-in `GITHUB_TOKEN` cannot write to Projects v2.

1. Go to `https://github.com/settings/tokens`
2. Click **Generate new token (classic)**
3. Name it (e.g. `AgentArmy Actions`)
4. Check the **`project`** scope only
5. Generate and copy the token (shown once)

```bash
gh secret set PROJECT_TOKEN --repo YOUR_USERNAME/AgentArmy
# Paste your PAT when prompted
```

## Step 6 — Install and configure MemPalace

MemPalace provides cross-session memory for Claude Code. Install it once:

```bash
pip install mempalace
mempalace init
```

The hooks are already wired in `.claude/settings.json`. Verify they work:

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

## Step 7 — Configure Claude Code permissions

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
.env
```

## Step 8 — Verify everything works

```bash
# Confirm project board is accessible
gh project list --owner YOUR_USERNAME

# Confirm secrets are set
gh secret list --repo YOUR_USERNAME/AgentArmy

# Confirm workflows are present
ls .github/workflows/

# Open a test issue to trigger auto-add-to-project
gh issue create \
  --title "Setup verification" \
  --body "Testing auto-add-to-project workflow." \
  --label "enhancement"

# Check it appeared on the board
gh project item-list PROJECT_NUM --owner YOUR_USERNAME --format json
```

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
- [ ] MemPalace installed (`pip install mempalace && mempalace init`)
- [ ] Docs tooling installed (`python3 -m pip install -r requirements-docs.txt`)
- [ ] Claude Code plugins installed (`/plugin` + `/reload-plugins`)
- [ ] `.claude/settings.local.json` configured and gitignored
- [ ] Test issue auto-added to board
