"""initial — schema_version meta table

Revision ID: 0001
Revises:
Create Date: 2026-05-27 00:00:00

The initial revision creates a tiny meta table (`schema_version`) so we have
something to migrate end-to-end. Real revisions land later from the spokes
that share this Postgres instance. The DDL is idempotent so manual re-runs
(or a half-applied transaction) don't trip on the second go.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            id           SERIAL PRIMARY KEY,
            applied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            note         TEXT NOT NULL DEFAULT ''
        );
        """
    )
    # Tracker for ArcadeDB DDL files that have already been POSTed. Lives in
    # Postgres because Postgres is the only DB guaranteed to be reachable; the
    # arcadedb runner writes a row per applied file.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS arcadedb_migration_history (
            filename     TEXT PRIMARY KEY,
            applied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            checksum     TEXT NOT NULL
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS arcadedb_migration_history;")
    op.execute("DROP TABLE IF EXISTS schema_version;")
