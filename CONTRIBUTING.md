# Contributing to AgentArmyPowerTemplatePowerTemplate

Thanks for improving the template. The full guide lives in `docs/contributing.md`; this file is the root quick reference.

## Essentials

1. Open or select an issue before significant work.
2. Keep changes focused and generic.
3. Link PRs with `Closes #N`, `Fixes #N`, or `Resolves #N`.
4. Update docs when workflows, conventions, or agent behavior changes.
5. Run the relevant validation command before requesting review.

## Common validation

```bash
pip install -r requirements-docs.txt
python scripts/validate_agents.py
python scripts/generate_agent_docs.py
python -m mkdocs build
```
