# ArcadeDB image template

A **thin derived** ArcadeDB image: `FROM arcadedata/arcadedb:26.5.1` with the
AgentArmy platform's opinions baked on top. It is **not** a fork or a from-source
build — engine fixes still arrive by bumping the pinned base in the `Dockerfile`.

It exists so a fresh container is **correct-by-default** instead of relying on
manual Studio clicks: the read-only MCP posture, the `platform_reader` service
user, the `knowledge` database, and the doctor-stub types are all applied
automatically.

> **Hub template.** This lives in the AgentArmy Hub as a reusable artifact. Copy
> this directory into your spoke and build/push it from there — this repo ships
> **no** registry/ACR push pipeline (same convention as
> `templates/local-docker-ci/`). See [docs/azure-container-apps-dev.md](../../docs/azure-container-apps-dev.md)
> for the spoke build/push lane.

## What it bakes in

| Concern | How |
|---|---|
| Read-only MCP posture | `config/mcp-config.json` is staged in the image and copied into `config/` on every boot (`enabled:true`, all mutations `false`, `allowedUsers:["platform_reader"]`). |
| Default database + service user | First boot creates `knowledge` and the read-only user `platform_reader` via `arcadedb.server.defaultDatabases=knowledge[platform_reader:<pw>:readonly]`. |
| Doctor-stub schema | After readiness, `bootstrap/doctor-stub-schema.json` ensures empty `Chunk`/`StoredObject`/`IngestJob` document types (`IF NOT EXISTS`) so `tools/agentarmy-doctor.mjs arcadedb` passes. |
| Healthcheck | `HEALTHCHECK` polls `/api/v1/ready` (204, no auth) with `wget`. |

The image does **not** bake the ontology schema (`OntologyElement`,
`PinLedgerEntry`, indexes, edges). backend-core's `EnsureReadyAsync` owns that —
the stub types use `IF NOT EXISTS` so the two never collide.

## Files

| File | Purpose |
|---|---|
| `setup.sh` / `setup.ps1` | One-command setup: gen secrets → build+up → wait healthy → run doctor → emit MCP client wiring. |
| `Dockerfile` | The thin derived image. Base is digest-pinned. |
| `entrypoint.sh` | POSIX `sh` wrapper: applies MCP posture, resolves secrets, starts the server, ensures stub schema. |
| `config/mcp-config.json` | Baked read-only MCP posture. |
| `bootstrap/doctor-stub-schema.json` | `sqlscript` payload for the three doctor-stub types. |
| `.dockerignore` | Keeps docs/secrets out of the build context. |
| `.env.example` | Non-secret knobs; documents the secret env vars (no values). |
| `examples/compose.arcadedb-server.example.yml` | Run the image with file-mounted secrets + persistent volumes. |
| `examples/.secrets/README.md` | Placeholder; keep real secrets here and gitignored. |

## Secrets (server side)

The base image has no `curl`/`jq`/`bash`; the entrypoint is POSIX `sh` + `wget` +
`base64`. Passwords are read from a `*_FILE` (preferred) or the plain env var and
are never logged.

| Env var | Meaning |
|---|---|
| `ARCADEDB_ROOT_PASSWORD_FILE` / `ARCADEDB_ROOT_PASSWORD` | `root` (admin; bootstrap only). |
| `ARCADEDB_SERVICE_PASSWORD_FILE` / `ARCADEDB_SERVICE_PASSWORD` | `platform_reader` (read-only). |

Clients (doctor, cockpit) read the **same** reader secret via
`ARCADEDB_PASSWORD_FILE`. See [docs/arcadedb-secret-hardening.md](../../docs/arcadedb-secret-hardening.md).

> ArcadeDB takes passwords as JVM `-D` args, so they are visible in the
> in-container process list (same as upstream). Avoid `:` `[` `]` `{` `}` in the
> service password — they are `defaultDatabases` delimiters.

## Quick start (one command)

```bash
./setup.sh        # Linux / macOS / WSL / Git-Bash
.\setup.ps1       # Windows PowerShell / pwsh
```

