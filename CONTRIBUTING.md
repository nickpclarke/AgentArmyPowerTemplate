# Contributing to AgentArmy

Thanks for your interest in improving AgentArmy. The full contributor guide —
agent authoring conventions, doc style, MECE rules, and review expectations —
lives in **[docs/contributing.md](docs/contributing.md)**. This file is the
quick reference GitHub surfaces from the repo root.

## The essentials

1. **Track work as an issue first.** AgentArmy uses GitHub Projects as the task
   backbone — open an issue and add it to the board before significant work. See
   [docs/github-projects.md](docs/github-projects.md).
2. **Branch from `main`** and keep changes focused.
3. **Open a PR with `Closes #N`** (or `Fixes #N` / `Resolves #N`) in the body —
   this is required for the `auto-status` workflow to move the issue to *Done*.
4. **Keep PRs small.** PRs over 200 lines get the `needs-deep-review` label
   automatically; expect a deeper review.

## Local setup

- Git + GitHub CLI (`gh`)
- Python 3.11+ (docs build, helper scripts)
- Node.js 20+ (only if working on `extensions/board-manager/`)

Build the docs locally with `pip install -r requirements-docs.txt && mkdocs serve`.

## Adding or changing agents

Agent definitions live in `.claude/agents/categories/`. Each must have valid
frontmatter (`name`, `description`, `tools`, `model`) with `name` matching the
filename, and a non-overlapping (MECE) scope. The `validate-agents` CI check
enforces the frontmatter rules — run `python scripts/validate_agents.py` before
pushing. See [docs/contributing.md](docs/contributing.md) for the full agent
authoring guide.
