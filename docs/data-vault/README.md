# Data Vault 2.1 — AgentArmy Strategy & Toolkit

This is the entry point for everything Data Vault 2.1 in AgentArmy: the strategy, the patterns, the agent team, and the tooling.

## What lives here

| Doc | Purpose |
|---|---|
| [strategy.md](strategy.md) | The full DV 2.1 architecture, principles, raw-vs-business vault split, and adoption roadmap. The "north star" doc. |
| [patterns.md](patterns.md) | Concrete implementation patterns: hash keys, hash diffs, multi-active sats, effectivity sats, PIT/bridge, real-time load. |
| [glossary.md](glossary.md) | Disambiguated DV 2.1 vocabulary, with notes on what changed in 2.0 → 2.1. |

The anchor decision is [`ARC-ADR-026 — Data Vault 2.1 as the Enterprise Warehouse Methodology`](../decisions/ARC-ADR-026-data-vault-2-1-methodology.md).

## The DV team (3 agents)

| Agent | Owns |
|---|---|
| [`data-vault-architect`](../../.claude/agents/categories/05-data-ai/data-vault-architect.md) | Strategy. Raw vs business vault split, source-to-hub mapping, governance, methodology adoption. |
| [`data-vault-modeler`](../../.claude/agents/categories/05-data-ai/data-vault-modeler.md) | Logical model. Hubs, links, satellites, references, multi-active and effectivity satellites, modeling anti-patterns. |
| [`data-vault-engineer`](../../.claude/agents/categories/05-data-ai/data-vault-engineer.md) | Build & load. dbt + Datavault4dbt macros, hash-key/hash-diff implementation, PIT/bridge tables, information marts, CI. |

Boundaries are MECE: the architect designs the *what and why*, the modeler designs the *shape*, the engineer designs the *load and serve*.

## The toolkit

All tools live in [`tools/data-vault/`](../../tools/data-vault/) and are dialect-agnostic (Snowflake, Postgres, BigQuery, Databricks).

| Tool | What it does |
|---|---|
| `model-generator.mjs` | YAML/JSON model spec → DDL + dbt model stubs (Datavault4dbt-compatible) for hubs, links, sats, refs. |
| `hash.mjs` / `hash.py` | DV-2.x-compliant SHA-256 hash-key and hash-diff utilities with canonical ordering, Unicode normalization, and null-handling rules. |
| `lineage-doc.mjs` | Reads a model spec, emits Mermaid diagrams + Markdown lineage docs for the board. |
| `adr-scaffold.mjs` | Pre-fills a DV-2.1-flavored ADR (`ARC-ADR-NNN-…`) for decisions like raw-vs-business placement, hash algorithm, multi-active strategy. |

See [`tools/data-vault/README.md`](../../tools/data-vault/README.md) for usage.

## How to start

1. Read [strategy.md](strategy.md) end-to-end.
2. Skim [patterns.md](patterns.md) for the implementation idioms you'll actually use.
3. Author a model in YAML against `tools/data-vault/model.schema.json` (see `tools/data-vault/examples/sample-model.yaml`).
4. Run the model generator to scaffold DDL + dbt stubs.
5. Loop in the agents:
   - architect for "should this be in raw or business vault?"
   - modeler for "is this hub or link? multi-active or not?"
   - engineer for "how do we load this idempotently and serve it through a mart?"

## Why DV 2.1 and not 2.0

DV 2.1 keeps everything 2.0 did (hash keys, hash diffs, parallel load, audit columns) and tightens four things:

- **Real-time / streaming** is a first-class load pattern, not a workaround.
- **NoSQL & graph integration** is in scope, including how a graph projection (e.g. ArcadeDB) coexists with the raw vault.
- **Managed self-service BI** through information marts is formalized — the consumption layer is part of the methodology, not an afterthought.
- **Business vault** patterns are formalized: same-as links, computed satellites, PIT, bridge — with explicit guidance on when to materialize vs virtualize.

See [strategy.md](strategy.md#why-data-vault-21) for the long version.
