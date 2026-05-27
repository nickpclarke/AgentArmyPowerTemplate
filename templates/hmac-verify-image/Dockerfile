# AgentArmy hmac-verify — constant-time HMAC verification sidecar.
# Lifts the verifier already living inside templates/event-bridge-image/ into
# its own function-tier image so any spoke that accepts signed webhooks can
# drop it in front without code changes.
#
# Base: python:3.12-slim, digest-pinned (CWE-1357: no floating tags in prod).
# Matches the local-embedder image's pin for fleet-wide consistency.
FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

# Non-root runtime user (CWE-269). Let useradd pick UID to avoid collisions
# with the base's defaults.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    # Secure-by-default deps. stdlib hmac.compare_digest is the load-bearing
    # primitive (constant-time); httpx for the proxy hop; cryptography is
    # reserved for KV-resolved secret unwrap (follow-up).
    pip install --no-cache-dir \
        "fastapi==0.117.0" \
        "uvicorn[standard]==0.36.0" \
        "pydantic==2.11.7" \
        "httpx==0.28.1" \
        "cryptography==43.0.3"; \
    groupadd -r hmac; \
    useradd -r -g hmac -m -d /home/hmac hmac

COPY scripts /opt/agentarmy/scripts

RUN chown -R hmac:hmac /opt/agentarmy

USER hmac
ENV PYTHONUNBUFFERED=1

EXPOSE 8083

CMD ["python", "/opt/agentarmy/scripts/verify-sidecar.py"]
