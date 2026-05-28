# AgentArmy agentarmy-forge — function-tier code generator.
# Reads an ontology (YAML / RDF) from HTTP, file, or Azure Blob and emits
# typed source files for the three application-tier spokes (C# / TS / Python).
#
# Per ARC-ADR-029:
#   v0 — YAML → C# byte-identical to middle-core baseline
#   v1 — RDF + multi-source + FastAPI server + HMAC webhook
#   v2 — multi-language emit (C# / TS / Python)
#
# Base: python:3.12-slim, digest-pinned (CWE-1357: no floating tags in prod).
# Same digest as templates/local-embedder-image so the base is shared across
# function-tier images (smaller pull surface, easier patching).
FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

# Non-root runtime user (CWE-269). Let useradd pick UID to avoid collisions
# with the base's defaults.
#
# apt:
#   curl + ca-certificates — health probes, http source fetches.
#   git                    — pr_opener clones consumer repos.
#   nodejs                 — `tsc --noEmit` smoke-compile for the v2 TS emitter.
#                            Apt's nodejs is older than 22 but is sufficient for
#                            type-checking; we install typescript via npm.
#
# .NET SDK is NOT baked in — it's a 400+MB install that the doctor doesn't
# need for the byte-identical golden check. Operators who want a `dotnet build`
# smoke-step can layer the dotnet/sdk image on top or run the check with
# SKIP_DOTNET=0 (see doctor script).
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        curl ca-certificates git nodejs npm; \
    rm -rf /var/lib/apt/lists/*; \
    npm install -g --silent typescript@5.7.2 zod@3.24.1; \
    pip install --no-cache-dir \
        "fastapi==0.117.0" \
        "uvicorn[standard]==0.36.0" \
        "pydantic==2.11.7" \
        "pyyaml==6.0.2" \
        "rdflib==7.1.1" \
        "pyshacl==0.27.0" \
        "httpx==0.28.1" \
        "azure-storage-blob==12.24.0" \
        "azure-identity==1.19.0"; \
    groupadd -r forge; \
    useradd -r -g forge -m -d /home/forge forge

# Bake the forge package + entrypoint + doctor.
COPY scripts /opt/agentarmy/scripts
COPY tests /opt/agentarmy/tests

# Make entrypoints executable and chown for the non-root runtime user.
RUN chmod +x /opt/agentarmy/scripts/entrypoint.sh \
             /opt/agentarmy/scripts/forge-doctor.sh \
 && chown -R forge:forge /opt/agentarmy \
 && mkdir -p /work/out \
 && chown -R forge:forge /work

# Put the forge package on PYTHONPATH so `python -m forge.server` works.
ENV PYTHONPATH=/opt/agentarmy/scripts \
    PYTHONUNBUFFERED=1 \
    FORGE_OUT_DIR=/work/out

USER forge
WORKDIR /opt/agentarmy

EXPOSE 8086

ENTRYPOINT ["/opt/agentarmy/scripts/entrypoint.sh"]
