# ArcadeDB Secret Hardening

ArcadeDB credentials are platform secrets, not template content. AgentArmy can define the standard and the test shape, but platform/spoke repositories own their runtime secret stores.

Use this standard for local Docker, GitHub automation, Azure Container Apps Dev, and future workload targets that need ArcadeDB.

## Rules

- Never commit real ArcadeDB passwords in `.env`, Compose files, workflow YAML, docs, screenshots, exported Postman environments, or agent settings.
- Prefer `ARCADEDB_PASSWORD_FILE` when a runtime can mount a secret as a file.
- Use `ARCADEDB_PASSWORD` only when the value is injected by a runtime secret channel such as GitHub Actions secrets, Azure Container Apps secrets, Key Vault references, or a local ignored `.env`.
- Keep browser clients credential-free. Frontends should call backend/cockpit APIs, not ArcadeDB directly.
- Rotate ArcadeDB passwords when a secret may have been printed, committed, exported, or shared outside the runtime boundary.
- Use service-specific database users where possible; do not make every platform service use the root account.

## Runtime Pattern

`ARCADEDB_PASSWORD_FILE` wins over `ARCADEDB_PASSWORD`.

```text
ARCADEDB_URL=http://arcadedb:2480
ARCADEDB_DATABASE=knowledge
ARCADEDB_USER=platform_reader
ARCADEDB_PASSWORD_FILE=/run/secrets/arcadedb_password
```

The diagnostics CLI and ArcadeDB cockpit both accept this shape. Their output may report the source of the secret, but must never print the secret value.

## Local Docker

Use Compose secrets for local smoke stacks when the workload needs ArcadeDB.

```yaml
services:
  backend-core:
    environment:
      ARCADEDB_URL: http://arcadedb:2480
      ARCADEDB_USER: platform_reader
      ARCADEDB_PASSWORD_FILE: /run/secrets/arcadedb_password
    secrets:
      - arcadedb_password

secrets:
  arcadedb_password:
    file: .secrets/arcadedb_password.txt
```

Keep `.secrets/` ignored. Commit only a placeholder such as `.secrets/README.md` if the spoke needs setup instructions.

For a simple local-only run without Compose secrets, an ignored `.env` can set `ARCADEDB_PASSWORD`, but that is a developer convenience, not the preferred container pattern.

## GitHub Actions

Use GitHub repository or environment secrets for workflow-time values. For local Docker self-hosted runners, write the secret to a temporary file and pass only the file path to the container or CLI.

```powershell
$secretPath = Join-Path $env:RUNNER_TEMP "arcadedb_password.txt"
Set-Content -LiteralPath $secretPath -Value $env:ARCADEDB_PASSWORD -NoNewline
"ARCADEDB_PASSWORD_FILE=$secretPath" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8
```

Do not echo the secret value. Remove temporary secret files in `always()` cleanup steps when the runner does not do that automatically.

## Azure Container Apps

For Azure Dev workload containers:

- Store the ArcadeDB password in Azure Key Vault or as a Container Apps secret.
- Prefer Key Vault references with managed identity for shared Dev and later environments.
- Inject the value into the container as a secret-backed environment variable, or mount it as a secret file when the runtime shape supports it.
- Keep Azure credential JSON and secret values out of repository files and PR comments.

If the platform uses an internal ArcadeDB Container App, run authenticated smoke tests from a trusted network path: a self-hosted runner on the same network, an Azure Container Apps job in the same environment, or a controlled backend smoke endpoint. Publicly exposing ArcadeDB just to make CI easier is not the standard.

## Postman

Postman environments may include variable names such as `arcadedb_url`, but committed examples must use placeholders. Real passwords belong in local current/secret values, not exported collection files.

## Validation

Run:

```powershell
node tools/agentarmy-doctor.mjs arcadedb --write-artifacts
```

The `arcadedb.credentials` check should report `ARCADEDB_PASSWORD_FILE` or `ARCADEDB_PASSWORD` as the source when credentials are present. It should never include the password.

## Source Notes

- Azure Container Apps supports Container Apps secrets and Key Vault references with managed identity: [Manage secrets in Azure Container Apps](https://learn.microsoft.com/azure/container-apps/manage-secrets).
- Docker Compose supports secrets sourced from files or environment values: [Compose secrets](https://docs.docker.com/reference/compose-file/secrets/).
- GitHub Actions supports repository, environment, and organization secrets: [Using secrets in GitHub Actions](https://docs.github.com/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
- ArcadeDB supports server users and password management through server APIs and commands: [ArcadeDB users](https://docs.arcadedb.com/arcadedb/how-to/operations/users.html).
