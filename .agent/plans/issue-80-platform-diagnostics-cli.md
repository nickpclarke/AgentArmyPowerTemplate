# ExecPlan: Platform Diagnostics CLI

Issue: https://github.com/nickpclarke/AgentArmy/issues/80

## Goal

Design and then implement a high-quality development CLI that can test the active frontend, backend, ArcadeDB, and future containerized microservices in the AgentArmy ecosystem. The CLI should become the fast local truth surface for "is my platform slice healthy?" while also emitting structured artifacts that other pages, cockpit panels, GitHub summaries, and docs can render.

## Context

AgentArmy is a starter template, not a product application. This work belongs in reusable template tooling and documentation, with optional adapters for current proof surfaces such as `extensions/arcadedb-cockpit/`. The existing ArcadeDB cockpit already has a server-side proxy, read-only defaults, and a future backend contract. The CLI should reuse those ideas instead of creating a separate database access model.

The ecosystem is expected to expand into multiple spokes, services, and containers. The CLI therefore needs service discovery and adapter contracts, not a single hard-coded frontend/backend/database script.

## Non-Goals

- Do not implement product application functionality.
- Do not require ArcadeDB, a frontend, or a backend to be running for basic CLI self-checks.
- Do not expose raw credentials, provider keys, or ArcadeDB root passwords in terminal output or JSON artifacts.
- Do not replace existing service-specific test runners; orchestrate them and normalize their results.
- Do not couple the CLI to one cloud provider or one container runtime beyond adapter boundaries.

## Relevant Docs and Source-of-Truth Files

- `AGENTS.md`
- `docs/onboarding.md`
- `docs/diagnostics-standards.md`
- `docs/cloud-serving.md`
- `docs/gcp-cloud-run-pipeline.md`
- `docs/board-manager.md`
- `extensions/arcadedb-cockpit/README.md`
- `extensions/arcadedb-cockpit/BACKEND_CONTRACT.md`
- `.agent/plans/issue-78-arcadedb-cockpit.md`
- `scripts/onboarding-check.ps1`
- `templates/gcp-cloud-run/README.md`

## Standards Defined

This work introduced the repo-wide diagnostics standards in `docs/diagnostics-standards.md`.

The standards define:

- One CLI command surface for broad platform checks.
- Adapter-first diagnostic boundaries.
- Manifest-before-guesswork service discovery.
- Stable `doctor.v1` artifact envelopes.
- Status, severity, and exit-code semantics.
- Secret-safe evidence and browser-surface constraints.
- Offline-safe defaults and strict-mode behavior.
- Generated artifact ownership under `tests/artifacts/doctor/`.
- Page/dashboard consumption through artifacts instead of duplicated probes.
- CI expectations for offline-safe diagnostics workflows.
- Documentation and naming requirements for future adapters.

## Proposed CLI Shape

Command: `node tools/agentarmy-doctor.mjs`.

The command model should be stable enough to use locally and in CI:

| Command | Purpose | Output consumers |
|---|---|---|
| `node tools/agentarmy-doctor.mjs` | Run the default local readiness suite across repo, tools, services, and configured containers. | Terminal, CI summary, latest JSON artifact |
| `node tools/agentarmy-doctor.mjs services` | Discover configured services and report health, ports, compose status, and expected URLs. | Dev dashboard, service catalog |
| `node tools/agentarmy-doctor.mjs frontend` | Run configured frontend build/lint/smoke checks when a spoke declares a frontend. | PR checks, local page status |
| `node tools/agentarmy-doctor.mjs backend` | Run backend health, OpenAPI/schema, smoke, and contract probes when a backend is declared. | PR checks, API docs |
| `node tools/agentarmy-doctor.mjs arcadedb` | Probe ArcadeDB readiness, databases, schema inventory, and query policy. | Arcade cockpit, graph pages |
| `node tools/agentarmy-doctor.mjs containers` | Inspect compose or container runtime state, image age, port bindings, logs, and restart loops. | Ops pages, CI artifacts |
| `node tools/agentarmy-doctor.mjs contracts` | Validate API, event, and database adapter contracts without needing every service online. | Release gates |
| `node tools/agentarmy-doctor.mjs export` | Re-render the latest run as JSON, Markdown, or static page data. | Docs, dashboards, GitHub summaries |

## Output Contract

Every command should support human and machine output:

```text
node tools/agentarmy-doctor.mjs --format table
node tools/agentarmy-doctor.mjs --format json --output tests/artifacts/doctor/latest.json
node tools/agentarmy-doctor.mjs arcadedb --format markdown --output tests/artifacts/doctor/arcadedb.md
node tools/agentarmy-doctor.mjs --write-artifacts
```

The JSON artifact should use a normalized envelope:

```json
{
  "schema_version": "doctor.v1",
  "run_id": "2026-05-24T12-00-00Z-local",
  "generated_at": "2026-05-24T12:00:00Z",
  "scope": "local",
  "status": "pass",
  "summary": {
    "pass": 12,
    "warn": 2,
    "fail": 0,
    "skip": 3
  },
  "checks": [
    {
      "id": "arcadedb.health",
      "component": "arcadedb",
      "status": "pass",
      "severity": "required",
      "duration_ms": 42,
      "message": "ArcadeDB ready",
      "evidence": {
        "url": "http://localhost:2480",
        "database": "knowledge"
      },
      "redactions": []
    }
  ],
  "artifacts": [
    {
      "kind": "markdown",
      "path": "tests/artifacts/doctor/latest.md"
    }
  ]
}
```

Status values: `pass`, `warn`, `fail`, `skip`, and `error`.

