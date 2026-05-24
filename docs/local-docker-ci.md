# Local Docker CI

Local Docker CI is the optional, cost-conscious path for running container smoke tests on a trusted host you control. It complements the hosted `Platform Diagnostics CLI` workflow: hosted CI proves the template and offline diagnostics, while this workflow proves that local Docker can build and run the current repository or a declared spoke stack.

Use this lane for development proof, spoke readiness, and pre-production smoke checks. Do not use it for arbitrary untrusted pull request code.

## When To Use It

Use local Docker CI when:

- a spoke has meaningful container runtime behavior to test
- a hosted runner would be unnecessarily expensive or too far from the local stack
- the test needs local-only dependencies such as a private ArcadeDB, emulator, or internal service
- a developer wants a repeatable smoke test before pushing a broader deployment change

Do not use it when:

- untrusted fork code would run on the local host
- the test needs production-grade isolation, audit, or availability
- the host has personal credentials that the runner account can read
- the same result can be proven with the cheaper offline diagnostics workflow

## Host Requirements

The local host needs:

- Docker Desktop or a Docker Engine reachable from the runner account
- Docker Compose v2
- a GitHub Actions self-hosted runner installed outside active repositories
- runner labels that include `self-hosted` and `docker-local`
- a dedicated non-admin runner account where possible
- no personal provider keys, Codex config, Claude settings, or cloud credentials in the runner workspace

Suggested runner directory:

```text
C:\ActionsRunner\agentarmy-local-docker
```

Suggested labels:

```text
self-hosted
windows
docker-local
agentarmy-local
```

## Activation

The committed workflow is:

```text
.github/workflows/local-docker-smoke.yml
```

It is manual-only and guarded by a repository variable so it stays off by default.

To enable normal manual runs, set this repository or environment variable:

```text
LOCAL_DOCKER_SMOKE_ENABLED=true
```

You can also run the workflow manually with `force=true` when testing runner setup.

## Smoke Modes

The workflow has two modes.

| Mode | Trigger | Purpose |
|---|---|---|
| Root Dockerfile | Leave `compose_file` blank. | Build the repository `Dockerfile`, run it, and request `README.md` from the temporary container. |
| Compose stack | Set `compose_file`, for example `compose.yaml`. | Run a spoke's compose stack, then execute strict diagnostics against the live stack. |

The root mode exists so AgentArmy can prove the local Docker path without pretending to be a product app. Spoke repositories should prefer the compose mode once they own real services.

## Cost Controls

Local Docker CI should stay opt-in:

- use `workflow_dispatch`, not automatic runs on every push
- keep `LOCAL_DOCKER_SMOKE_ENABLED` unset unless the host is ready
- set workflow timeouts
- use one compose project per run
- upload logs and doctor artifacts for review instead of rerunning blindly
- clean up containers, networks, and images in `always()` steps

The workflow sets:

```text
COMPOSE_PROJECT_NAME=agentarmy-local-<run_id>
```

Spoke repos should override this with a service-specific prefix, such as:

```text
COMPOSE_PROJECT_NAME=career-api-local-<run_id>
```

## Security Rules

A self-hosted runner with Docker can control the host. Treat it as trusted infrastructure.

Rules:

- do not run untrusted fork PRs on `docker-local`
- prefer `workflow_dispatch` or protected environments for local Docker jobs
- keep runner workspaces outside user profile secrets
- keep `.env`, `.env.local`, provider keys, and personal agent settings uncommitted
- never mount the host Docker socket into untrusted containers
- avoid using your normal interactive admin account as the runner service identity

## Spoke Repository Pattern

Each container spoke should commit:

```text
.agent/layer.json
agentarmy.services.json
compose.yaml
.env.example
.github/workflows/local-docker-smoke.yml
```

The spoke workflow can copy from:

```text
templates/local-docker-ci/github-actions-local-docker-smoke.yml
```

The compose smoke example is:

```text
templates/local-docker-ci/compose.smoke.example.yml
```

Spokes should update `agentarmy.services.json` so the doctor CLI knows which frontend, backend, database, or worker checks are required during strict local Docker runs.

## Validation

Recommended host validation:

```powershell
docker version
docker compose version
docker run hello-world
node tools/agentarmy-doctor.mjs --write-artifacts
```

Recommended workflow validation:

1. Install and start the self-hosted runner.
2. Confirm the runner has the `docker-local` label.
3. Set `LOCAL_DOCKER_SMOKE_ENABLED=true`, or run once with `force=true`.
4. Run `Local Docker Smoke Test` from the Actions tab.
5. Review the uploaded `local-docker-smoke` artifact.

## Relationship To Hosted CI

Hosted CI remains the default proof path:

```text
.github/workflows/platform-diagnostics-cli.yml
```

Use hosted CI for offline-safe template checks. Use local Docker CI only when a container runtime or local dependency materially improves confidence.
