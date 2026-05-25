---
tags: [middle-core, scenario]
track: middle-core
---
# Scenarios

Reusable flows that exercise platform capabilities. Each scenario is a [[scenario-template]]; a run is a [[capability-exercise]] that produces an [[evidence-pack]].

| Scenario | Proves | Touches |
|---|---|---|
| knowledge-drop | upload, land, ingest, chunk, index mixed content | [[knowledge-source]], [[knowledge-chunk]] |
| semantic-constellation | cross-modal search + graph projection | [[knowledge-chunk]], [[knowledge-graph-snapshot]] |
| schema-scout | ArcadeDB schema / type / index / count / sample inspection | [[knowledge-graph-snapshot]] |
| read-only-query-lab | guarded read-only query (limits, redaction, metrics) | [[knowledge-graph-snapshot]] |
| evidence-pack | proof-bundle assembly for completion / promotion | [[evidence-pack]] |
| agent-route-and-prove | route work, require gates, capture learning | [[work-packet]], [[decision-record]], [[evidence-pack]] |
