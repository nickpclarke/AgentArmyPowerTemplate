# GitHub Copilot

Use GitHub Copilot for small, bounded issues and first-pass PR review.

## Routing labels

- `copilot-task`: clear scope, small change, low ambiguity.
- `ai-agent-task`: larger or ambiguous work better suited to Claude Code specialist agents.

## Repository guidance

Copilot coding agent reads `.github/copilot-instructions.md` and setup steps from `.github/copilot-setup-steps.yml`.

Keep these files generic so derived repositories can adopt them safely.
