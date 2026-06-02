# CONSTITUTION.md

Behavioral principles for agents operating in AgentArmyPowerTemplatePowerTemplate-derived repositories.

## Article I — Template neutrality

Keep reusable template content separate from organization-specific implementation. Public template files should use placeholders for owners, repository names, project numbers, URLs, IDs, and secrets.

## Article II — Work is tracked

Non-trivial work starts from an issue and ends in a pull request that references the issue with `Closes #N`, `Fixes #N`, or `Resolves #N`.

## Article III — Small, reviewable changes

Prefer focused changes. Escalate large, cross-cutting, or ambiguous work from `copilot-task` to `ai-agent-task`.

## Article IV — Human-in-the-loop decisions

Create a decision artifact for irreversible, security-sensitive, policy, licensing, or architecture choices. Keep blocked work labeled `awaiting-human` until the decision is resolved.

## Article V — No secrets

Never commit credentials, private project IDs, production URLs, or personal workspace data. Rotate any exposed secret immediately.
