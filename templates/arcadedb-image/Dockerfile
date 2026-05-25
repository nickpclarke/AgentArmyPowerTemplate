# Thin derived ArcadeDB image for the AgentArmy platform.
#
# Bakes the platform's opinions on top of the official image WITHOUT forking it:
#   - read-only MCP posture (config/mcp-config.json)
#   - default database `knowledge` + read-only service user `platform_reader`
#   - empty doctor-stub document types (Chunk/StoredObject/IngestJob) so
#     `node tools/agentarmy-doctor.mjs arcadedb` passes out of the box
#
# It is NOT a fork or a from-source build — engine fixes still come from upstream
# by bumping the base tag/digest below.
#
# HUB TEMPLATE: copy this directory into your spoke and build/push it yourself.
# This repo intentionally ships NO registry/ACR push pipeline (see README).
#
# The base already runs as the non-root user `arcadedb` (uid 1000) and contains
# only sh + wget + base64 + java (no bash/curl/jq) — the entrypoint is POSIX sh.

# --- Base (digest-pinned for dev==prod reproducibility) ---------------------
# Resolved 2026-05 for arcadedata/arcadedb:26.5.1. Re-resolve on a version bump:
#   docker buildx imagetools inspect arcadedata/arcadedb:<tag>
FROM arcadedata/arcadedb:26.5.1@sha256:3d8183bceb93db2c5dba136e808f799ea0ff9b44e921c94c3364ef86c38d3b1a
# OPTIONAL (NOT default): arcadedata/arcadedb-minimal is smaller but its dropped
# contents are undocumented. MCP + HTTP (2480) are REQUIRED. Only switch after the
# README "Verify" steps confirm /api/v1/ready AND /api/v1/mcp both work on it.

ARG ARCADEDB_VERSION=26.5.1
LABEL org.opencontainers.image.title="agentarmy-arcadedb" \
      org.opencontainers.image.description="ArcadeDB with read-only MCP + platform_reader + doctor-stub schema" \
      org.opencontainers.image.base.name="arcadedata/arcadedb:${ARCADEDB_VERSION}"

# --- Runtime defaults (non-secret; override per environment) -----------------
ENV ARCADEDB_DATABASE=knowledge \
    ARCADEDB_SERVICE_USER=platform_reader \
    ARCADEDB_HTTP_PORT=2480 \
    ARCADEDB_SERVER_MODE=production \
    # Container-aware heap (overrides the base's fixed -Xms2G -Xmx2G) so the same
    # image is small on a laptop and larger on ACI/ACA. Keeps the base JAVA_OPTS
    # (ZGC) untouched. Override ARCADEDB_OPTS_MEMORY to pin an explicit heap.
    ARCADEDB_OPTS_MEMORY="-XX:InitialRAMPercentage=50.0 -XX:MaxRAMPercentage=75.0"

# --- Bake config + scripts into a NON-volume seed dir ------------------------
# /home/arcadedb/{config,databases,log,...} are declared VOLUMEs in the base, so
# we stage under /opt/agentarmy and let the entrypoint copy config in at boot
# (wins over volume-seeded defaults). Least-volatile layer first for caching.
# Switch to root only to place files + fix perms (the base runs as `arcadedb`),
# then drop back. The seed dir needs 0755 so the runtime user can traverse it.
USER root
COPY config/mcp-config.json            /opt/agentarmy/mcp-config.json
COPY bootstrap/doctor-stub-schema.json /opt/agentarmy/doctor-stub-schema.json
COPY entrypoint.sh                     /usr/local/bin/agentarmy-entrypoint.sh
RUN chmod 0755 /opt/agentarmy /usr/local/bin/agentarmy-entrypoint.sh \
 && chmod 0644 /opt/agentarmy/mcp-config.json /opt/agentarmy/doctor-stub-schema.json
USER arcadedb

# --- Ports (2480 = HTTP/Studio/MCP, used by doctor + cockpit + MCP) ----------
EXPOSE 2480

# --- Healthcheck (wget; /api/v1/ready returns 204 with no auth) --------------
HEALTHCHECK --interval=15s --timeout=5s --start-period=45s --retries=5 \
  CMD wget -q -O /dev/null -T 4 "http://localhost:${ARCADEDB_HTTP_PORT}/api/v1/ready" || exit 1

# Keep the base ENTRYPOINT (/__cacert_entrypoint.sh, which exec's our CMD);
# replace only the CMD with our bootstrap wrapper.
CMD ["/usr/local/bin/agentarmy-entrypoint.sh"]
