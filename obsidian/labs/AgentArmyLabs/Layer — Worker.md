---
tags: [platform, layer]
track: platform
layer: Worker
---
# Layer — Worker

> [!abstract] Scope
> Background execution: queues, orchestration, long-running scenario runs, retries, and timed pipelines.

**🎛 [[Obsidian Board]] · 🧭 [[Platform Atlas]]**

## Responsibilities

- Run scenarios asynchronously (and record evidence deterministically)
- Coordinate projections (graph snapshots, analytics exports, index builds)
- Maintain idempotency and replayability (“prove again”)

## Interfaces

- Scenario runtime API
- Evidence storage and manifests

Related: [[Factory-Loop-Test-Infrastructure]].
