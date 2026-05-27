#!/usr/bin/env python3
"""Apply pending ArcadeDB DDL files from migrations/arcadedb/.

Algorithm (idempotent):
    1. Connect to Postgres (DATABASE_URL).
    2. Read applied history from `arcadedb_migration_history` (created by the
       alembic 0001 revision).
    3. For each `*.sql` file in migrations/arcadedb (sorted by name):
         - if filename already in history → SKIP
         - else POST each `;\\n`-separated SQL command to
           `${ARCADEDB_URL}/api/v1/command/${ARCADEDB_DB}` with basic auth
         - on success, insert a row recording (filename, checksum)
    4. Exit 0 on success; nonzero on the first failure (with a message).

ArcadeDB's REST API: POST /api/v1/command/{db}
  body: {"language": "sql", "command": "CREATE VERTEX TYPE ... IF NOT EXISTS"}
  auth: Basic root:playwithdata (configurable via ARCADEDB_USER / ARCADEDB_PASSWORD).
  https://docs.arcadedb.com/#HTTP-API

Idempotency strategy per DDL:
  - Prefer `IF NOT EXISTS` in the SQL itself (ArcadeDB supports it on CREATE
    TYPE / PROPERTY since 23.x).
  - For statements that don't accept `IF NOT EXISTS`, the runner catches the
    well-known "already exists" / "duplicate" error class and treats it as
    success (logged as "skipped — already applied"). This guard is what lets
    the doctor's "applies twice" check pass for older ArcadeDB versions.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import sys

import httpx
import psycopg

ARCADEDB_URL = os.environ.get("ARCADEDB_URL", "").rstrip("/")
ARCADEDB_DB = os.environ.get("ARCADEDB_DB", "agentarmy")
ARCADEDB_USER = os.environ.get("ARCADEDB_USER", "root")
ARCADEDB_PASSWORD = os.environ.get("ARCADEDB_PASSWORD", "playwithdata")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
MIGRATIONS_DIR = pathlib.Path(
    os.environ.get("ARCADEDB_MIGRATIONS_DIR", "/opt/agentarmy/migrations/arcadedb")
)

IDEMPOTENT_ERROR_SIGNALS = (
    "already exist",
    "duplicate",
    "is already",
)


def log(msg: str) -> None:
    print(f"apply_arcadedb {msg}", file=sys.stderr, flush=True)


def normalize_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url[len("postgresql+psycopg://") :]
    return url


def ensure_arcadedb_database(client: httpx.Client) -> None:
    """ArcadeDB doesn't auto-create the target DB on first command. Idempotent."""
    create_url = f"{ARCADEDB_URL}/api/v1/server"
    try:
        r = client.post(
            create_url,
            json={"command": f"create database {ARCADEDB_DB}"},
            timeout=10.0,
        )
        if r.status_code == 200:
            log(f"created arcadedb database {ARCADEDB_DB!r}")
            return
        if r.status_code in (400, 409, 500) and (
            "already exist" in r.text.lower() or "duplicate" in r.text.lower()
        ):
            log(f"arcadedb database {ARCADEDB_DB!r} already exists")
            return
        log(f"WARN: unexpected response from server-command: {r.status_code} {r.text}")
    except httpx.HTTPError as exc:
        log(f"WARN: server-command request failed: {exc!r} — assuming DB exists")


def apply_command(client: httpx.Client, sql: str) -> None:
    url = f"{ARCADEDB_URL}/api/v1/command/{ARCADEDB_DB}"
    payload = {"language": "sql", "command": sql}
    r = client.post(url, json=payload, timeout=30.0)
    if r.status_code == 200:
        return
    body = r.text.lower()
    if any(sig in body for sig in IDEMPOTENT_ERROR_SIGNALS):
        log(f"  skip — already applied: {sql[:60]!r} ({r.status_code})")
        return
    raise RuntimeError(f"arcadedb command failed ({r.status_code}): {r.text}\nSQL: {sql}")


def split_ddl(text: str) -> list[str]:
    """Split on `;\\n`, dropping blank lines and comments."""
    out: list[str] = []
    for raw in text.split(";\n"):
        stmt_lines = [
            ln.rstrip()
            for ln in raw.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if not stmt_lines:
            continue
        stmt = " ".join(stmt_lines).strip().rstrip(";").strip()
        if stmt:
            out.append(stmt)
    return out


def main() -> int:
    if not ARCADEDB_URL:
        log("ARCADEDB_URL unset — nothing to do")
        return 0
    if not DATABASE_URL:
        log("FATAL: DATABASE_URL unset; need PG for migration history")
        return 1

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        log(f"no DDL files in {MIGRATIONS_DIR} — nothing to do")
        return 0

    auth = (ARCADEDB_USER, ARCADEDB_PASSWORD)
    pg_dsn = normalize_pg_url(DATABASE_URL)

    with httpx.Client(auth=auth) as client:
        ensure_arcadedb_database(client)
        with psycopg.connect(pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT filename FROM arcadedb_migration_history")
                applied = {row[0] for row in cur.fetchall()}

            for fp in files:
                name = fp.name
                if name in applied:
                    log(f"{name}: already applied — skip")
                    continue
                text = fp.read_text(encoding="utf-8")
                checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
                log(f"{name}: applying ({len(text)} bytes)")
                for stmt in split_ddl(text):
                    apply_command(client, stmt)
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO arcadedb_migration_history (filename, checksum) "
                        "VALUES (%s, %s)",
                        (name, checksum),
                    )
                conn.commit()
                log(f"{name}: applied + recorded")

    return 0


if __name__ == "__main__":
    sys.exit(main())
