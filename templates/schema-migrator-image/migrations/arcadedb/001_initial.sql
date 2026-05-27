-- AgentArmy schema-migrator — ArcadeDB initial DDL.
--
-- Each statement separated by a semicolon at the END of a line. The runner
-- splits on `;\n` and POSTs each command individually to ArcadeDB's REST
-- endpoint `POST /api/v1/command/{db}` (it accepts one SQL command per call).
-- Idempotency: ArcadeDB supports `IF NOT EXISTS` on CREATE TYPE since 23.x.
-- Statements that don't are wrapped client-side by the runner's "try/ignore"
-- guard (see apply_arcadedb.py).

CREATE VERTEX TYPE migration_marker IF NOT EXISTS;
CREATE PROPERTY migration_marker.applied_at IF NOT EXISTS DATETIME;
CREATE PROPERTY migration_marker.revision IF NOT EXISTS STRING;
