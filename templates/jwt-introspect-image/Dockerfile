# AgentArmy jwt-introspect — JWT verification sidecar (ARC-ADR-002 verify-side).
# Any spoke that needs to verify a forwarded user JWT calls 127.0.0.1:8084/introspect
# inside its own network namespace. Centralizes JWKS caching, leeway handling,
# and algorithm allowlisting so each spoke isn't re-implementing RS256/ES256
# verify + JWKS rotation logic.
#
# Base: python:3.12-slim, digest-pinned (CWE-1357: no floating tags in prod).
# Matches the digest used by templates/local-embedder-image/Dockerfile.
FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

# Non-root runtime user (CWE-269). Let useradd pick UID to avoid collisions
# with the base's defaults.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    # Secure-by-default deps. PyJWT[crypto] pulls the cryptography wheel which
    # provides constant-time signature verify. httpx is the async JWKS fetcher.
    pip install --no-cache-dir \
        "fastapi==0.117.0" \
        "uvicorn[standard]==0.36.0" \
        "pydantic==2.11.7" \
        "pyjwt[crypto]==2.10.1" \
        "httpx==0.28.1"; \
    groupadd -r introspect; \
    useradd -r -g introspect -m -d /home/introspect introspect

COPY scripts /opt/agentarmy/scripts

RUN chown -R introspect:introspect /opt/agentarmy

USER introspect
ENV PYTHONUNBUFFERED=1

EXPOSE 8084

CMD ["python", "/opt/agentarmy/scripts/introspect.py"]