It generates local secrets (random, if missing), builds and starts the stack via
compose, waits for the healthcheck, runs `agentarmy-doctor arcadedb`, and writes
the MCP client wiring to `examples/.secrets/mcp-client.env` (gitignored). Tear
down with `./setup.sh --down` (or `.\setup.ps1 -Down`).

## Build & run (manual)

```bash
cp .env.example .env                       # optional, non-secret knobs
printf 'change-me-root'   > examples/.secrets/arcadedb_root_password.txt
printf 'change-me-reader' > examples/.secrets/arcadedb_password.txt

# Compose (recommended — persists config + databases together):
docker compose -f examples/compose.arcadedb-server.example.yml up -d --build

# …or plain docker:
docker build -t agentarmy-arcadedb:local .
docker run -d --name arcadedb -p 2480:2480 \
  -v "$PWD/examples/.secrets/arcadedb_root_password.txt:/run/secrets/arcadedb_root_password:ro" \
  -v "$PWD/examples/.secrets/arcadedb_password.txt:/run/secrets/arcadedb_password:ro" \
  -e ARCADEDB_ROOT_PASSWORD_FILE=/run/secrets/arcadedb_root_password \
  -e ARCADEDB_SERVICE_PASSWORD_FILE=/run/secrets/arcadedb_password \
  agentarmy-arcadedb:local
```

## Connect an MCP client

The built-in MCP server is enabled, read-only, and scoped to `platform_reader`.
The endpoint accepts **either** auth header — pick one in `.mcp.json`:

```jsonc
"arcadedb": {
  "type": "http",
  "url": "${ARCADEDB_MCP_URL:-http://localhost:2480/api/v1/mcp}",
  // Turnkey (no Studio step) — value emitted by setup into mcp-client.env:
  "headers": { "Authorization": "Basic ${ARCADEDB_MCP_BASIC}" }
  // Hardened alternative — mint a token in Studio -> Security:
  // "headers": { "Authorization": "Bearer ${ARCADEDB_MCP_TOKEN}" }
}
```

`tools/list` exposes `list_databases`, `get_schema`, and `query`;
`execute_command` is present but blocked by the read-only posture
(`allowInsert/Update/Delete/SchemaChange:false`). Flip those in
`config/mcp-config.json` only as a deliberate, reviewed change.

## Verify

```bash
# Health (no auth):
curl -i http://localhost:2480/api/v1/ready          # 204 No Content

# Repo doctor (all arcadedb checks pass):
ARCADEDB_URL=http://localhost:2480 ARCADEDB_DATABASE=knowledge \
ARCADEDB_USER=platform_reader \
ARCADEDB_PASSWORD_FILE=examples/.secrets/arcadedb_password.txt \
  node ../../tools/agentarmy-doctor.mjs arcadedb
```

MCP is enabled and protected: `GET /api/v1/mcp` returns **401** until you add a
Bearer token created in ArcadeDB Studio → Security. Wire clients via `.mcp.json`
(`ARCADEDB_MCP_URL`, `ARCADEDB_MCP_TOKEN`).

## Operational notes

- **Non-root.** The base already runs as `arcadedb` (uid 1000); no `USER`
  override is needed. The image switches to `root` only during build to place
  files, then drops back.
- **Volumes.** `config/` and `databases/` are base VOLUMEs. Persist them
  **together** (the reader user lives in `config/server-users.jsonl`, the data in
  `databases/`) — keeping only one desyncs the user from the data on recreate.
  The MCP posture is re-applied from the image on every boot, so it stays correct
  even on a persisted `config/` volume.
- **Heap.** `ARCADEDB_OPTS_MEMORY` defaults to container-aware RAM percentages
  (overriding the base's fixed `-Xms2G -Xmx2G`). Pin an explicit heap per
  environment if you prefer.
- **Bump the base.** Re-resolve the digest on a version change:
  `docker buildx imagetools inspect arcadedata/arcadedb:<tag>`, then update the
  `FROM` line.
- **Extra settings.** `ARCADEDB_EXTRA_SETTINGS` (space-separated `-D…`) is
  appended to the server args.
