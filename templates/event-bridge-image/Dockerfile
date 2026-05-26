# AgentArmy event-bridge — HTTP webhooks ↔ NATS JetStream + CloudEvents v1.0.
# Built from python:3.12-slim. Drops back to non-root before ENTRYPOINT (CWE-269).
# Conforms to the AgentArmy Image Standard (image.json + setup + doctor).

FROM python:3.12-slim

USER root
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    # Secure-by-default deps: stdlib hmac/compare_digest for HMAC; fastapi +
    # pydantic for typed input; nats-py for JetStream; httpx for the relay.
    pip install --no-cache-dir \
        "fastapi==0.117.0" \
        "uvicorn[standard]==0.36.0" \
        "pydantic==2.11.7" \
        "nats-py==2.10.0" \
        "httpx==0.28.1" \
        "cryptography==45.0.7"; \
    # Non-root runtime user (let useradd pick UID — avoids noble UID-1000 collision).
    groupadd -r bridge; \
    useradd -r -g bridge -m -d /home/bridge bridge

COPY entrypoint.sh /opt/agentarmy/entrypoint.sh
COPY scripts /opt/agentarmy/scripts
RUN chmod +x /opt/agentarmy/entrypoint.sh \
 && chown -R bridge:bridge /opt/agentarmy

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8080}/healthz" || exit 1

USER bridge
WORKDIR /home/bridge

# serve-inbound (default) | relay-outbound | <any command>
ENTRYPOINT ["/opt/agentarmy/entrypoint.sh"]
CMD ["serve-inbound"]
