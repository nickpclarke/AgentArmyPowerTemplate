# ARC-ADR-026 — Adopt Data Vault 2.1 as the Enterprise Warehouse Methodology

| Field      | Value                                                |
|------------|------------------------------------------------------|
| ID         | ARC-ADR-026                                          |
| Status     | Proposed                                             |
| Date       | 2026-05-27                                           |
| Deciders   | Architecture Review                                  |
| Supersedes | —                                                    |
| Superseded by | —                                                 |
| Tags       | data-vault, warehouse, analytics, methodology, dbt   |

---

## Context and Problem Statement

AgentArmy spokes increasingly need an analytics warehouse layer with three properties at once: source-system independence (so a spoke can ingest CRM, billing, events without coupling consumers to source shape), historical preservation with audit (so we can answer "what did we know at time T"), and parallel/idempotent loads (so the platform scales horizontally with the existing event-bus and dlt pipelines).

The repository already commits to three adjacent decisions that constrain the warehouse choice:

1. **[ARC-ADR-009 — Canonical Data Model (Arrow)](ARC-ADR-009-canonical-data-model-arrow.md)** defines the cross-spoke data *contract*. The warehouse is a *consumer* of this contract, not a replacement.
2. **[ARC-ADR-022 — Event Bus Bridges](ARC-ADR-022-event-bus-bridges.md)** establishes streaming as a core integration mechanism. Any warehouse methodology must accept streaming as a first-class load shape, not a bolt-on.
3. **[ARC-ADR-016 — Ontology Representation (Reification and Hyperedges)](ARC-ADR-016-ontology-representation-reification-hyperedges.md)** plus the [IKW-GraphEngine track](../../obsidian/labs/AgentArmyLabs/IKW-GraphEngine%20%28Parallel%20Track%29.md) put a graph projection on the consumption layer. The warehouse must produce data shapes that project cleanly to a graph.

No methodology has been picked. Existing data work (`data-engineer`, `dlt-engineer`, `schema-migration-engineer`, `information-architect`) covers ingestion, schema migration, and information architecture, but the *warehouse modeling discipline* — when to introduce a hub vs a link, where business rules live, how history is preserved — is unowned and informal.

The methodology must satisfy:

| # | Driver |
|---|--------|
| D1 | Schema-on-write integration layer that decouples consumers from source shape. |
| D2 | History preservation with audit (`load_date`, `record_source`) by default, not as an opt-in. |
| D3 | Parallel, idempotent loads compatible with our existing dlt + event-bus stack. |
| D4 | First-class streaming support — micro-batch and continuous. |
| D5 | Multi-dialect (Snowflake, Postgres, BigQuery, Databricks) without methodology change. |
| D6 | Composable with a graph projection as one of several consumption shapes. |
| D7 | Macro-driven implementation that doesn't depend on a single ETL vendor. |
| D8 | Clear MECE boundary against existing agents (`data-engineer`, `dlt-engineer`, `information-architect`, `schema-migration-engineer`). |

---

## Considered Options

1. **Data Vault 2.1** (chosen) — Linstedt's methodology, 2.1 supplement formalizing streaming, graph projection, business vault patterns, and managed self-service BI. Reference loader: dbt + Datavault4dbt.
2. **Data Vault 2.0** — Same methodology, older revision. Streaming and graph projection are not first-class.
3. **Kimball star schema as the primary model** — Dimensional modeling end-to-end, no integration layer.
4. **Inmon-style 3NF EDW** — Normalized enterprise data warehouse, dimensional marts on top.
5. **Anchor Modeling** — Attribute-per-table 6NF methodology with bi-temporal history.
6. **Medallion (bronze/silver/gold) without methodology** — Storage layering convention from Databricks, no opinionated modeling rules.

---

## Decision Outcome

**Option 1 — Data Vault 2.1** is adopted.

