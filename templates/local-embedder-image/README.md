# local-embedder-image

Local embedding service — function-tier image generating dense vectors for ArcadeDB RAG. Exposes the OpenAI-compatible `POST /v1/embeddings` endpoint so callers swap between cloud and local embeddings without code changes.

Closes hub issue #281. Hub #184 is the broader model-serving pin.

## Quick start

```bash
cd templates/local-embedder-image
./setup.sh
```

This builds the image, brings up the container (CPU mode, default model), waits for `/livez`, and runs the doctor. First run takes 60–90s while sentence-transformers downloads the model (~133 MB) into the persistent volume; subsequent runs are seconds.

Expected output: **5 pass, 0 fail**.

```bash
./setup.sh --down   # also drops the model cache volume
```

## Embedding endpoint

OpenAI-compatible. Single string OR array.

```bash
curl -sS http://localhost:8082/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":"hello world"}'
```

Response (truncated):

```json
{
  "object": "list",
  "model": "BAAI/bge-small-en-v1.5",
  "data": [
    { "object": "embedding", "index": 0, "embedding": [0.0123, -0.0456, ...] }
  ],
  "usage": { "prompt_tokens": 4, "total_tokens": 4 }
}
```

## Health surface

| Endpoint | Auth-free? | Returns | Use case |
|---|:---:|---|---|
| `/livez` | ✅ | 200 always (no dependency checks) | LB liveness probe |
| `/readyz` | ✅ | 200 when model is loaded, 503 + Problem Details otherwise | LB readiness gate |
| `/healthz` | ✅ | 200 with version + model + dim + per-dependency status | Heartbeat + dashboards |

The model lazy-loads on the first `/v1/embeddings` call. Until then `/readyz` returns 503. This is intentional — the container boots in seconds and serves `/livez` even before the heavy model download completes, which keeps Kubernetes restart logic from killing it during cold-start.

To warm the model proactively (e.g. in a deploy-job step before promoting), send a small embed at startup:

```bash
curl -sS -X POST http://localhost:8082/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"warmup","input":"ok"}' >/dev/null
```

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `EMBEDDER_MODEL` | `BAAI/bge-small-en-v1.5` | HuggingFace model id |
| `EMBEDDER_DEVICE` | `cpu` | Torch device. `cuda` if a GPU is available |
| `EMBEDDER_NORMALIZE` | `true` | L2-normalize embeddings (recommended for cosine sim) |
| `EMBEDDER_MAX_BATCH` | `64` | Max inputs per request (422 if exceeded) |
| `EMBEDDER_PORT` | `8082` | Listen port |

## Hardware roadmap

| Backend | Status | Notes |
|---|---|---|
| CPU (PyTorch) | ✅ Shipped | sentence-transformers 3.3.1 + torch 2.5.1+cpu. Works anywhere. |
| Intel Arc iGPU (OpenVINO) | 🔜 Follow-up | The office dev box has Core Ultra 7 + Arc iGPU; OpenVINO via `optimum-intel` should give 3–5× speedup. Tracked separately. |
| AI Boost NPU | 🔜 Future | Same dev-box silicon; less mature OTel/inference tooling. Re-evaluate when toolchain firms up. |
| CUDA | ✅ Out-of-the-box | Set `EMBEDDER_DEVICE=cuda`; works if torch+cuda wheel is available. Image currently ships the CPU wheel only. |

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Different hardware profile** — NPU/iGPU/GPU divergence from spoke compute.
- **Different scale curve** — embedding throughput tracks document ingestion volume, not request rate.
- **Independent release cadence** — model upgrades happen on their own schedule, decoupled from any spoke.

## Contract anchor

Backlog row **BE-4 (Embeddings API)** in [`docs/contracts.md`](../../docs/contracts.md). Until BE-4 lands as a dedicated spec, this image implements the embeddings slice of [`contracts/llm-gateway.openapi.yaml`](../../contracts/llm-gateway.openapi.yaml) (`POST /v1/embeddings`, the `EmbeddingRequest`/`EmbeddingResponse` schemas).
