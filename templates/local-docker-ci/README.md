# Local Docker CI Template

Copy these files into a spoke repository when it needs optional local Docker smoke tests.

| File | Destination | Purpose |
|---|---|---|
| `github-actions-local-docker-smoke.yml` | `.github/workflows/local-docker-smoke.yml` | Manual self-hosted runner workflow for local Docker smoke tests. |
| `compose.smoke.example.yml` | `compose.yaml` or `compose.smoke.yaml` | Minimal Compose stack pattern for a spoke-owned service. |
| `.env.example` | `.env.example` | Non-secret local environment keys to document required runtime settings. |

Before enabling the workflow:

1. Install a GitHub Actions self-hosted runner on the local host.
2. Add the runner label `docker-local`.
3. Make sure the runner account can run `docker version` and `docker compose version`.
4. Set `LOCAL_DOCKER_SMOKE_ENABLED=true` as a repository or environment variable.
5. Keep service secrets in ignored `.env` files or GitHub Environment secrets, not in committed YAML.

The workflow is intentionally `workflow_dispatch` only. Local Docker CI is for trusted, explicit smoke tests, not arbitrary untrusted pull request execution.
