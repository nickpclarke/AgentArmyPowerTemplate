# Setup

## 1. Create the repository

Create a new repository from the template and replace placeholders such as `OWNER`, `PROJECT_NUMBER`, and repository URLs.

## 2. Configure GitHub Projects

Create a GitHub Projects v2 board with these recommended fields:

| Field | Type | Example values |
|---|---|---|
| Status | Single select | Todo, Ready, In Progress, In Review, Awaiting Decision, Done |
| Type | Single select | Epic, Feature, Story, Bug, Spike, Enabler, Decision |
| Priority | Single select | P0, P1, P2, P3 |
| Size | Single select | XS, S, M, L, XL |
| PI | Text | PI-1 |
| Iteration | Iteration | Team cadence |

Set repository variable `PROJECT_NUMBER` to the board number.

## 3. Configure token access

Create a repository secret named `PROJECT_TOKEN` with the minimum permissions needed for Projects v2 automation in your organization.

## 4. Validate locally

```bash
pip install -r requirements-docs.txt
python scripts/validate_agents.py
python scripts/generate_agent_docs.py
python scripts/generate_subagent_roster.py
python -m mkdocs build
```

## 5. Publish docs

Enable GitHub Pages and run the `Deploy Documentation` workflow.
