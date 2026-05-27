# otel-collector-image

OpenTelemetry Collector function-tier image. Two operating modes baked into one image:

- **Standalone** (default `CMD`) — the fleet's terminal collector. Receives OTLP from all sidecars, applies tail sampling, writes to file (default) or forwards to a real backend.
- **Sidecar** — co-deployed with a spoke. Receives OTLP locally, batches, forwards to the standalone fleet collector.

Realizes [ARC-ADR-010](../../docs/decisions/ARC-ADR-010-observability-standard.md) (observability standard) and the OTel-init remediation track from [ARC-ADR-024](../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md). Closes hub issue #280.

## Quick start (local)

```bash
cd templates/otel-collector-image
./setup.sh
```

This builds the image, brings up the container in standalone mode with the file exporter, waits for readiness, and runs the doctor. Expected output: **4 pass, 0 fail**.

Tear down:

```bash
./setup.sh --down
```

## Selecting mode

`OTELCOL_MODE` is honored by the example compose file's `command:` override (the base image is distroless — no shell — so we can't use a shell-wrapper entrypoint that branches on env vars).

```yaml
# Standalone (default — also what setup.sh runs)
services:
  otel-collector:
    image: agentarmy-otel-collector:local
    # No `command:` override needed; Dockerfile CMD is standalone.yaml

# Sidecar — override the CMD
services:
  otel-collector-sidecar:
    image: agentarmy-otel-collector:local
    command: ["--config=/etc/otelcol-contrib/sidecar.yaml"]
    environment:
      OTEL_DOWNSTREAM_ENDPOINT: otel-collector:4317
```

## Switching exporters in standalone mode

**Important gotcha:** the OpenTelemetry Collector's env-var substitution does **NOT** support shell-style defaults (`${env:VAR:-fallback}` resolves to lookup of a variable named literally `VAR:-fallback`). So we ship `standalone.yaml` with only the `file` exporter wired into the pipelines — adding Tempo / Honeycomb / any OTLP-compatible backend requires extending the config, not toggling an env var.

Two paths:

**A. Mount your own config over the baked one** (preferred for prod):

```yaml
services:
  otel-collector:
    image: agentarmy-otel-collector:local
    command: ["--config=/etc/otelcol-contrib/custom.yaml"]
    volumes:
      - ./my-config.yaml:/etc/otelcol-contrib/custom.yaml:ro
```

**B. Build an extended image** — copy `templates/otel-collector-image/`, add your exporter block to `config/standalone.yaml`, rebuild.

## Configuration

| Env var | Required? | Default | Used by | Meaning |
|---|---|---|---|---|
| `OTEL_TAIL_SAMPLE_PCT` | yes (standalone) | — | tail_sampling | Sampling percentage 0–100 for non-error traces |
| `OTEL_ENVIRONMENT` | yes (standalone) | — | resource processor | Tag spans with `deployment.environment` |
| `OTEL_DOWNSTREAM_ENDPOINT` | yes (sidecar) | — | otlp/forward exporter | gRPC endpoint of the standalone fleet collector |

The example compose file (`examples/compose.otel-collector.example.yml`) sets all of these to sensible local-dev values.

## Doctor checks

`scripts/otel-doctor.sh` proves:

1. `/:13133` returns 200 (readiness)
2. OTLP HTTP `POST /v1/traces` on `:4318` returns 200/202
3. TCP `:4317` (gRPC) accepts connections (curl can't speak gRPC; we test reachability)
4. A span emitted by the doctor appears in the file exporter output after the 5s batch flush

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Independent rollout** — collector config changes ship without rebuilding any spoke.
- **Different scale curve** — telemetry volume tracks request rate, not application logic.
- **Different release cadence** — collector binary releases follow upstream OTel; spokes follow product velocity.
