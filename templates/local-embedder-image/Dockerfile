# AgentArmy local-embedder — OpenAI-compatible local embedding service.
# CPU-first baseline using sentence-transformers + PyTorch. OpenVINO / iGPU
# acceleration is a follow-up (see README "Hardware roadmap"); the CPU path
# works on any architecture and gets us a working contract producer today.
#
# Base: python:3.12-slim, digest-pinned (CWE-1357: no floating tags in prod).
FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

# Non-root runtime user (CWE-269). Let useradd pick UID to avoid collisions
# with the base's defaults.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    # Secure-by-default deps. sentence-transformers pulls torch (CPU build);
    # numpy is transitive. pin versions to keep the image reproducible.
    pip install --no-cache-dir \
        "fastapi==0.117.0" \
        "uvicorn[standard]==0.36.0" \
        "pydantic==2.11.7" \
        "sentence-transformers==3.3.1" \
        "torch==2.5.1+cpu" \
        --extra-index-url https://download.pytorch.org/whl/cpu; \
    groupadd -r embedder; \
    useradd -r -g embedder -m -d /home/embedder embedder

COPY scripts /opt/agentarmy/scripts

# Pre-create the HF cache dir owned by the runtime user. Docker initializes
# named volumes mounted on top of this path by SEEDING from the underlying
# image content + ownership — so making it embedder-owned here means the
# named volume's first mount preserves write access for our non-root user.
RUN chown -R embedder:embedder /opt/agentarmy \
 && mkdir -p /home/embedder/.cache/huggingface \
 && chown -R embedder:embedder /home/embedder/.cache

USER embedder
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/home/embedder/.cache/huggingface

EXPOSE 8082

CMD ["python", "/opt/agentarmy/scripts/serve.py"]