Severity values: `required`, `recommended`, and `informational`.

## Adapter Model

Adapters should be small modules with a common interface:

- `discover(context)`: identify whether the adapter applies.
- `plan(context)`: list checks and prerequisites.
- `run(context)`: execute checks and return normalized results.
- `render(context)`: optionally contribute dashboard-specific fragments.

Initial adapters:

- Repo/tooling adapter: GitHub CLI auth, Project board visibility, Node/Python/MkDocs availability, sync scripts.
- Frontend adapter: package manager, build script, dev server smoke endpoint, static asset existence, browser smoke hook.
- Backend adapter: health endpoint, OpenAPI endpoint, migrations/schema readiness, smoke requests, contract probes.
- ArcadeDB adapter: health, database list, schema snapshot, graph snapshot, read-only query guard, telemetry.
- Container adapter: Docker/Podman availability, compose project status, port collisions, restart loops, log excerpt redaction.
- Artifact adapter: writes JSON, Markdown, and page-data fragments under `tests/artifacts/doctor/`.

## File Ownership

Planning owner:

- `.agent/plans/issue-80-platform-diagnostics-cli.md`
- `docs/platform-diagnostics-cli.md`
- `mkdocs.yml`

Future implementation owners should use disjoint write scopes:

- CLI/tooling owner: `tools/doctor/**` or `tools/agentarmy-doctor.mjs`
- Artifact owner: `tests/artifacts/doctor/**`
- ArcadeDB owner: `extensions/arcadedb-cockpit/**` only when integrating rendered results into the cockpit
- Docs owner: `docs/platform-diagnostics-cli.md`, `docs/onboarding.md`, and setup references
- CI owner: `.github/workflows/**` only after local command behavior is stable

## Subagents To Use

Implementation should use a small pod:

- `cli-developer`: command taxonomy, flags, help, exit codes, and cross-platform command UX.
- `platform-engineer`: service discovery, adapter boundaries, and golden-path developer workflow.
- `backend-developer` or `api-designer`: backend and contract probe shapes.
- `docker-expert`: container runtime and compose diagnostics.
- `database-administrator` plus `security-auditor`: ArcadeDB checks and credential handling.
- `test-automator` or `qa-expert`: validation matrix and CI gates.
- `documentation-engineer`: docs, examples, and artifact consumption guidance.

Reviewers should be advisory unless assigned a disjoint file set.

## Work Breakdown

1. Planning and contract
   - Add this ExecPlan.
   - Add a docs page with command taxonomy, output contract, and milestone plan.
   - Confirm issue #80 is on the Project board.

2. CLI skeleton
   - Status: implemented.
   - Added a dependency-light Node CLI.
   - Added `--help`, `--format`, `--output`, `--component`, `--strict`, `--timeout-ms`, `--write-artifacts`, and stable exit-code behavior.

3. Local adapters
   - Status: implemented for first pass.
   - Added repo/tooling, ArcadeDB, container, contract, frontend, and backend adapters.
   - Offline service states are warnings or skips unless explicitly required by `--strict`.
   - ArcadeDB result fields reuse the credential-free cockpit contract posture.

4. Frontend/backend adapters
   - Status: implemented for first pass.
   - Uses `agentarmy.services.json` or `.agent/services.json`.
   - Supports optional smoke URLs, build commands, test commands, health endpoints, and OpenAPI paths.

5. Artifact surfacing
   - Status: implemented for first pass.
   - `--write-artifacts` writes `tests/artifacts/doctor/latest.json` and `latest.md`.
   - ArcadeDB cockpit can ingest the latest JSON artifact without reading secrets.

6. CI and project integration
   - Status: implemented for first pass.
   - Added a workflow that runs non-secret, offline-safe checks on PRs.
   - The workflow writes JSON/Markdown artifacts and appends the Markdown report to the GitHub step summary.

## Tests and Validation

Planning validation:

- `node --check extensions/arcadedb-cockpit/server.js`
- `node --check extensions/arcadedb-cockpit/public/app.js`
- `node --check tools/agentarmy-doctor.mjs`
- `node tools/agentarmy-doctor.mjs --write-artifacts`
- `python -m mkdocs build --strict`

Implementation validation:

- CLI help exits 0.
- Default doctor run exits 0 when optional services are offline and reports skips/warnings clearly.
- `--strict` exits non-zero when required services fail.
- JSON output validates against the checked-in schema.
- Artifact paths are deterministic and do not include secrets.
- ArcadeDB adapter can run in offline mode and online mode.
- Container adapter handles Docker missing, Docker stopped, no compose project, and healthy compose project.

## Risks

- A too-clever discovery layer could become fragile across many service types. Prefer explicit manifests first, with detection as a convenience.
- If the CLI directly talks to every service, it may duplicate backend contracts. Prefer adapters that validate existing contracts.
- Rendering CLI output into pages can accidentally expose environment details. Redaction needs to be part of the output contract, not a later polish pass.
- CI checks can become noisy if optional local-only services are treated as required by default.

## Decision Log

- Use a normalized CLI artifact as the bridge between terminal diagnostics and future pages. Implemented as `tools/agentarmy-doctor.mjs`.
- Keep the ArcadeDB browser credential-free pattern from the cockpit as a hard constraint for CLI output too.
- Treat the first implementation as template tooling, not product application code.
- Prefer adapter contracts and service manifests over one-off scripts as the platform grows.
- Keep diagnostics standards in `docs/diagnostics-standards.md` so future adapters inherit the same artifact, redaction, CI, and page-surfacing rules.
