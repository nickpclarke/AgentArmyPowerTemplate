# Abstraction meta-service MCP (ARC-ADR-036) — function tier.
# Build context = REPO ROOT: the canonical server lives in tools/mcp-abstraction/ (the
# single source of truth — no vendored copy, no drift). Build with:
#   docker build -f templates/abstraction-mcp-image/Dockerfile -t agentarmy-abstraction-mcp .
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Canonical server + proxy + their deps (single source: tools/mcp-abstraction/).
COPY tools/mcp-abstraction/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY tools/mcp-abstraction/server.py tools/mcp-abstraction/client.py ./
# Image-local doctor + dispatch.
COPY templates/abstraction-mcp-image/doctor.py templates/abstraction-mcp-image/entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Run as a non-root user (no privileged operations are needed).
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

# streamable-http on all interfaces so the tunnel / ACA ingress can reach it; DNS-rebinding
# protection stays ON (the server allowlists MCP_PUBLIC_HOST). Served at /abstract.
ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8181 \
    MCP_PUBLIC_HOST=mcp.untool.ai \
    ABSTRACTION_API_URL=http://host.docker.internal:8000
EXPOSE 8181

# Default: the offline correctness gate (no keys/network/backend needed). 'serve' runs the MCP.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["doctor"]
