# local-embedder-image — scaffold

**Status:** scaffold (image.json + this README + `setup.sh` placeholder). Dockerfile, `scripts/serve.py`, `scripts/embedder-doctor.sh`, and the model-selection logic land in the implementation issue.

## What this image will be

A local embedding-vector service implementing the OpenAI-compatible `/v1/embeddings` endpoint so the fleet's RAG layer can use local models for ArcadeDB-backed retrieval without paying per-call to OpenAI/Cohere.

Hardware targets, in priority order:

1. **Intel Arc iGPU via OpenVINO** — best fit for the office dev box (per `reference_local_model_serving` memory: Core Ultra 7 265 / 32GB / Arc iGPU / no dGPU).
2. **CPU fallback** — sentence-transformers PyTorch path.
3. **NVIDIA CUDA** — when deployed to a cloud node with a GPU.

Hub issue [#184](https://github.com/nickpclarke/AgentArmy/issues/184) is the implementation pin.

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Different hardware profile** — needs NPU/iGPU/GPU access, which the application-tier spoke containers don't.
- **Different scale curve** — embedding throughput tracks document ingestion volume, not request rate.
- **Independent release cadence** — model upgrades happen on the embedder's own schedule, decoupled from any spoke.

These three together are the load-bearing reasons this is its own image rather than a sub-module inside backend-core.

## Backlog row

`docs/contracts.md` Backlog row **BE-4 (Embeddings API)** is the contract this image realizes. Until BE-4 lands as a dedicated spec, the embedder implements the embeddings slice of `contracts/llm-gateway.openapi.yaml`.
