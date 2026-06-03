# Cross-Layer Docker Networking

*Last updated: 2026-05-31 · Sprint: current*

## Overview

All n-layer services share a common Docker network (`agentarmy-local-stack_default`) for local development, enabling **direct cross-layer HTTP communication** without port-forwarding hacks. This means backend-core, middle-core, frontend-core, and commons-core containers can reach each other by service name, just as they would in a production cluster.

!!! info "Why a shared external network?"
    Docker Compose creates an isolated network per project by default. When each spoke repo has its own `docker-compose.yml`, their containers can't talk to each other. The shared external network solves this — all spokes join the same network and resolve each other by DNS name.

## Docker Compose Configuration

Every spoke repo's `docker-compose.yml` declares the shared network as **external** and attaches its services to it:

```yaml
# Example: backend-core/docker-compose.yml
services:
  app:
    build: .
    container_name: application-layer
    networks:
      - agentarmy-local-stack_default
    # ... other config

  rust-api:
    build: ./rust-api
    container_name: uda-function-layer
    networks:
      - agentarmy-local-stack_default
    # ... other config

networks:
  agentarmy-local-stack_default:
    external: true
```

!!! warning "The `external: true` line is critical"
    Without `external: true`, Docker Compose will attempt to create a *new* network scoped to this project. With `external: true`, it joins the pre-existing shared network. If the network doesn't exist yet, `docker compose up` will fail with a clear error.

## Service Naming

Each repo renames its Docker Compose services to **n-layer names**, providing a consistent naming scheme across the fleet:

| Repo | Docker Service | N-Layer Container Name | Port |
|---|---|---|---|
| backend-core | `app` | `application-layer` | 8000 |
| backend-core | `rust-api` | `uda-function-layer` | 8080 |
| middle-core | `model` | `semantic-governance-layer` | 8001 |
| middle-core | `runtime` | `agent-orchestration-layer` | 8002 |

These container names become **DNS hostnames** on the shared network. Any container on `agentarmy-local-stack_default` can reach `application-layer` at `http://application-layer:8000`.

## URL Configuration

For cross-layer communication, each repo sets environment variables pointing to the other layers:

=== "middle-core → backend-core"

    ```env
    # middle-core/.env
    BACKEND_CORE_URL=http://host.docker.internal:8000
    ```

=== "frontend-core → backend-core"

    ```env
    # frontend-core/.env
    VITE_BACKEND_CORE_URL=http://localhost:8000
    VITE_MIDDLE_CORE_URL=http://localhost:8001
    ```

=== "Container-to-container (inside Docker)"

    ```env
    # When both services are inside Docker:
    BACKEND_CORE_URL=http://application-layer:8000
    MIDDLE_CORE_URL=http://semantic-governance-layer:8001
    ```

!!! tip "host.docker.internal vs container name"
    Use `host.docker.internal` when the caller is inside Docker but the target is exposed on the host (typical for dev). Use the container name (e.g., `application-layer`) when both caller and target are on the same Docker network.

## Prerequisites

The `agentarmy-local-stack_default` network must exist before any spoke's `docker compose up` will succeed.

### Option A — Created by the stack repo

If you run `docker compose up` in the main stack repo first, it creates the network automatically.

### Option B — Manual creation

```bash
docker network create agentarmy-local-stack_default
```

### Verify the network exists

```bash
docker network ls | grep agentarmy-local-stack
```

Expected output:

```
a1b2c3d4e5f6   agentarmy-local-stack_default   bridge    local
```

## Troubleshooting

### Network not found

```
Error: network agentarmy-local-stack_default declared as external, but could not be found
```

**Fix:** Create the network manually:

```bash
docker network create agentarmy-local-stack_default
```

### DNS resolution failure between containers

```
Error: Could not resolve host: application-layer
```

**Possible causes:**

1. **Target container not running** — verify with `docker ps | grep application-layer`
2. **Target container not on the shared network** — verify with `docker network inspect agentarmy-local-stack_default`
3. **Using container name instead of service name** — ensure the `container_name` in `docker-compose.yml` matches what you're resolving

### Port conflicts

If two spokes try to bind the same host port (e.g., both want `8000`), the second `docker compose up` will fail.

**Fix:** Each spoke uses distinct host ports. The mapping is defined in the service naming table above. If you've customized ports, ensure no overlaps.

### Inspecting the network

To see all containers on the shared network:

```bash
docker network inspect agentarmy-local-stack_default --format '{{range .Containers}}{{.Name}} {{end}}'
```

## Related Pages

- [Running Locally (fleet boot)](running-locally.md) — full local dev startup sequence
- [Mobile Live-Data Pipeline](mobile-live-data-pipeline.md) — uses cross-layer networking
- [N-Layer Architecture](n-layer-architecture.md) — the layer model these names map to
