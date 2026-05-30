# One-shot loader image for the platform self-model -> Azure ArcadeDB (in-VNet).
# Built via `az acr build` (no local docker). Runs as a Container Apps Job inside
# cae-arcade-platform so it can reach arcadedb over private ingress.
FROM python:3.11-slim
WORKDIR /job
RUN pip install --no-cache-dir httpx
COPY load.py fragments.json arcadedb-schema.sql ./
ENV SELFMODEL_FRAGMENTS=/job/fragments.json \
    SELFMODEL_SCHEMA=/job/arcadedb-schema.sql
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /job
USER appuser
CMD ["python", "load.py"]
