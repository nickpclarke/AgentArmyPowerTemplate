# CLAUDE.md

Claude Code guidance for AgentArmyPowerTemplate.

## Repository role

AgentArmyPowerTemplate is a reusable template, not an application. Default work products are Markdown, GitHub Actions, issue/PR templates, agent definitions, and MkDocs configuration.

## Working rules

- Read `AGENTS.md` first for shared routing guidance.
- Keep the template generic: replace organization-specific names, URLs, project IDs, and secrets with placeholders.
- Use the starter agent roster in `.claude/agents/categories/` for specialist review lenses.
- Use `copilot-task` for small GitHub-native tasks and `ai-agent-task` for larger Claude Code work.
- Use HITL decision artifacts when a choice affects governance, security, public release posture, or long-lived workflow design.

## Validation commands

```bash
python scripts/validate_agents.py
python scripts/generate_agent_docs.py
python scripts/generate_subagent_roster.py
python scripts/sync_agents_to_codex.py
python scripts/sync_agents_to_antigravity.py
python -m mkdocs build
```

Install docs dependencies with `pip install -r requirements-docs.txt` before building docs.

## Optional memory hooks

MemPalace is documented as an optional integration. Do not enable persistence hooks by default in a public template; teams can opt in after reviewing their privacy and retention requirements.
