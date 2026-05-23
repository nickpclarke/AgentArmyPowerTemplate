# Example multi-stage image for Cloud Run.
#
# Cloud Run routes traffic to the port in $PORT (default 8080) — your app MUST
# listen on 0.0.0.0:$PORT. The structure below (small base, non-root user,
# $PORT) applies to any language; swap the Python specifics for your stack.

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080
WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
# Non-root user (least privilege; required by some org policies).
RUN useradd --create-home --uid 10001 appuser
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .
USER appuser
EXPOSE 8080
# Bind to 0.0.0.0:$PORT so Cloud Run can reach the container.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
