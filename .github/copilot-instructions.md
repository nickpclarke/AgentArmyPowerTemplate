# Copilot Coding Agent Instructions

You are working in the **AgentArmy** template repository. This is a starter template — not an application. There is no source code to build or run.

## What You Deliver

Changes to:

- GitHub Actions workflows in `.github/workflows/`
- Agent definitions in `.claude/agents/categories/`
- Documentation in `docs/`
- Configuration files at the repo root

**There is no `index.html` or app to work on.** When an issue asks you to "implement something", it means updating docs, workflows, or config — not writing application code.

## Sub-Agent Specialist Knowledge

This repo contains 168+ specialist agent definitions in `.claude/agents/categories/`. **Before starting work on any issue, consult the relevant specialist definition to adopt its expertise.**

### How to Use Sub-Agents

1. Determine the task domain from the issue (e.g., documentation, CI/CD, security, frontend)
2. Find the matching specialist in the routing table below
3. **Read the agent's `.md` file** from `.claude/agents/categories/<category>/<agent-name>.md`
4. Adopt that specialist's approach, constraints, and quality standards when implementing

### Agent Routing Table

| Task Domain | Agent | Path |
|---|---|---|
| Documentation, READMEs | `documentation-engineer` | `06-developer-experience/documentation-engineer.md` |
| GitHub Actions, CI/CD pipelines | `devops-engineer` | `03-infrastructure/devops-engineer.md` |
| Deployment, releases | `deployment-engineer` | `03-infrastructure/deployment-engineer.md` |
| Security hardening | `security-engineer` | `03-infrastructure/security-engineer.md` |
| Code review quality | `code-reviewer` | `04-quality-security/code-reviewer.md` |
| Test automation | `test-automator` | `04-quality-security/test-automator.md` |
| Frontend / UI work | `frontend-developer` | `01-core-development/frontend-developer.md` |
| Backend / API work | `backend-developer` | `01-core-development/backend-developer.md` |
| API design, OpenAPI | `api-designer` | `01-core-development/api-designer.md` |
| Python code | `python-pro` | `02-language-specialists/python-pro.md` |
| TypeScript code | `typescript-pro` | `02-language-specialists/typescript-pro.md` |
| Go code | `golang-pro` | `02-language-specialists/golang-pro.md` |
| Docker, containers | `docker-expert` | `03-infrastructure/docker-expert.md` |
| Kubernetes | `kubernetes-specialist` | `03-infrastructure/kubernetes-specialist.md` |
| Terraform / IaC | `terraform-engineer` | `03-infrastructure/terraform-engineer.md` |
| Database work | `database-administrator` | `03-infrastructure/database-administrator.md` |
| Performance issues | `performance-engineer` | `04-quality-security/performance-engineer.md` |
| Accessibility | `accessibility-tester` | `04-quality-security/accessibility-tester.md` |
| CLI tools | `cli-developer` | `06-developer-experience/cli-developer.md` |
| Refactoring | `refactoring-specialist` | `06-developer-experience/refactoring-specialist.md` |

**Full catalog:** Browse `.claude/agents/categories/` — 11 category folders with all specialists.

### Example

If the issue asks you to "update the deploy-docs workflow", you would:

1. Read `.claude/agents/categories/03-infrastructure/devops-engineer.md`
2. Adopt its CI/CD expertise and quality standards
3. Then implement the workflow change

## Conventions

### PR Body

Your PR body **must** include `Closes #N` (where N is the issue number) to trigger the auto-status workflow that moves the issue to Done on the project board.

### Scope Constraints

- Keep changes to **≤ 50 lines per file** for copilot-task issues
- Stick to **single file or tightly related files**
- If the task touches multiple unrelated systems, comment on the issue suggesting escalation to `agent-army-task` label instead

### File Quality

- Follow existing patterns in adjacent files
- Do not add new dependencies unless the issue explicitly requires them
- Match the documentation style of surrounding `.md` files

## Environment

This template repo uses:

- **Python 3.x** with MkDocs for documentation (`requirements-docs.txt`)
- **Node.js** for the optional board-manager extension
- **GitHub Actions** for all automation

## Hub vs Spoke Context

You are in the **Hub repo** (the AgentArmy template itself). All deliverables are template artifacts. Do not assume an application exists or try to build/run one.
