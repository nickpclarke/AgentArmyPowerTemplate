# ARC-ADR-DRAFT — Disambiguator: a high-speed streaming sense-resolution service

- **ID:** ARC-ADR-DRAFT
- **Status:** Proposed (draft / vision)
- **Date:** 2026-05-30
- **Deciders:** platform-architect, knowledge-engineer, ontologist-generalist, async-messaging-engineer
- **Related:** Acronym Squasher ([acronym-squasher.md](../acronym-squasher.md)) is the static, batch, single-sense special case of this service.

## Context

Natural language — in docs, code, chat, agent traffic — is saturated with ambiguous
**surface forms**. Three families, one underlying problem:

| Family | One ↔ many | Example |
|---|---|---|
| **Acronyms** | one surface → many expansions | `MC` = middle-core │ Master of Ceremonies │ Marginal Cost |
| **Homonyms / polysemy** | one surface → many senses | `bridge` = the `agent-army-docker-bridge` repo │ a network bridge │ a verb |
| **Synonyms / aliases** | many surfaces → one referent | `backend-core` = `BE` = "the API layer" |

The right sense depends on **context** (surrounding tokens, active domain, who's
speaking, what was just resolved) and **shifts over time within a stream** — a later
sentence can retroactively change what an earlier token meant. The Acronym Squasher
solved the easy corner (one fixed expansion per acronym, whole-doc, offline). The
general capability is a **streaming Word-Sense Disambiguation (WSD) + entity-linking
service**: ingest a token stream, emit a continuously-revised array of resolutions.

## Decision drivers

- **Speed** — bounded per-token latency; O(n) over the stream; most tokens resolve in microseconds. *(Realized: the Rust core `tools/disambiguator-rs/` runs ~13–14 M tokens/sec single-thread, ~72 ns/token, zero-dependency.)*
- **Context-sensitivity** — same surface resolves differently per stream/domain/conversation state.
- **Revisability** — resolutions are provisional; later context emits *revisions*, not just appends.
- **Cost-awareness** — escalate to embeddings / LLM only for the genuinely ambiguous minority.
- **Knowledge-graph-backed** — reuse the fleet's ontology stack so acronyms, synonyms, homonyms, and entities share one sense inventory.
- **Fleet-native** — ride NATS / CloudEvents / event-bridge; no new bus.

## Core model

```
stream of tokens ─▶ [surface detection] ─▶ [candidate senses] ─▶ [context scoring]
                                                                        │
                          ┌─────────────────────────────────────────────┘
                          ▼
            per-stream resolution state  (the "array that shifts")
            surface ─▶ { sense, confidence, provenance, validInterval, version }
                          │
                          ├─▶ emit Disambiguation event   (new resolution)
                          └─▶ emit Revision event         (confidence/sense changed)
```

The central object is a **per-stream resolution map** — a live array of
`Resolution` records that is *mutated and versioned* as the stream advances. That is
the user's "array of mapped disambiguations which may shift over time."

```jsonc
// Resolution record (emitted as a CloudEvent)
{
  "surface": "MC",
  "span": { "start": 1043, "end": 1045 },
  "sense": "kb://entity/middle-core",      // canonical referent in the knowledge graph
  "confidence": 0.91,
  "alternates": [ { "sense": "kb://concept/marginal-cost", "confidence": 0.06 } ],
  "tier": 1,                                // which resolver tier decided it (0..3)
  "provenance": ["domain:fleet-ops", "window:±12", "prior:0.7"],
  "validInterval": { "from": "<HLC>", "to": null },  // time-varying; revisable
  "version": 2                              // bumped on each revision
}
```

## Architecture

A tiered pipeline — cheap-and-fast first, expensive-and-smart only when needed.

