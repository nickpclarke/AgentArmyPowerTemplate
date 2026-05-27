# AgentArmy schema-migrator — init-container that applies idempotent schema
# migrations against Postgres (via alembic) and ArcadeDB (via REST DDL) and
# exits zero so depends_on.condition: service_completed_successfully holds.
#
# Base: python:3.12-slim, digest-pinned (CWE-1357: no floating tags in prod).
FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

# Non-root runtime user (CWE-269). Let useradd pick UID to avoid collisions
# with the base's defaults.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        curl ca-certificates postgresql-client; \
    rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir \
        "alembic==1.14.0" \
        "sqlalchemy==2.0.36" \
        "psycopg[binary]==3.2.3" \
        "httpx==0.28.1"; \
    groupadd -r migrator; \
    useradd -r -g migrator -m -d /home/migrator migrator

# Copy migration tree + entrypoint + helper scripts.
COPY migrations /opt/agentarmy/migrations
COPY scripts /opt/agentarmy/scripts

# Make entrypoints executable + ownership for non-root runtime user.
RUN chmod +x /opt/agentarmy/scripts/migrate.sh \
             /opt/agentarmy/scripts/apply_arcadedb.py \
 && chown -R migrator:migrator /opt/agentarmy

USER migrator
WORKDIR /opt/agentarmy

ENV PYTHONUNBUFFERED=1 \
    ALEMBIC_CONFIG=/opt/agentarmy/migrations/postgres/alembic.ini

# Run-to-completion entrypoint. The container exits 0 on success and nonzero
# on any failure (bad revision, connect timeout, DDL syntax error...).
ENTRYPOINT ["/opt/agentarmy/scripts/migrate.sh"]
