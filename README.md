# AgentArmyPowerTemplate

AgentArmyPowerTemplate is a reusable GitHub repository template for AI-powered Markdown-first delivery. It packages documentation practices, specialist-agent guidance, GitHub Projects workflows, issue and pull-request conventions, and a MkDocs site without assuming any specific application runtime.

## What is included

- Markdown guidance for humans, Claude Code, Codex, and GitHub Copilot.
- A starter specialist-agent roster for planning, engineering, documentation, delivery, quality, and review work.
- GitHub Actions for Projects v2 board automation, PR review routing, stale-item hygiene, ADR numbering, acronym coverage, and docs publishing.
- Issue templates, PR template, security policy, routing policy, and CODEOWNERS placeholders.
- MkDocs Material documentation organized around setup, collaboration, agent guidance, delivery practices, and ADRs.
- Optional MemPalace documentation for teams that want cross-session memory hooks.

## Quick start

1. Create a new repository from this template.
2. Replace placeholder owner/repository URLs in `mkdocs.yml`, `.github/CODEOWNERS`, and any setup examples.
3. Optionally create a GitHub Projects v2 board and set repository variable `PROJECT_NUMBER`.
4. To enable board automation, set repository variable `PROJECT_AUTOMATION_ENABLED` to `true` and create a `PROJECT_TOKEN` secret with the minimum scopes needed to read/write the project board. Board additions, status sync, and PI reports are disabled by default; configured authentication failures remain errors.
5. Install documentation dependencies and build the site:

```bash
pip install -r requirements-docs.txt
python scripts/validate_agents.py
python scripts/generate_agent_docs.py
python -m mkdocs build
```

See `docs/setup.md` and `docs/quick-start.md` for the complete template adoption path.

## Starter labels

- `copilot-task` — bounded issues suitable for GitHub Copilot coding agent.
- `ai-agent-task` — complex or multi-file issues for Claude Code / local specialist agents.
- `needs-deep-review` — large PRs that should receive deeper human or agent review.
- `hitl-decision` / `awaiting-human` — decision artifacts and blocked work.

## License

This template is provided under the MIT License. Review `LICENSE` before publishing a derived repository.