Every analytics-bearing spoke (current and future) targets a three-layer DV 2.1 architecture: **stage → raw vault → business vault → information marts**. Hash keys are SHA-256 with canonical ordering, UTF-8 NFC normalization, `^^` null sentinel, and `||` separator. The reference loader is **dbt + [Datavault4dbt](https://github.com/ScalefreeCOM/datavault4dbt)** but the methodology is loader-agnostic — the model spec at `tools/data-vault/model.schema.json` is the single source of truth and is rendered to DDL + dbt stubs by `tools/data-vault/model-generator.mjs`.

Three specialist agents own the methodology: `data-vault-architect` (strategy & raw/business split), `data-vault-modeler` (logical model), `data-vault-engineer` (build, load, serve). Their MECE boundary against existing data agents is documented in [`docs/data-vault/strategy.md`](../data-vault/strategy.md) and in their respective agent files.

### Confirmation criteria

- [`docs/data-vault/strategy.md`](../data-vault/strategy.md), [`patterns.md`](../data-vault/patterns.md), and [`glossary.md`](../data-vault/glossary.md) are merged and linked from `docs/index.md` (or equivalent landing).
- Three agents (`data-vault-architect`, `data-vault-modeler`, `data-vault-engineer`) pass `AGENT_ONBOARDING_RUBRIC.md` and are wired into the `CLAUDE.md` routing table.
- `tools/data-vault/model-generator.mjs`, `hash.mjs`, `hash.py`, `lineage-doc.mjs`, `adr-scaffold.mjs` exist, have a `--help`, and pass their self-tests.
- An example model spec (`tools/data-vault/examples/sample-model.yaml`) is parsed by the generator without error and produces DDL for at least Snowflake and Postgres dialects.
- One spoke commits to a Phase 1 raw vault per the roadmap in [`strategy.md §8`](../data-vault/strategy.md#8-adoption-roadmap).

---

## Pros and Cons of the Options

### Option 1 — Data Vault 2.1 (chosen)

DV 2.1 directly satisfies all eight drivers:

**Pros:**
- D1: The raw vault *is* the schema-on-write integration layer. That's its entire job.
- D2: `load_date` and `record_source` are mandatory columns on every vault row by methodology rule.
- D3: Hash keys make every loader deterministic and parallel. Idempotency is a side-effect of hash-diff comparison.
- D4: DV 2.1 specifically formalizes streaming load (micro-batch + continuous) and the late-arriving-key pattern via ghost hub rows.
- D5: The methodology is platform-agnostic. Datavault4dbt supports Snowflake, Postgres, BigQuery, Databricks, Exasol with the same macros.
- D6: Hubs project to nodes, links to edges. The graph projection is one of four standard mart shapes in DV 2.1.
- D7: dbt + Datavault4dbt is the reference, but the model spec → DDL path means we can swap loaders without changing the model.
- D8: The DV discipline (hub/link/sat design, business vault rules) is genuinely distinct from `data-engineer` (pipeline architecture), `dlt-engineer` (ingestion mechanics), `information-architect` (enterprise data architecture), and `schema-migration-engineer` (DDL evolution). The three DV agents fill a real gap.

**Cons:**
- Learning curve: the team needs to internalize hubs/links/sats vs facts/dims. Mitigated by patterns.md and 3 specialist agents.
- Hash-diff false negatives are theoretically possible (probability ~2⁻¹²⁸ for SHA-256 collision in a single sat). Accepted.
- Macro-driven generation means we own a model spec format and a generator. Mitigated by keeping the spec narrow (see `model.schema.json`).

---

### Option 2 — Data Vault 2.0

Same methodology, 2.0 revision.

**Pros:** Mature, lots of literature, identical core constructs.

**Cons:** Misses D4 and D6 — streaming and graph projection are workarounds, not first-class. Choosing 2.0 means we'd be re-deriving 2.1's solutions ourselves. Zero benefit over 2.1.

---

### Option 3 — Kimball star schema as the primary model

Dimensional modeling from source to BI tool, no integration layer.

**Pros:**
- BI tools love star schemas; less mart layer effort.
- Familiar to most analysts.

**Cons:**
- Violates D1: there's no integration layer. Consumers are coupled to the dim/fact shape, and a source schema change ripples to every mart.
- Violates D2: SCD2 handles history *per dimension*, not platform-wide. Audit columns are per-design, not by methodology.
- Violates D3: parallel load across dims/facts is harder because surrogate-key dependency chains are serial.
- Violates D8 partially: star-schema design is largely covered by `information-architect` and `data-engineer` already.

A star schema is the *right shape for a mart*, not for the warehouse. DV 2.1 produces stars *out of* the vault — see [`patterns.md §14`](../data-vault/patterns.md#14-information-mart--star-schema).

---

### Option 4 — Inmon-style 3NF EDW

Normalized enterprise data warehouse, dimensional marts downstream.

**Pros:**
- Strong integration layer — that part is similar to DV.
- Familiar to teams from traditional enterprise warehousing.

**Cons:**
- Violates D2: 3NF + SCD2 is verbose, inconsistent across tables, and history is bolted on per-table rather than methodology-level.
- Violates D3: parallel load is hard because foreign keys force serial order.
- Violates D4: streaming into a 3NF EDW is awkward — every late-arriving key violates a FK constraint.
- Schema change cost is high: renaming a single source column can require migrations across many normalized tables.

DV's hub/link/sat decomposition is essentially a 3NF refactor where the integration semantics are pushed into the *table type* (hub = entity, link = relationship, sat = attribute group), giving you the integration benefit *and* parallel/idempotent loads *and* uniform history.

---

### Option 5 — Anchor Modeling

6NF attribute-per-table methodology with bi-temporal history.

**Pros:**
- Theoretically the cleanest history model (bi-temporal).
- Even more granular than DV.

**Cons:**
- Violates D7 hard: tooling ecosystem is small (no dbt-equivalent macro package with broad community).
- Query cost on 6NF is high; every consumer needs a join layer.
- Violates D5: dialect-specific implementations are sparse.
- Team skill availability is near zero industry-wide.

Anchor Modeling is academically attractive but pragmatically isolated. Adoption cost outweighs the marginal history-modeling benefit over DV's satellites.

---

### Option 6 — Medallion (bronze/silver/gold) without methodology

Storage layering convention from Databricks; no opinionated modeling rules within each layer.

**Pros:**
- Familiar from lakehouse contexts.
- No methodology learning curve.

**Cons:**
- Violates D1: bronze/silver/gold tells you *where* data lives, not *how it's modeled*. Without a methodology, "silver" devolves into whatever-shape-the-pipeline-emits.
- Violates D2: history is per-table convention, not methodology rule.
- Violates D8: this isn't a methodology, it's a folder structure. The actual modeling discipline is still missing.

Medallion *layers* are compatible with DV — bronze ≈ stage, silver ≈ raw vault, gold ≈ marts — but they don't *replace* the need for DV's modeling rules.

---

## Positive Consequences

- The discipline of "warehouse modeling" is owned by a clear three-agent team with MECE boundaries against the existing data roster.
- Schema-on-write integration means a spoke can change its source shape without breaking downstream consumers — only the staging layer changes.
- Audit and history are guaranteed by methodology, not by per-project memory.
- Streaming and graph projection are explicit first-class load/serve shapes, not "we'll figure it out."
- The model spec format becomes a contract that travels with the spoke; the generator emits DDL + dbt stubs deterministically.
- Multi-dialect: the same model spec produces working DDL on Snowflake, Postgres, and BigQuery.

## Negative Consequences

- Team must invest in DV literacy. Mitigated by patterns.md + 3 agents.
- The model spec format and generator are new artifacts to maintain. Mitigated by keeping the spec minimal.
- Business vault virtualization vs materialization decisions are non-trivial per case. The architect agent owns this judgment.

## Related decisions

- [`ARC-ADR-009`](ARC-ADR-009-canonical-data-model-arrow.md) — Canonical Data Model (Arrow). DV consumes this contract.
- [`ARC-ADR-016`](ARC-ADR-016-ontology-representation-reification-hyperedges.md) — Ontology representation. The graph mart projection follows these reification rules.
- [`ARC-ADR-022`](ARC-ADR-022-event-bus-bridges.md) — Event bus bridges. The streaming load path consumes this.
- [`ARC-ADR-023`](ARC-ADR-023-container-tiering-strategy.md) — Container tiering. Warehouse engines run as **platform** tier.

## Open questions (deferred)

- Vendor DV tools (WhereScape, Vaultspeed, BimlFlex) — re-evaluate at Phase 4 of the [adoption roadmap](../data-vault/strategy.md#8-adoption-roadmap) if dbt-macro maintenance becomes the bottleneck.
- Right-to-be-forgotten implementation: tombstone-link pattern is documented but not yet exercised against a regulatory request. Spike when the first PII-bearing raw vault lands.
- Bi-temporal queries (transaction time + valid time): DV handles transaction time natively via `load_date`; valid time is a business-vault effectivity-satellite pattern. Defer formal bi-temporal API until a use case demands it.
