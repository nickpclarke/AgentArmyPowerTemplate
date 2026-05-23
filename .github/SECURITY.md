# Security Policy

## Reporting a vulnerability

Please report security issues privately rather than opening a public issue.

- Use **GitHub Security Advisories** ("Report a vulnerability" under the repo's
  **Security** tab), or
- Email the maintainer at the address on their GitHub profile.

Include enough detail to reproduce (affected file/workflow, steps, and impact).
We aim to acknowledge reports within a few business days.

## Scope notes for this template

AgentArmy is a template repo, so a few things are worth calling out for anyone
forking it:

- **Never commit secrets.** `.claude/settings.local.json`, `.env`, and
  `extensions/board-manager/.env` are gitignored because they hold credentials.
  If a secret is ever committed, rotate it immediately — removing it from the
  latest commit does not remove it from history.
- **`PROJECT_TOKEN`** is a classic PAT with the `project` scope used by the
  board-syncing workflows. Treat it as sensitive and scope it to the minimum
  required.
- Workflow automation runs with elevated tokens; review changes under
  `.github/workflows/` and `scripts/` with care.
