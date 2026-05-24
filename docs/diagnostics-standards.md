# Diagnostics Standards

These standards apply to AgentArmy diagnostic CLIs, local dashboards, status pages, service probes, and generated proof artifacts.

AgentArmy is a template repository. Diagnostics should prove the health of template tooling and declared spoke services without becoming product application code.

## Standard 1: One Command Surface

Every broad local platform check should be reachable from the platform diagnostics CLI:

```powershell
node tools/agentarmy-doctor.mjs
```

New diagnostic tools should be added as adapters or subcommands before adding unrelated one-off scripts. Existing focused scripts can stay, but the doctor CLI should orchestrate or reference them when they become part of the standard readiness path.

## Standard 2: Adapter-First Checks

Each diagnostic domain should be implemented as an adapter with a narrow component boundary:

| Adapter type | Owns |
|---|---|
| Repo/tooling | Local command availability, repo shape, agent sync, docs config. |
| Frontend | Declared frontend build/test/smoke checks. |
| Backend | Declared backend health, OpenAPI, smoke, and contract checks. |
| Database | Readiness, schema sampling, query policy, credential-safe evidence. |
| Containers | Runtime availability, compose status, ports, restart loops, log snippets. |
| Contracts | Schema files, backend contracts, manifest shape, artifact validation. |
| Artifacts | JSON, Markdown, and static page-data exports. |

Adapters should return normalized checks. They should not print directly except through the CLI renderer.

## Standard 3: Manifest Before Guesswork

Service-specific checks should prefer explicit manifests over framework detection.

Supported manifest locations:

```text
agentarmy.services.json
.agent/services.json
```

Manifest records should declare:

| Field | Purpose |
|---|---|
| `name` | Stable service name used in check IDs. |
| `kind` | `frontend`, `backend`, or future adapter kind. |
| `path` | Service root relative to the repository root. |
| `build` | Optional build command. |
| `test` | Optional test command. |
| `health_url` | Optional local smoke URL. |
| `openapi` | Optional backend contract path relative to the service root. |
| `required` | `true` for required checks, `false` for optional local services. |

Template example: `templates/service-manifest.example.json`.

## Standard 4: Stable Artifact Contract

Every machine-readable diagnostic run should emit the `doctor.v1` envelope:

```json
{
  "schema_version": "doctor.v1",
  "run_id": "2026-05-24T12-00-00Z-local",
  "generated_at": "2026-05-24T12:00:00Z",
  "scope": "local",
  "status": "pass",
  "summary": {
    "pass": 1,
    "warn": 0,
    "fail": 0,
    "skip": 0,
    "error": 0
  },
  "checks": [],
  "artifacts": []
}
```

Schema source of truth:

```text
tools/doctor/doctor.v1.schema.json
```

Validation command:

```powershell
node tools/doctor/validate-artifact.mjs tests/artifacts/doctor/latest.json
```

## Standard 5: Status And Exit Semantics

Use these status values consistently:

| Status | Meaning |
|---|---|
| `pass` | The check succeeded. |
| `warn` | The check found a non-blocking issue that should be visible. |
| `fail` | The check failed and should fail strict readiness. |
| `skip` | The check did not apply or an optional dependency was absent. |
| `error` | The check crashed or returned an unexpected diagnostic failure. |

Use these severity values consistently:

| Severity | Meaning |
|---|---|
| `required` | Should fail when broken. |
| `recommended` | Important but may be optional in local development. |
| `informational` | Evidence only; should not block readiness by itself. |

Default local mode should allow optional services to skip. Strict mode may promote skipped required live dependencies to failure.

CLI exit codes:

| Code | Meaning |
|---|---|
| `0` | No `fail` or `error` checks. |
| `1` | At least one `fail` or `error` check. |
| `2` | CLI usage, parsing, or top-level runtime failure. |

## Standard 6: Secret-Safe Evidence

Diagnostics may report configuration presence, target host, database name, status, count, or timing. They must not report raw secret values.

Redact:

- Passwords
- Tokens
- API keys
- Credentials
- Embedded credentials in URLs
- Provider keys
- Raw connection strings that contain secrets

Browser surfaces and generated docs should consume redacted artifacts only. They should not read local `.env` files or service credentials directly.

## Standard 7: Offline-Safe By Default

The default diagnostic run should be useful on a fresh clone.

If Docker, ArcadeDB, a frontend, or a backend is not running, the check should usually report `skip` or `warn` unless the service is explicitly required. This keeps the template usable before a spoke has live containers.

Strict mode exists for stronger environments:

```powershell
node tools/agentarmy-doctor.mjs --strict
```

## Standard 8: Generated Artifacts Stay Out Of Git

Runtime diagnostic outputs belong under:

```text
tests/artifacts/doctor/
```

Committed files in that directory should be limited to stable placeholders or curated examples. Generated `.json` and `.md` outputs are ignored by `.gitignore`.

## Standard 9: Pages Consume Artifacts, Not Probes

Dashboards, docs pages, and cockpit panels should read generated artifacts instead of reimplementing every probe.

Current pattern:

```text
node tools/agentarmy-doctor.mjs --write-artifacts
extensions/arcadedb-cockpit GET /api/doctor
```

This keeps probes centralized and lets multiple surfaces show the same evidence.

## Standard 10: CI Runs Offline-Safe Checks First

PR workflows should start with offline-safe checks that do not require local secrets or live containers. Live strict checks can be added as manual or environment-specific workflows once runner infrastructure declares the required services.

The standard workflow is:

```text
.github/workflows/platform-diagnostics-cli.yml
```

It should:

- Syntax-check the CLI and affected dashboard bridge files.
- Run `node tools/agentarmy-doctor.mjs --write-artifacts`.
- Validate the generated artifact.
- Append the Markdown report to the GitHub step summary.
- Upload generated artifacts.

## Standard 11: Local Docker Smoke Tests Are Opt-In

Local Docker CI is allowed when a trusted self-hosted runner can prove container behavior more cheaply or more accurately than a hosted runner. It must remain opt-in.

The standard workflow is:

```text
.github/workflows/local-docker-smoke.yml
```

It should:

- Run only through `workflow_dispatch`.
- Target self-hosted runners with the `docker-local` label.
- Stay disabled unless `LOCAL_DOCKER_SMOKE_ENABLED=true` or the manual `force` input is used.
- Verify `docker version` and `docker compose version`.
- Run offline diagnostics before live container checks.
- Use a unique `COMPOSE_PROJECT_NAME` per run.
- Upload doctor artifacts and container logs.
- Clean up containers, networks, and images in `always()` steps.
- Never run untrusted fork code on the local Docker host.

## Standard 12: Documentation Requirements

Any new diagnostics adapter should update:

- `docs/diagnostics-standards.md` when a standard changes.
- `docs/platform-diagnostics-cli.md` when commands or user-facing behavior changes.
- `docs/local-docker-ci.md` when local self-hosted Docker workflow behavior changes.
- `tests/artifacts/README.md` when artifact locations or validation commands change.
- The active ExecPlan when the work is part of a tracked issue.

## Standard 13: Naming

Check IDs should use dot-separated names:

```text
component.scope.detail
```

Examples:

```text
repo.node
arcadedb.health
containers.docker-engine
backend.api.health
contracts.doctor-schema
```

Component names should match adapter names whenever possible.
