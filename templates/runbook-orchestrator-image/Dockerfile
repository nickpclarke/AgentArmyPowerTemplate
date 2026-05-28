# AgentArmy runbook-orchestrator — runs BPMN 2.0 + OASIS CACAO 2.0 runbooks,
# responding to event-bus triggers. Function-tier per ARC-ADR-023 / -031.
# Built from python:3.12-slim. Drops to a non-root user before ENTRYPOINT.
FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    # defusedxml hardens BPMN XML parsing against XXE / billion-laughs; the kernel
    # itself is stdlib-only — fastapi/uvicorn/nats-py are the optional serve layer.
    pip install --no-cache-dir \
        "defusedxml==0.7.1" \
        "fastapi==0.117.0" \
        "uvicorn[standard]==0.36.0" \
        "pydantic==2.11.7" \
        "nats-py==2.10.0"; \
    groupadd -r runbook; \
    useradd -r -g runbook -m -d /home/runbook runbook

COPY entrypoint.sh /opt/agentarmy/entrypoint.sh
COPY scripts /opt/agentarmy/scripts
COPY runbooks /runbooks
RUN chmod +x /opt/agentarmy/entrypoint.sh \
 && chown -R runbook:runbook /opt/agentarmy /runbooks

ENV RUNBOOK_DIR=/runbooks
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8080}/healthz" || exit 1

USER runbook
WORKDIR /home/runbook

# serve (default) | run <file> | validate <file> | <any command>
ENTRYPOINT ["/opt/agentarmy/entrypoint.sh"]
CMD ["serve"]
