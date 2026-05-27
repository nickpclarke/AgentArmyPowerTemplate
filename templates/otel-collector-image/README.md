# otel-collector-image — scaffold

**Status:** scaffold (image.json + this README only). Dockerfile, `setup.sh`, `config/sidecar.yaml`, `config/standalone.yaml`, and `scripts/otel-doctor.sh` land in the implementation issue (linked in the contracts.md backlog row XC-2).

## What this image will be

An OpenTelemetry Collector function-tier image with two operating modes:

- **Sidecar mode** — co-deployed with each spoke. Receives OTLP on gRPC `:4317` + HTTP `:4318`, batches, and forwards to the standalone fleet collector (or directly to the configured backend in single-region deployments).
- **Standalone mode** — fleet-wide receiver with tail-sampling for cost control before exporting to Grafana Tempo / Honeycomb / Tempo+Loki.

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Independent rollout** — collector config changes ship without rebuilding any spoke.
- **Different scale curve** — telemetry volume tracks request rate, not application logic. A noisy backend doesn't need to bring the collector with it.
- **Different release cadence** — collector binary releases follow upstream OTel; spoke releases follow product velocity.

## Realizes

- [ARC-ADR-010 — observability standard](../../docs/decisions/ARC-ADR-010-observability-standard.md) (assumed to exist; placeholder until verified)
- [ARC-ADR-024 — platform maturity audit](../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md): the `otel-not-initialized` remediation track flagged by `tools/fleet-heartbeat.mjs` against frontend-core + middle-core lands here.

## Backlog row

See `docs/contracts.md` Backlog row **XC-2 (OTel trace-context)** — the contract this image realizes.
