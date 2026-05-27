# schema-migrator-image — scaffold

**Status:** scaffold (image.json + this README + setup.sh placeholder).

## What this image will be

Run-to-completion init container that applies idempotent schema migrations to:

- **Postgres** (DBOS system DB + app DB) via Alembic.
- **ArcadeDB** (graph schema) via HTTP DDL with idempotency guards.

Owned + advanced by the `schema-migration-engineer` agent. Realizes the "init container" composition pattern called out in [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md).

## Why this is its own image

- **Lifecycle is run-to-completion** — categorically different from the long-running application-tier spoke it precedes.
- **Different ownership** — schema is a cross-cutting concern; bundling it inside backend-core couples DB ops to app deploys.
- **Reusable** — middle-core, backend-core, and any future spoke that depends on the same Postgres can share the migration tree.

## Backlog row

No new backlog row — schema migrations are mechanical infrastructure, not a published contract per se. The schema's *consumers* (BE, MC) bind to the data-platform contract (already registered).
