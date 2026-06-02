# AI Coordination

This template coordinates GitHub Copilot, Claude Code, and human reviewers through GitHub Issues, PRs, and Projects v2.

## Flow

1. Issue is created and added to the project board.
2. A routing label is applied:
   - `copilot-task` for bounded work.
   - `ai-agent-task` for larger specialist-agent work.
3. PR opens with `Closes #N`.
4. Size label and review automation run.
5. Linked issue moves to Done when the PR merges.

## Escalation

Use `awaiting-human` and a `hitl-decision` issue when a decision affects security, licensing, governance, or long-lived architecture.
