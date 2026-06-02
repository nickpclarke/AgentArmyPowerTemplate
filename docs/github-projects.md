# GitHub Projects

GitHub Projects v2 is the shared planning surface for humans and agents.

## Required configuration

- Repository variable: `PROJECT_NUMBER`.
- Repository secret: `PROJECT_TOKEN`.
- Board fields: Status, Type, Priority, Size, PI, Iteration.

## Automation

| Workflow | Purpose |
|---|---|
| `auto-add-to-project.yml` | Adds new issues and PRs to the board. |
| `auto-status.yml` | Moves linked issues to In Progress or Done based on PR state. |
| `board-commands.yml` | Handles slash commands such as `/board-status`, `/sprint`, and `/blocked`. |
| `pi-report.yml` | Writes a scheduled board summary. |
| `template-sanity-check.yml` | Validates token and board access. |

Keep field names stable or update workflows and docs together.
