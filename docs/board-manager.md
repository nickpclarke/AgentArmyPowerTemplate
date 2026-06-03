# Board Manager Extension

GitHub Copilot Chat extension for querying GitHub Projects v2 board.

## What is Board Manager?

`@board-manager` is an Azure-deployable Copilot Chat extension that lets you query the GitHub Projects board from Copilot Chat.

## Installation

[Instructions coming soon]

## Usage

In Copilot Chat, use `@board-manager` to ask board questions:

```
@board-manager What issues are in In Progress?
@board-manager Show me P0 issues for PI-1
@board-manager Who's working on the auth feature?
@board-manager List all stories in Ready status
```

## Example Queries

| Query | Response |
|-------|----------|
| `@board-manager What's my sprint status?` | Shows current sprint burndown |
| `@board-manager Show P0 bugs` | Lists all P0 severity bugs |
| `@board-manager Who has capacity?` | Shows available team members |
| `@board-manager What's blocked?` | Lists blocked issues |

## Setup

1. Deploy extension to Azure (see `extensions/board-manager/`)
2. Install in Copilot Chat
3. Enable in GitHub
4. Start querying

## Related Docs

- **[Copilot Army](copilot.md)**
- **[GitHub Projects](github-projects.md)**
