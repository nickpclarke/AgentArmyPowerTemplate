# Platform Diagnostics CLI

The platform diagnostics CLI is the proposed local and CI command surface for answering a simple question: "Is this platform slice healthy enough to keep working?"

It should test the parts AgentArmy expects to grow around: frontend spokes, backend APIs, ArcadeDB, container runtimes, contract files, and generated artifacts. It should also produce normalized output that pages can consume later, rather than trapping useful status in terminal text.

The durable standards for this class of tooling live in [Diagnostics Standards](diagnostics-standards.md). This page describes the current CLI implementation.

## Why It Matters

AgentArmy is a template for coordinated agent work, so diagnostics need to be reusable across many future spokes. A single hard-coded script for one frontend, one backend, and one database will not age well. The CLI should be adapter-based: each service declares enough metadata for the CLI to discover it, run the right probes, and normalize the result.

This also gives agents a shared proof surface. Instead of saying "I think the backend works," an agent can run a command, attach the artifact, and let PM, scrum, QA, docs, and engineering views render the same evidence.

## Working Command Model

Command:

```powershell
node tools/agentarmy-doctor.mjs
```

Initial commands:

| Command | Purpose |
|---|---|
| `node tools/agentarmy-doctor.mjs` | Run the default local readiness suite. |
| `node tools/agentarmy-doctor.mjs services` | Discover configured services and expected URLs. |
| `node tools/agentarmy-doctor.mjs frontend` | Run frontend build, lint, and smoke checks when a frontend is declared. |
| `node tools/agentarmy-doctor.mjs backend` | Run health, OpenAPI/schema, smoke, and contract checks when a backend is declared. |
| `node tools/agentarmy-doctor.mjs arcadedb` | Probe ArcadeDB health, databases, schema, and read-only policy. |
| `node tools/agentarmy-doctor.mjs containers` | Inspect compose/runtime state, port bindings, logs, and restart loops. |
| `node tools/agentarmy-doctor.mjs contracts` | Validate service, API, event, and database contracts. |
| `node tools/agentarmy-doctor.mjs export` | Render the latest run for docs, dashboards, cockpit panels, and CI summaries. |

## Output Formats

Every command should support human and machine output:

```powershell
node tools/agentarmy-doctor.mjs --format table
node tools/agentarmy-doctor.mjs --format json --output tests/artifacts/doctor/latest.json
node tools/agentarmy-doctor.mjs arcadedb --format markdown --output tests/artifacts/doctor/arcadedb.md
node tools/agentarmy-doctor.mjs --write-artifacts
node tools/doctor/validate-artifact.mjs tests/artifacts/doctor/latest.json
```

For optional local container proof, use the manual [Local Docker CI](local-docker-ci.md) workflow. It runs hosted-style diagnostics first, then builds the root Dockerfile or a declared compose stack on a trusted self-hosted runner with the `docker-local` label.

