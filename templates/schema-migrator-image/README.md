# schema-migrator-image

Function-tier init-container image that applies idempotent schema migrations to:

- **Postgres** (DBOS system DB + app DB) via Alembic.
- **ArcadeDB** (graph schema) via HTTP DDL with idempotency guards.

Closes hub issue #283. Owned + advanced by the `schema-migration-engineer` agent (per [ARC-ADR-027](../../docs/decisions/)). Realizes the "init container" composition pattern called out in [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md).

## Quick start

```bash
cd templates/schema-migrator-image
./setup.sh                       # build + doctor (PG + ArcadeDB)
SKIP_ARCADEDB=1 ./setup.sh       # PG only (faster, doctor skips arcadedb checks)
```

Expected output: **3 pass, 0 fail**.

The doctor:
1. Spins up throwaway `postgres:16-alpine` (+ optional `arcadedata/arcadedb:latest`) on its own Docker network.
2. Runs the migrator → checks `schema_version` (PG) and `migration_marker` (ArcadeDB) exist.
3. Runs the migrator again → exits 0, alembic version doesn't drift, no new history rows.
4. Runs once more with `MIGRATION_BAD_REV=fakeXYZ` → exits nonzero so `depends_on.condition: service_completed_successfully` holds.

## Why function-tier init-container (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Lifecycle is run-to-completion** — categorically different from the long-running application-tier spoke it precedes.
- **Different ownership** — schema is a cross-cutting concern; bundling it inside `backend-core` couples DB ops to app deploys.
- **Reusable** — `middle-core`, `backend-core`, and any future spoke that depends on the same Postgres share the migration tree.
- **Fail-fast guarantee** — nonzero exit is what makes `depends_on.condition: service_completed_successfully` meaningful; the migrator is the contract between schema and app.

## Usage as a compose init container

See [`examples/compose.schema-migrator.example.yml`](examples/compose.schema-migrator.example.yml) for a worked example with `postgres`, `arcadedb`, the `migrator`, and a placeholder `backend` that only starts after the migrator exits successfully.

```yaml
services:
  migrator:
    image: agentarmy-schema-migrator:local
    environment:
      DATABASE_URL: postgresql://agentarmy:agentarmy@postgres:5432/agentarmy
      ARCADEDB_URL: http://arcadedb:2480
    depends_on:
      postgres:
        condition: service_healthy

  backend:
    image: my-spoke-backend:local
    depends_on:
      migrator:
        condition: service_completed_successfully
```

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | *(required)* | Postgres URL (`postgresql://user:pass@host:port/db`); psycopg-style accepted |
| `ARCADEDB_URL` | *(unset = skip)* | ArcadeDB base URL (e.g. `http://arcadedb:2480`); omit to run alembic-only |
| `ARCADEDB_DB` | `agentarmy` | Database name on the ArcadeDB server (auto-created idempotently) |
| `ARCADEDB_USER` | `root` | ArcadeDB basic-auth user |
| `ARCADEDB_PASSWORD` | `playwithdata` | ArcadeDB basic-auth password (override in prod) |
| `MODE` | `migrate` | `migrate` / `dryrun` / `rollback` |
| `MIGRATION_BAD_REV` | *(unset)* | If set, alembic targets this revision; doctor uses it to prove fail-fast |
| `PG_WAIT_SECS` | `60` | Max seconds to wait for `pg_isready` |
| `ARCADEDB_WAIT_SECS` | `60` | Max seconds to wait for ArcadeDB `/api/v1/ready` |
| `SKIP_ARCADEDB` *(doctor only)* | `0` | `1` runs the doctor against PG only |

## Modes

| `MODE` | What it does |
|---|---|
| `migrate` *(default)* | Wait for DBs → `alembic upgrade head` → apply pending ArcadeDB DDL → exit 0 |
| `dryrun` | Emit the plan to stdout; exit 0 without applying |
| `rollback` | `alembic downgrade -1`; log "ArcadeDB rollback not implemented" (graph DDL is forward-only) |

## How idempotency is enforced

**Postgres:** Alembic tracks applied revisions in its `alembic_version` table; `alembic upgrade head` is a no-op when nothing is pending. The initial revision uses `CREATE TABLE IF NOT EXISTS` as belt-and-braces protection against partial application.

**ArcadeDB:** Two-layer guard.
1. DDL files prefer `IF NOT EXISTS` where ArcadeDB supports it (CREATE TYPE / PROPERTY since 23.x).
2. The Python runner records each applied filename in PG's `arcadedb_migration_history` table (created by the alembic initial revision). On rerun the runner sees the filename, skips the file entirely — so the doctor's "second run is a no-op" check passes regardless of ArcadeDB version.
3. Inside a file, statements that don't accept `IF NOT EXISTS` are wrapped in a runner-side try/already-exists guard.

## Roadmap

- **DBOS system DB migrations** — add a `migrations/dbos-system/` alembic tree for the workflow-runtime schema. The image already runs `alembic upgrade head` against `DATABASE_URL`; the schema-migration-engineer agent will multiplex when needed.
- **Pre-flight checks** — `MODE=verify` that connects to all configured DBs but applies nothing, useful in CI gates.
- **Postgres rollback** — currently we only support `downgrade -1`; multi-revision rollback needs a `MIGRATION_TARGET_REV` env knob.

## Contract anchor

No external HTTP contract — this is an init container. The "contract" is the migration-versioning convention (alembic linear history for Postgres; ArcadeDB DDL files tracked in PG's `arcadedb_migration_history` meta table). Registered as prose in [`docs/contracts.md`](../../docs/contracts.md).
