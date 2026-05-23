# Multi-stage build for AgentArmy
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements if they exist
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install Azure CLI and other tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Default command - can be overridden
CMD ["python", "-m", "http.server", "8080"]

# Metadata
LABEL org.opencontainers.image.title="AgentArmy"
LABEL org.opencontainers.image.description="AI-powered agent army with Azure infrastructure"
LABEL org.opencontainers.image.version="1.0.0"
