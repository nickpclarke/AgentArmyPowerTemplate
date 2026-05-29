# Board-sync runtime (ARC-ADR-036): apply a vended field adapter to live board items.
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# azure-* only for resolving GithubPAT from Key Vault when GH_TOKEN is absent.
# The GitHub fetch itself uses stdlib urllib (no httpx).
RUN pip install --no-cache-dir azure-identity azure-keyvault-secrets

COPY apply.py connectors.py doctor.py sync.py entrypoint.sh ./
COPY adapters/ ./adapters/
COPY samples/ ./samples/
RUN chmod +x entrypoint.sh

# Run as a non-root user (no privileged operations are needed).
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

# Default: the correctness gate (no keys/network needed).
ENTRYPOINT ["./entrypoint.sh"]
CMD ["doctor"]
