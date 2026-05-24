# AgentArmy Onboarding Sanity Check

Use this page when a fresh fork, new agent runtime, or microVM runner needs a fast confidence check before real work starts.

AgentArmy has two authentication contexts:

| Context | Where it lives | Used for | Required name |
|---|---|---|---|
| Local `gh` login | Developer or agent machine keyring | Manual setup, issue creation, board inspection | Managed by `gh auth login` |
| Runner token | GitHub Actions secret or external runner secret store | Workflows, microVM agents, board automation | `PROJECT_TOKEN` exposed as `GH_TOKEN` |

Do not store tokens as GitHub Actions variables. Tokens belong in **Secrets**. Non-sensitive values such as the project number belong in **Variables**.

## Required Configuration

For a standard fork owned by `YOUR_USERNAME`:

```powershell
gh auth login -h github.com -p https -s repo,workflow,read:org,project

gh secret set PROJECT_TOKEN --repo YOUR_USERNAME/AgentArmy
gh variable set PROJECT_NUMBER --repo YOUR_USERNAME/AgentArmy --body "1"
```

Use a classic PAT for `PROJECT_TOKEN` unless your organization has already standardized on a GitHub App installation token. The practical classic PAT scopes for this template are:

| Scope | Why this template may need it |
|---|---|
| `project` | Read and write GitHub Projects v2 items and fields |
| `repo` | Create/comment/close issues and read private repo metadata |
| `workflow` | Allow agent workflows that dispatch or update workflow automation |
| `read:org` | Read org-owned projects and org repository metadata when the fork is under an organization |

If you use a narrower token, run the sanity check before relying on automation.

## Local Sanity Check

From the repository root:

```powershell
.\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber 1
```

For a broader local platform check, also run:

```powershell
node tools/agentarmy-doctor.mjs --write-artifacts
```

This writes normalized JSON and Markdown diagnostics under `tests/artifacts/doctor/` for handoff, CI, and optional dashboard display.

If Windows blocks local scripts, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber 1
```

To test the full issue-opened auto-add path, allow the script to create and close a temporary issue:

```powershell
.\scripts\onboarding-check.ps1 -Owner YOUR_USERNAME -Repo AgentArmy -ProjectNumber 1 -CreateTestIssue
```

The script checks:

- local `gh` auth and visible scopes
- repository access
- GitHub Projects v2 visibility and item reads
- `PROJECT_TOKEN` secret name
- `PROJECT_NUMBER` variable value
- required workflow files
- optional end-to-end issue creation, auto-add, board lookup, and cleanup

## Runner Sanity Check

After pushing your fork, run **Actions -> Template sanity check -> Run workflow**.

Use the default project number unless your board is not Project 1. Leave **Create test issue** off for a read-only check; turn it on when you want to prove the runner can create an issue, let `auto-add-to-project` add it to the board, and close the temporary issue.

## External MicroVM Agents

If an agent runs outside GitHub Actions, give the microVM a secret named `GH_TOKEN` whose value is the same class of token as `PROJECT_TOKEN`.

Example environment contract:

```text
GH_TOKEN=<classic PAT or GitHub App installation token>
GH_REPO=YOUR_USERNAME/AgentArmy
PROJECT_NUMBER=1
```

Inside the microVM, prefer commands that name the repo and owner explicitly:

```bash
gh project item-list "$PROJECT_NUMBER" --owner YOUR_USERNAME --format json --limit 10
gh issue create --repo "$GH_REPO" --title "..." --body "..."
```

## Common Failure Patterns

| Symptom | Likely cause | Fix |
|---|---|---|
| `secrets.PROJECT_TOKEN` appears empty in a workflow | Secret was named `PAT` or added as a variable | Add a repository secret named `PROJECT_TOKEN` |
| `GITHUB_TOKEN` works for issues but not Projects | Built-in token is repository-scoped | Use `GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}` for project commands |
| Local `gh project item-list` works but Actions fail | Local keyring token is valid, runner secret is missing or stale | Reset `PROJECT_TOKEN` and rerun Template sanity check |
| Project defaults to the wrong board | `PROJECT_NUMBER` unset or wrong | Set `gh variable set PROJECT_NUMBER --repo OWNER/AgentArmy --body "N"` |
| Board commands can read but cannot comment | Token only has `project` scope | Add `repo` scope or use an installation token with Issues write permission |

## What Is Automated

Current automation coverage:

| Automation | Location | Purpose |
|---|---|---|
| Local sanity script | `scripts/onboarding-check.ps1` | Validate local and repo configuration before an agent starts work |
| Runner sanity workflow | `.github/workflows/template-sanity-check.yml` | Validate `PROJECT_TOKEN` and `PROJECT_NUMBER` from GitHub Actions |
| Auto-add workflow | `.github/workflows/auto-add-to-project.yml` | Add new issues and PRs to the configured Project |
| Board commands | `.github/workflows/board-commands.yml` | Let issue comments query board status |
| PI report | `.github/workflows/pi-report.yml` | Summarize project status on schedule or manual dispatch |

Good future automation candidates:

- a setup workflow that comments exact missing configuration after a failed sanity check
- a field-ID discovery script for `auto-status.yml`
- label bootstrap for `copilot-task` and `agent-army-task`
- a project bootstrap script that creates required fields and stores the resulting IDs
