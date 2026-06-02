# AGENTS.md

Shared guidance for AI agents working in AgentArmyPowerTemplate-derived repositories.

## Purpose

This repository is a template for AI-assisted GitHub and Markdown workflows. Treat repository changes as documentation, configuration, workflow, and agent-guidance work unless the derived repository clearly contains application code.

## Operating principles

1. Track non-trivial work in GitHub Issues before implementation.
2. Keep changes focused and reviewable.
3. Prefer existing scripts, workflows, and conventions over ad-hoc tooling.
4. Do not commit secrets, personal tokens, private project IDs, or environment-specific credentials.
5. Preserve the template boundary: reusable guidance belongs here; product- or organization-specific implementation belongs in the derived repository.

## Routing

Use `.agent/subagent-roster.md` as the compact routing index. Open only the relevant agent definition from `.claude/agents/categories/` or `.codex/agents/` when deeper expertise is needed.

| Work type | Default route |
|---|---|
| Small, bounded issue | GitHub Copilot coding agent (`copilot-task`) |
| Multi-file or architectural issue | Claude Code specialist agents (`ai-agent-task`) |
| PR under 200 changed lines | Copilot/code-review first pass |
| PR over 200 changed lines | Deep review with `code-reviewer`, `security-auditor`, or the relevant specialist |
| Ambiguous or high-impact decision | HITL decision artifact |

## Required checks

- Agent changes: `python scripts/validate_agents.py` and `python scripts/generate_agent_docs.py`.
- Docs changes: `python -m mkdocs build` after installing `requirements-docs.txt`.
- ADR changes: follow `docs/decisions/README.md`.
