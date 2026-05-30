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

### Shared ArcadeDB ACA app (`rg-arcade-platform`) — root password MUST NOT be a plaintext env

The fleet's shared ArcadeDB runs as the `arcadedb` Container App in `rg-arcade-platform` /
`cae-arcade-platform`, built from the **upstream** `arcadedata/arcadedb` image (not the thin
`agentarmy-arcadedb` image). The upstream image takes the root password as a JVM `-D` argument
via `JAVA_OPTS`.

**Banned:** a plaintext compound env var, e.g.

```text
# DO NOT DO THIS — readable by anyone with RG Reader via `az containerapp show`
JAVA_OPTS = -Darcadedb.server.rootPassword=<plaintext> -Darcadedb.txWalFlush=2
```

Anyone with `Reader` on the resource group can read that value with a single
`az containerapp show`, and it leaks into any log/transcript that captures the command output.

**Required:** the whole `JAVA_OPTS` value is sourced from a secret, so the control plane shows
only a `secretRef` (no value). Because an ACA `secretRef` substitutes the *entire* env var (you
cannot interpolate a secret into the middle of a string), the secret holds the full opts string:

```text
# secret (Key Vault reference preferred; managed identity + Key Vault Secrets User)
arcadedb-server-opts = -Darcadedb.server.rootPassword=<password> -Darcadedb.txWalFlush=2

# env on the container
JAVA_OPTS -> secretRef: arcadedb-server-opts        # no plaintext on the control plane
```

The bare root password is **also** kept in Key Vault as `arcadedb-root-password` (the canonical
value the *other* consumers read — `backend-core`, the `selfmodel-loader` job, the
`ARCADEDB_ROOT_PASSWORD` GitHub Actions secret). Keep the two in lockstep: rotation writes the new
value to `arcadedb-root-password` **and** rebuilds `arcadedb-server-opts` from it in the same step
(see the rotation runbook). The longer-term convergence is to adopt the thin
`agentarmy-arcadedb` image, which reads a *bare* `ARCADEDB_ROOT_PASSWORD` secret directly and takes
`txWalFlush` via `ARCADEDB_EXTRA_SETTINGS` — eliminating the second secret. Tracked as a follow-up.

**First-init-only caveat (the rotation lever).** `arcadedb.server.rootPassword` is applied only
when the server has no `root` user yet — it lives in `config/server-users.jsonl`
([ArcadeDB #2058](https://github.com/ArcadeData/arcadedb/issues/2058)). On this app only
`/home/arcadedb/databases` is mounted (Azure Files share `arcadedb`); `config/` is **ephemeral**,
so each container (re)start re-initialises `root` from the setting. That makes rotation a restart:
update the secret(s), activate a new revision, and the next cold start adopts the new password — no
volume surgery or `security.json` reset needed. (If `config/` were ever persisted, you would instead
have to reset the credential via ArcadeDB Studio → Security or by clearing the persisted
`server-users.jsonl`.) The env var form `arcadedb_server_rootPassword` is **not** a reliable
substitute on this image — verified locally: with no `JAVA_OPTS` the server blocks waiting for a
root password on stdin ([ArcadeDB #561](https://github.com/ArcadeData/arcadedb/issues/561)).

Reproducible IaC for this app lives at
[`deploy/arcadedb-aca-platform.bicep`](../../templates/arcadedb-image/deploy/arcadedb-aca-platform.bicep);
do not re-create or re-`update` the app with an ad-hoc `az containerapp` command carrying a
plaintext `JAVA_OPTS` — that is what drifted the live app away from the secure template.

## Postman

Postman environments may include variable names such as `arcadedb_url`, but committed examples must use placeholders. Real passwords belong in local current/secret values, not exported collection files.

## Validation

Run:

```powershell
node tools/agentarmy-doctor.mjs arcadedb --write-artifacts
```

The `arcadedb.credentials` check should report `ARCADEDB_PASSWORD_FILE` or `ARCADEDB_PASSWORD` as the source when credentials are present. It should never include the password.

## MCP Server

ArcadeDB v26.3.1+ ships a **built-in** Model Context Protocol server inside the database process (your spike image, `arcadedata/arcadedb:26.5.1`, already includes it). It lets the Claude and Copilot armies query the knowledge graph natively in SQL, Cypher, Gremlin, or GraphQL, always against the live schema.

- Endpoint: `http://<host>:2480/api/v1/mcp` (the standard ArcadeDB HTTP port).
- Transport: HTTP. Claude Code connects directly — no `mcp-remote` / `npx` bridge is needed (that bridge is only for stdio-only clients such as older Claude Desktop).
- Auth (either works, scoped by `allowedUsers`):
  - **Basic** — `Authorization: Basic <base64(user:password)>` using a server user (e.g. `platform_reader`). Turnkey: no Studio step, fully scriptable. Used by the `templates/arcadedb-image/` setup scripts.
  - **Bearer** — `Authorization: Bearer <token>`. Create the token in ArcadeDB Studio → Security. Prefer this for shared/hardened environments where you want a revocable token distinct from the DB password.

### Client config

The `arcadedb` server in the repo `.mcp.json` uses env-var interpolation, so no token is committed (same pattern as the `gcp-*` entries):

```json
"arcadedb": {
  "type": "http",
  "url": "${ARCADEDB_MCP_URL:-http://localhost:2480/api/v1/mcp}",
  "headers": { "Authorization": "Bearer ${ARCADEDB_MCP_TOKEN}" }
}
```

| Var | Purpose |
|---|---|
| `ARCADEDB_MCP_URL` | MCP endpoint. Defaults to local Docker; set to the Azure ACI instance host for shared Dev. |
| `ARCADEDB_MCP_TOKEN` | Bearer token from Studio → Security. |
| `ARCADEDB_MCP_BASIC` | `base64(platform_reader:password)` for the Basic-auth alternative. Swap the header to `Basic ${ARCADEDB_MCP_BASIC}`. |

Treat `ARCADEDB_MCP_TOKEN` / `ARCADEDB_MCP_BASIC` like any other ArcadeDB credential: never commit them, inject via a gitignored `.env` locally or a runtime secret channel, and rotate if printed or shared.

### Server-side posture (read-only by default)

Match the platform default and enable MCP read-only. Configure it via Studio (Server > MCP), `POST /api/v1/mcp/config`, or `config/mcp-config.json`:

```json
{
  "enabled": true,
  "allowReads": true,
  "allowInsert": false,
  "allowUpdate": false,
  "allowDelete": false,
  "allowSchemaChange": false,
  "allowAdmin": false,
  "allowedUsers": ["platform_reader"]
}
```

Scope `allowedUsers` to a service-specific reader (not `root`), and flip mutation flags only as a deliberate, reviewed change.

## Source Notes

- Azure Container Apps supports Container Apps secrets and Key Vault references with managed identity: [Manage secrets in Azure Container Apps](https://learn.microsoft.com/azure/container-apps/manage-secrets).
- Docker Compose supports secrets sourced from files or environment values: [Compose secrets](https://docs.docker.com/reference/compose-file/secrets/).
- GitHub Actions supports repository, environment, and organization secrets: [Using secrets in GitHub Actions](https://docs.github.com/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
- ArcadeDB supports server users and password management through server APIs and commands: [ArcadeDB users](https://docs.arcadedb.com/arcadedb/how-to/operations/users.html).
- ArcadeDB ships a built-in MCP server (v26.3.1+) over HTTP with Bearer-token auth: [ArcadeDB MCP Server](https://arcadedb.com/blog/arcadedb-mcp-server-connect-your-llm-to-your-database/).
