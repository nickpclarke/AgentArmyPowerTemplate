# Local Docker CI

Local Docker CI is the optional, cost-conscious path for running container smoke tests on a trusted host you control. In AgentArmy, it proves the host/runner path and supplies templates. In platform and spoke workload repos, it proves real container builds and smoke tests.

Use this lane for development proof, platform/spoke readiness, and pre-production smoke checks. Do not use it for arbitrary untrusted pull request code.

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

The reusable workflow template has two modes for workload repos.

| Mode | Trigger | Purpose |
|---|---|---|
| Single Dockerfile | Leave `compose_file` blank. | Build the workload repository `Dockerfile` and run a service-specific smoke command. |
| Compose stack | Set `compose_file`, for example `compose.yaml`. | Run a spoke's compose stack, then execute strict diagnostics against the live stack. |

AgentArmy itself is not a product workload and should not be treated as a platform container. Platform/spoke repositories should copy the template and wire their own Dockerfile, compose stack, and smoke commands.

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
- prefer mounted secret files such as `ARCADEDB_PASSWORD_FILE` over plaintext password environment variables inside Compose stacks
- never mount the host Docker socket into untrusted containers
- avoid using your normal interactive admin account as the runner service identity

## Spoke Repository Pattern

Each container-producing platform/spoke repo should commit:

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

When a local smoke stack needs ArcadeDB, use Compose secrets and point `ARCADEDB_PASSWORD_FILE` at the mounted file. See [ArcadeDB Secret Hardening](arcadedb-secret-hardening.md) for the shared rule set.

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

## Relationship To Lifecycle Promotion

When a platform/spoke workload needs full lifecycle CI/CD, local Docker CI becomes the first promotion gate. It proves the merged source locally, then promotes the configured Dev source branch for the cloud build lane. AgentArmy template development uses a simpler `local -> main` track and does not build workload containers.

Use:

```text
docs/lifecycle-promotion-management.md
docs/azure-container-apps-dev.md
templates/lifecycle-promotion/
templates/azure-container-apps-dev/
```

Local Docker CI proves the branch on the trusted host. Azure ACR Tasks or another cloud build service builds the shared Dev image from the promoted source ref.