| Stage | Responsibility | Realized by |
|---|---|---|
| **Ingest** | accept a stream (HTTP push or subject subscribe), CloudEvents-wrapped | `event-bridge` (`:8080`) → NATS JetStream `FLEET` |
| **Lexicon / sense inventory** | surface form → candidate senses, with domain tags, priors, validity intervals | knowledge graph (ArcadeDB / Fuseki); **SKOS** `altLabel`/`prefLabel` for synonyms, the **glossary** for acronyms, a **UFO/BFO** ontology for entity senses |
| **Surface detection** | O(n) multi-pattern match over the token window | Aho-Corasick automaton compiled from the lexicon (generalizes `acronyms.mjs`'s regex bank) |
| **Context scorer (tiered)** | pick the sense | **T0** lexicon prior + active-domain filter (µs) → **T1** sliding-window co-occurrence + recent-resolution state → **T2** embedding similarity (`local-embedder`, #184) → **T3** `llm-gateway` for the hard residue |
| **Stream resolver** | maintain the revisable per-stream map; order revisions; emit deltas | windowed, stateful; **HLC**-ordered so out-of-order/late context revises deterministically |
| **Output** | emit Disambiguation / Revision events; serve current-state snapshot | CloudEvents on NATS; a queryable `GET /streams/{id}/resolutions` snapshot |
| **Feedback loop** | grow the lexicon; tune priors; escalate novelty | low-confidence / novel surfaces → `hitl-coordinator` Decision; confirmed senses → `knowledge-synthesizer` updates priors; new entries authored by `taxonomist` (SKOS) / `ontologist-generalist` (senses) |

### Why tiered is the whole game

Empirically most tokens are unambiguous or have a dominant sense — **T0 resolves the
vast majority at lexicon-lookup speed.** Only the ambiguous minority climbs to
embeddings (T2) or the LLM (T3). This keeps the service streaming-fast and cheap, and
it's the same cost-discipline as the fleet's existing `llm-gateway` / FinOps posture.

### Revisability (the "shifts over time" requirement)

Each `Resolution` carries a `validInterval` and `version`. When later context changes
a score past a hysteresis threshold, the resolver emits a **Revision** event (a delta,
not a re-send) and bumps the version. Consumers can replay the resolution history of a
span. HLC timestamps give a total order across late/out-of-order arrivals without a
central clock — so two workers resolving the same stream converge.

## Phased roadmap

1. **P1 — Static lexicon, batch (DONE).** Acronym Squasher: glossary as lexicon, whole-doc, one sense. The seed.
2. **P2 — Streaming T0/T1.** Aho-Corasick matcher + lexicon priors + window heuristics over a NATS stream; emit Disambiguation events. No ML yet. **→ runnable PoC: [`tools/disambiguator/`](../../tools/disambiguator/README.md)** (context-sensitivity + revision proven; transport/KG/T2-T3 still stubbed).
3. **P3 — Context + embeddings (T2).** Domain/conversation state; `local-embedder` for semantic tie-breaks; synonyms via SKOS. **→ the ontology-fed lexicon is already prototyped: `tools/disambiguator/skos-adapter.mjs` turns a Fuseki SKOS `CONSTRUCT` into surfaces/senses/cues (graph topology = model).** This is the **shared-service loop**: ontology pipelines *feed* the lexicon (SKOS → senses) and *consume* the output (resolved concept IRIs → entity links back into the graph).
4. **P4 — Revisable online (T3 + feedback).** HLC-ordered Revision events; `llm-gateway` for the hard residue; HITL-driven lexicon growth.
5. **P5 — Cross-stream entity resolution.** Same-as / identity resolution across streams (the Data-Vault `same-as` discipline applied to language), so `BE`/`backend-core`/"the API layer" collapse to one referent fleet-wide.

## Consequences

**Good:** one capability spans acronyms + homonyms + synonyms + entities; comprehension
debt is paid down continuously, not just in docs; agents get a shared, context-aware
"what does this token mean here" service; reuses the existing bus + KG + embedder + LLM
gateway rather than new infra.

**Costs / risks:** lexicon **governance** becomes load-bearing (who curates senses?
→ knowledge-ontology cluster + HITL); the LLM tier needs a hard budget cap or it
eats latency/cost; **eventual-consistency** of revisions means consumers must handle
"the answer changed"; **evaluation** needs real WSD/entity-linking metrics
(precision/recall, accuracy@k) and a labelled set, or quality is unknowable.

## Open questions

- Sense inventory store: extend the **glossary** format, or model senses natively as
  SKOS concepts + ontology individuals from day one?
- Per-stream state lifetime / eviction policy for long-lived streams.
- Is the revision hysteresis global, or per-surface-learned?
- Where's the line between this service and the existing ontology "sieve" (Fuseki/SHACL)?
