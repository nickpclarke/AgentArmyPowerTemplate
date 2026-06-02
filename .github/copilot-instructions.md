# Copilot Coding Agent Instructions

You are working in the **AgentArmyPowerTemplate** repository. This is a reusable template, not an application.

## Deliverables

Expected changes are usually in:

- `.github/workflows/`
- `.github/ISSUE_TEMPLATE/`
- `.claude/agents/categories/`
- `.codex/`
- `docs/`
- Root Markdown and configuration files

Do not invent application source code unless the issue explicitly adds an example.

## Routing

Use the starter roster in `.agent/subagent-roster.md` to choose specialist context. For direct agent definitions, read only the relevant file under `.claude/agents/categories/`.

## Scope constraints

- `copilot-task`: bounded, low ambiguity, small change.
- `ai-agent-task`: multi-file, ambiguous, security-sensitive, or architecture-heavy change.
- PR bodies must include `Closes #N`, `Fixes #N`, or `Resolves #N`.

## Validation

Run relevant existing checks only:

- Agent definitions: `python scripts/validate_agents.py`.
- Generated agent docs: `python scripts/generate_agent_docs.py`.
- Docs build: `python -m mkdocs build` after installing `requirements-docs.txt`.
