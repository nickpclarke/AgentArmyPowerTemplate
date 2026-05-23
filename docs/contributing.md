# Contributing to AgentArmy

## Getting Started

AgentArmy is a collaborative template for AI-powered software development. Contributions are welcome and encouraged.

### Prerequisites

- Git and GitHub CLI (`gh`)
- Python 3.11+ (for local testing)
- MkDocs tooling (`python3 -m pip install -r requirements-docs.txt`)
- A fork of the repository

Install docs dependencies once:

```bash
python3 -m pip install -r requirements-docs.txt
```

### Development Workflow

1. **Create an issue** on GitHub Projects describing your contribution
2. **Create a feature branch** from `main`
3. **Make your changes** — see guidelines below
4. **Test locally** — run `python3 -m mkdocs build`, check formatting
5. **Open a PR** with `Closes #N` in the body
6. **Address review feedback**
7. **Merge and celebrate!**

## Types of Contributions

### Documentation

**When to contribute docs:**
- Fix typos or clarify existing docs
- Add examples to agent definitions
- Expand guides with new use cases
- Document new agents or workflows

**Guidelines:**
- Use Material for MkDocs syntax
- Link related sections (e.g., "See [Armies Overview](armies-overview.md)")
- Include decision criteria and trade-offs, not just facts
- Add example code blocks where helpful

**Files to edit:**
- `docs/` — User-facing documentation
- `.claude/agents/categories/` — Agent definitions
- `CLAUDE.md` — Project instructions

### Agents

**When to add an agent:**
- You identify a new specialist not in the roster
- Existing agents don't cover a specific domain
- You want to customize agents for your team

**Guidelines:**
- Read [.claude/agents/categories/](https://github.com/nickpclarke/AgentArmy/tree/main/.claude/agents/categories) for structure
- Ensure MECE compliance: non-overlapping scope
- Run `/agent-distinctiveness-advocate` to validate
- Document use cases and routing criteria

**Agent template:**
```
# {{Agent Name}}

**Specialty**: {{One sentence}}

## When to delegate

- {{Use case 1}}
- {{Use case 2}}

## How to delegate

1. Create issue with {{requirements}}
2. {{Any special setup}}
3. Agent handles from there

## Tools available

{{Lists MCP tools, write capabilities, etc.}}

## Related agents

- {{Overlapping/complementary agents}}
```

### Workflows & Automation

**When to contribute workflows:**
- Add new GitHub Actions for automation
- Extend board automation
- Add CI/CD pipelines

**Guidelines:**
- Test on a feature branch
- Use secrets safely (no hardcoding credentials)
- Document trigger conditions
- Add to `.github/workflows/`

**Workflow template:**
```yaml
name: {{Clear descriptive name}}
on:
  push:
    branches:
      - main
  pull_request:

jobs:
  {{job}}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ...
```

### Data Pipelines (dlt)

**When to contribute pipelines:**
- Add new source connector
- Improve incremental loading
- Wire new destination
- Optimize schema handling

**Guidelines:**
- Place in `pipelines/dlt_pipelines/sources/{{source_name}}/`
- Include tests in `pipelines/tests/`
- Document API requirements and auth
- Use dlt best practices (incremental loading, type inference)

**Source structure:**
```
source_name/
├── __init__.py
├── pipeline.py          # Extraction logic
├── schema.py            # Type hints and schema
└── README.md            # Docs and examples
```

### Code Quality

**Standards:**
- **Python**: PEP 8, type hints where possible
- **YAML**: 2-space indentation
- **Markdown**: Consistent formatting, links relative to docs/
- **Commits**: Clear, concise messages with issue reference

**Tools:**
```bash
# Format Python code
black pipelines/

# Lint
flake8 pipelines/

# Type check
mypy pipelines/

# Build docs locally
python3 -m mkdocs build

# Serve docs locally
python3 -m mkdocs serve
```

## Review Process

### For Documentation PRs
1. Check for typos and grammar
2. Verify links work
3. Ensure consistency with style guide
4. Review for accuracy

### For Agent PRs
1. Run `/agent-distinctiveness-advocate` audit
2. Check MECE compliance
3. Verify routing decision matrix
4. Confirm examples are accurate

### For Workflow PRs
1. Test on feature branch first
2. Check for security issues (secrets, permissions)
3. Verify trigger conditions
4. Ensure auto-status compatibility

### For Pipeline PRs
1. Check schema inference
2. Verify incremental loading works
3. Test with sample data
4. Review error handling

## Reporting Issues

### Security Issues
**Do not** create public issues for security vulnerabilities.
- Email: [security contact, if available]
- Or use GitHub Security Advisory

### Bugs
Create an issue with:
- Clear title
- Reproduction steps
- Expected vs actual behavior
- Environment (OS, Python version, etc.)

### Feature Requests
Create an issue with:
- Clear title and description
- Why it's needed
- Proposed solution (if known)
- Alternative approaches

## Code of Conduct

- Be respectful and inclusive
- Assume good intent
- Provide constructive feedback
- Help others succeed

## Questions?

- **Setup help**: See [setup.md](setup.md)
- **Agent routing**: See [routing-matrix.md](routing-matrix.md)
- **FAQs**: See [faq.md](faq.md)
- **GitHub Issues**: Ask in a GitHub Discussion

---

## Quick Reference

| Task | File | Agent |
|------|------|-------|
| Fix docs typo | `docs/` | (create issue) |
| Add agent | `.claude/agents/categories/` | (create issue) |
| Add workflow | `.github/workflows/` | `devops-engineer` |
| Add pipeline source | `pipelines/dlt_pipelines/sources/` | `dlt-engineer` |
| Update CLAUDE.md | `CLAUDE.md` | (create issue) |

## Related Docs

- **[Setup Guide](setup.md)** — Environment setup
- **[Routing Matrix](routing-matrix.md)** — How to find the right specialist
- **[Agent Roster](agents.md)** — specialist agent definitions
- **[FAQ](faq.md)** — Common questions