The JSON envelope should stay stable:

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
  "checks": [],
  "artifacts": []
}
```

Status values should be `pass`, `warn`, `fail`, `skip`, and `error`.

Severity values should be `required`, `recommended`, and `informational`.

## Adapter Pattern

Adapters follow the repo-wide standards in [Diagnostics Standards](diagnostics-standards.md#standard-2-adapter-first-checks).

Each adapter should implement the same lifecycle:

| Step | Responsibility |
|---|---|
| `discover` | Decide whether this adapter applies in the current repo or spoke. |
| `plan` | List checks, prerequisites, and default severity. |
| `run` | Execute probes and return normalized check results. |
| `render` | Optionally contribute Markdown, JSON fragments, or page data. |

Initial adapters:

| Adapter | Checks |
|---|---|
| Repo/tooling | GitHub CLI, Project board access, Node, Python, MkDocs, sync scripts. |
| Frontend | Package manager, build script, dev URL, static assets, browser smoke hook. |
| Backend | Health endpoint, OpenAPI endpoint, migrations/schema readiness, smoke requests. |
| ArcadeDB | Readiness, database list, schema snapshot, graph snapshot, read-only query guard, telemetry. |
| Containers | Docker/Podman availability, compose status, image age, port conflicts, restart loops. |
| Artifacts | JSON, Markdown, and static page-data exports under `tests/artifacts/doctor/`. |

## Service Manifest

Frontend and backend checks are manifest-driven. Copy `templates/service-manifest.example.json` to `agentarmy.services.json` or `.agent/services.json` in a spoke repo, then edit the paths and commands.

```json
{
  "schema_version": "agentarmy.services.v1",
  "services": [
    {
      "name": "web",
      "kind": "frontend",
      "path": "apps/web",
      "build": "npm run build",
      "test": "npm test",
      "health_url": "http://127.0.0.1:3000",
      "required": false
    },
    {
      "name": "api",
      "kind": "backend",
      "path": "services/api",
      "test": "pytest",
      "health_url": "http://127.0.0.1:8000/health",
      "openapi": "openapi.json",
      "required": false
    }
  ]
}
```

When no manifest exists, frontend and backend checks are skipped in normal mode and fail in strict mode.

## ArcadeDB Boundary

The ArcadeDB adapter should reuse the current cockpit contract:

- Keep database credentials outside browser JavaScript and rendered pages.
- Prefer `ARCADEDB_PASSWORD_FILE` for mounted runtime secrets; accept `ARCADEDB_PASSWORD` only when injected by a runtime secret channel.
- Default to read-only probes.
- Redact secrets and connection strings in all outputs.
- Enforce limits on schema, graph, query, and traversal checks.
- Report offline ArcadeDB as `warn` or `skip` by default, and as `fail` only in strict mode or an environment that declares ArcadeDB required.

The existing cockpit can later read `tests/artifacts/doctor/latest.json` or a narrower `arcadedb.json` export to display CLI evidence without owning every probe directly.

The local ArcadeDB cockpit now exposes `GET /api/doctor`, which returns the latest doctor artifact when `tests/artifacts/doctor/latest.json` exists. This keeps the cockpit credential-free while still letting it show development diagnostics.

See [ArcadeDB Secret Hardening](arcadedb-secret-hardening.md) for the shared secret handling standard across local Docker, GitHub automation, and cloud workload targets.

## Standards Checklist

Before adding a new diagnostics adapter or dashboard consumer, confirm:

- It returns normalized `doctor.v1` checks.
- It uses `pass`, `warn`, `fail`, `skip`, or `error` consistently.
- It uses `required`, `recommended`, or `informational` consistently.
- It redacts secrets before writing terminal, JSON, Markdown, or page output.
- It is offline-safe by default unless a manifest declares the service required.
- It writes generated artifacts under `tests/artifacts/doctor/`.
- It updates docs and CI when command behavior changes.

## Milestone Plan

1. Plan and contract
   - Keep the ExecPlan in `.agent/plans/issue-80-platform-diagnostics-cli.md`.
   - Keep this page as the human-readable command and artifact contract.

2. Skeleton
   - Added the command entrypoint, help text, exit codes, output formats, and first adapters.

3. Local proof adapters
   - Added repo/tooling, ArcadeDB, container, contract, and manifest-driven service checks.

4. Service adapters
   - Frontend and backend checks use `agentarmy.services.json` or `.agent/services.json`.

5. Artifact surfacing
   - `--write-artifacts` writes deterministic JSON and Markdown artifacts.
   - The ArcadeDB cockpit can read the latest JSON artifact.

6. CI gates
   - The `Platform Diagnostics CLI` workflow runs offline-safe checks on PRs.
   - The `Local Docker Smoke Test` workflow provides a manual, opt-in self-hosted runner lane for strict live container checks.
   - Strict live checks should stay manual or environment-gated until runner environments consistently provide containers and ArcadeDB.

## Open Decisions

- Whether a later wrapper should expose `agentarmy doctor` as a package binary.
- Whether service manifests should eventually be generated by the spoke stack builder.
- Whether page rendering should expand beyond the ArcadeDB cockpit into a separate status extension.
- Which spoke repositories should copy the local Docker smoke template first.
