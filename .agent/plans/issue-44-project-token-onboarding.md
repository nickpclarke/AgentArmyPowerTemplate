# ExecPlan: Project Token Setup and Onboarding Sanity Checks

## Goal

Make AgentArmyPowerTemplate setup safer by documenting the difference between local GitHub CLI auth, GitHub Actions secrets, repository variables, and external microVM runner environment variables. Add an initial onboarding sanity-check path that can catch missing token and Project v2 configuration before real agent work starts.

## Context

Issue: `#44`

Observed setup failure: local `gh auth status` and `gh project item-list` can succeed while GitHub Actions still fails if the runner-side secret is missing, stale, or named incorrectly. The template workflows expect `secrets.PROJECT_TOKEN`; a secret named `PAT` is not read by default.

## Non-goals

- Do not implement an application runtime.
- Do not commit real token values.
- Do not require a destructive setup flow.
- Do not replace GitHub Projects v2 with another tracker.

## Source-of-Truth Files

- `AGENTS.md`
- `README.md`
- `docs/setup.md`
- `docs/onboarding.md`
- `.github/workflows/auto-add-to-project.yml`
- `.github/workflows/auto-status.yml`
- `.github/workflows/template-sanity-check.yml`

## Work Breakdown

1. Clarify token and variable naming in setup docs.
2. Add a reusable local sanity-check script.
3. Add a manual runner-side sanity-check workflow.
4. Add docs navigation and quick-start links.
5. Reduce hidden hardcoding by making `auto-status.yml` honor `PROJECT_NUMBER`.

## File Ownership

Codex owns this plan and the setup/onboarding docs for issue `#44`. Future workflow edits should keep `.github/workflows/*` changes narrow and verify with a manual sanity run.

## Validation

Run:

```powershell
.\scripts\onboarding-check.ps1 -Owner nickpclarke -Repo AgentArmyPowerTemplate -ProjectNumber 1
python -m mkdocs build
```

After merge/push, run the **Template sanity check** workflow from GitHub Actions. Use the optional test issue toggle when validating a new fork or runner secret.

## Risks

- The PowerShell sanity script depends on `gh` being installed and authenticated locally.
- The runner workflow can only prove `PROJECT_TOKEN` after it is saved as a repository secret.
- `auto-status.yml` still requires project field IDs and option IDs to match the target board.

## Decision Log

- Use `PROJECT_TOKEN` as the canonical runner secret name.
- Use `PROJECT_NUMBER` as a repository variable, not a secret.
- Keep the local script non-destructive by default; make issue creation opt-in.
- Add a manual workflow rather than running sanity checks on every push.

## Future Automation Candidates

- Script field-ID discovery for `auto-status.yml`.
- Bootstrap labels such as `copilot-task` and `agent-army-task`.
- Bootstrap required Project v2 fields and store generated IDs.
- Have failed sanity checks comment exact missing configuration on the workflow summary.
