# Contributing

## Workflow

1. Start from an issue.
2. Pick the correct routing label.
3. Keep the PR focused.
4. Link the issue from the PR body.
5. Run validation.

## Agent changes

Agent definitions live under `.claude/agents/categories/`. Each file must include YAML frontmatter with `name`, `description`, `tools`, and `model`.

Run:

```bash
python scripts/validate_agents.py
python scripts/generate_agent_docs.py
python scripts/generate_subagent_roster.py
python scripts/sync_agents_to_codex.py
python scripts/sync_agents_to_antigravity.py
```

## Docs changes

Build docs before review:

```bash
python -m mkdocs build
```
