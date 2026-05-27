# Data Vault 2.1 Strategy

> **Status:** Draft strategy. The anchor decision is [`ARC-ADR-026`](../decisions/ARC-ADR-026-data-vault-2-1-methodology.md). Patterns are in [patterns.md](patterns.md). Vocabulary is in [glossary.md](glossary.md).

## TL;DR

We adopt **Data Vault 2.1** as the enterprise warehouse methodology for any spoke that has analytics, integration, or auditable history requirements. The model splits cleanly into:

- **Raw Vault** — insert-only, history-preserving, schema-on-write copy of source business keys, relationships, and descriptive context. Audited (`load_date`, `record_source`) and hash-keyed (`*_hk`, `*_hd`). Never edited, never deleted.
- **Business Vault** — derived from raw, where business rules live. Same DV constructs (hubs, links, sats) with `_bv` naming and computed/derived attributes. Same audit columns.
- **Information Marts** — consumption layer. Star, snowflake, OBT (one-big-table), or graph projections. Built from PIT and bridge tables, virtualized where possible, materialized where SLA demands it.

The methodology is platform-agnostic. The reference loader is **dbt + [Datavault4dbt](https://github.com/ScalefreeCOM/datavault4dbt)**. Hash algorithm is **SHA-256** with canonical ordering, Unicode normalization, and explicit null handling.

The team is three agents: [`data-vault-architect`](../../.claude/agents/categories/05-data-ai/data-vault-architect.md), [`data-vault-modeler`](../../.claude/agents/categories/05-data-ai/data-vault-modeler.md), [`data-vault-engineer`](../../.claude/agents/categories/05-data-ai/data-vault-engineer.md). The tools are in [`tools/data-vault/`](../../tools/data-vault/).

---

## 1. Why Data Vault 2.1

### 1.1 The problem DV solves

Traditional star schemas optimize for query at the cost of integration. 3NF integrates but doesn't track history cleanly. Both struggle when:

- Source systems change shape mid-PI without warning.
- Multiple sources describe the same business entity differently ("customer" in CRM ≠ "customer" in billing).
- Audit and lineage are regulatory requirements, not nice-to-haves.
- Multiple consumers want the same data shaped differently (BI star, ML feature store, graph traversal, OBT).
- Loads must be parallel and idempotent across a horizontally scaled platform.

Data Vault separates **integration** (raw vault) from **interpretation** (business vault) from **presentation** (info marts). Each layer changes at its own cadence and for its own reason.

### 1.2 What changed from 2.0 to 2.1

| Area | 2.0 | 2.1 |
|---|---|---|
| Real-time / streaming load | Workaround pattern | First-class load type with explicit guidance on idempotent streaming, late-arriving keys, micro-batch vs continuous |
| NoSQL / graph | Mostly out of scope | In-scope projection target alongside the raw vault; covers when a graph (e.g. ArcadeDB) is the right consumption shape |
| Self-service BI | Implicit | Information mart layer is formalized: PIT, bridge, virtualization rules, semantic layer responsibility |
| Business vault | Loose | Formal pattern catalog: same-as links, computed sats, PIT/bridge as business-vault constructs, materialization decision tree |
| Tooling assumption | Vendor ETL implied | Cloud DW + ELT (dbt-flavored) assumed; macro-driven generation is the norm |

We adopt 2.1 because three of those changes (streaming, graph projection, formal business vault) match commitments AgentArmy has already made: the [event-bus bridges](../decisions/ARC-ADR-022-event-bus-bridges.md), the [graph-engine track](../../obsidian/labs/AgentArmyLabs/IKW-GraphEngine%20%28Parallel%20Track%29.md), and the [canonical data model](../decisions/ARC-ADR-009-canonical-data-model-arrow.md).

### 1.3 What DV is *not* for

- **Operational systems of record.** DV is a warehouse pattern. Use it for analytics, integration, and history; not as the OLTP source of truth.
- **Single-source, small-scale, single-consumer.** If you have one source, one consumer, and the source is well-behaved, a star schema or OBT is cheaper.
- **Replacing the canonical data model contract.** DV is downstream of [ARC-ADR-009](../decisions/ARC-ADR-009-canonical-data-model-arrow.md). The canonical model is the *contract*; the raw vault is one *implementation* shaped for warehousing.

---

## 2. The three layers

```
┌─────────────────────────────────────────────────────────────────────┐
│ SOURCE SYSTEMS  (CRM, billing, events, files, APIs)                 │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ ELT  (dlt, Fivetran, Kafka Connect, custom)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE  — typed source-shaped tables, hash-keyed at landing          │
│         (load_date, record_source, hash_keys, hash_diffs)           │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ DV insert-only loaders (idempotent, parallel)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ RAW VAULT  — hubs (business keys), links (relationships),           │
│              satellites (descriptive context with history),         │
│              references (lookups). Source-of-truth for history.     │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ Business rules (dbt models, never editing raw)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BUSINESS VAULT  — same shape, derived. _bv suffix.                  │
│                   Same-as links, computed sats, PIT, bridge.        │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ Projection: star / snowflake / OBT / graph
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ INFORMATION MARTS  — BI, ML feature store, graph, semantic layer    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Raw Vault

Insert-only. History-preserving. Schema-on-write. The raw vault is the **integration layer** — it normalizes source systems around shared *business keys* without imposing business rules.

**Construct types:**

- **Hub** — a unique business entity. One row per natural business key. Columns: `<entity>_hk`, `load_date`, `record_source`, business key column(s).
- **Link** — an association between hubs. Columns: `<link>_hk`, `load_date`, `record_source`, parent `_hk` columns.
- **Satellite** — descriptive context with history. Columns: parent `_hk`, `load_date`, `load_end_date` (or `load_date_source`), `record_source`, `hash_diff`, descriptive attributes.
- **Reference** — code lookups (country, currency, status). Either a thin hub + sat or a flat `ref_*` table.

**Naming conventions** (enforced by the model generator):

| Construct | Pattern | Example |
|---|---|---|
| Hub | `hub_<entity>` | `hub_customer` |
| Link | `lnk_<from>_<to>` | `lnk_customer_order` |
| Satellite | `sat_<parent>_<source>` | `sat_customer_crm` |
| Reference | `ref_<entity>` | `ref_country` |
| Hash key | `<entity>_hk` | `customer_hk` |
| Hash diff | `<sat>_hd` | `customer_crm_hd` |
| Business vault | `..._bv` suffix | `sat_customer_crm_bv` |

**Mandatory audit columns** on every raw vault table:

- `load_date` — when the row entered the warehouse (UTC, microsecond precision).
- `record_source` — opaque string identifying the source (e.g. `crm.salesforce.contact`).
- `<parent>_hk` — hash key(s) of the parent hub(s) or link.
- `hash_diff` (on satellites) — SHA-256 of the concatenated descriptive attributes.

### 2.2 Business Vault

Insert-only. Built from raw. Same construct types, same audit columns, `_bv` suffix.

The business vault is where:

- **Same-as links** unify entities across sources (e.g. `lnk_same_as_customer_bv` joins CRM and billing customers).
- **Computed satellites** materialize derived attributes (lifetime value, churn score, segment).
- **PIT (point-in-time) tables** snapshot the state of a hub + all its satellites at regular intervals to make point-in-time queries cheap.
- **Bridge tables** denormalize multi-hop link traversals for query.

**When to materialize vs virtualize:**

| Construct | Default | Materialize if |
|---|---|---|
| Same-as link | Materialize | Always — identity resolution is too expensive to redo per query |
| Computed sat | Virtualize (dbt view) | Query SLA demands it, OR computation is non-deterministic and must be frozen for audit |
| PIT | Materialize | Daily/hourly snapshots; the whole point is precomputation |
| Bridge | Virtualize | Multi-hop joins on hot paths breach SLA |

### 2.3 Information Marts

The presentation layer. Where the warehouse meets the consumer.

Four canonical projections:

| Projection | When |
|---|---|
| **Star schema** | Tabular BI (Looker, Power BI, Tableau). Dim tables come from hubs + sats. Facts come from links + sats. |
| **Snowflake schema** | Same as star but normalized — useful when dim cardinality is huge and dim hierarchy is deep |
| **OBT (one big table)** | ML feature store, ad-hoc analytics, columnar warehouses where joins are cheap. Wide denormalized projections from PIT + bridge. |
| **Graph projection** | Multi-hop traversal, recommendation, fraud, network analysis. Hubs → nodes, links → edges. See [IKW-GraphEngine track](../../obsidian/labs/AgentArmyLabs/IKW-GraphEngine%20%28Parallel%20Track%29.md). |

Marts are **disposable** by design. If a mart needs to change, you rebuild it from the vault. Never edit the vault to fit a mart.

---

## 3. Hash strategy

Hash keys replace surrogate sequence keys (the DV 2.0 break from 1.0). They enable:

- **Parallel load** — every loader can compute its own keys without coordination.
- **Pre-join** — links can be loaded in parallel with hubs because the key is deterministic.
- **Cross-platform consistency** — the same business key yields the same hash in Snowflake, Postgres, BigQuery.

### 3.1 Algorithm

- **Hash:** SHA-256 (256-bit, hex-encoded, lowercase). NOT MD5 (collision risk at scale) and NOT a database-native hash (portability).
- **Encoding:** UTF-8 after Unicode NFC normalization.
- **Separator:** `||` (double-pipe). Configurable but consistent within a vault.
- **Null handling:** nulls become the literal string `^^` (configurable). This is critical — a null in a business key is itself a meaningful key value.
- **Case:** business keys are case-folded to upper before hashing (configurable; some keys are case-sensitive — e.g. URLs, hashes).
- **Whitespace:** trimmed before hashing.

### 3.2 Hash key construction (hub)

```
hub_customer_hk = sha256_hex( upper(trim(customer_id)) )
```

### 3.3 Hash key construction (link)

```
lnk_customer_order_hk = sha256_hex(
  concat(
    coalesce(upper(trim(customer_id)), '^^'),
    '||',
    coalesce(upper(trim(order_id)),    '^^')
  )
)
```

Parent `_hk` columns on the link are recomputed independently (they must match the hub's `_hk`).

### 3.4 Hash diff (satellite delta detection)

```
sat_customer_crm_hd = sha256_hex(
  concat_ws('||',
    coalesce(first_name,'^^'),
    coalesce(last_name, '^^'),
    coalesce(email,     '^^'),
    coalesce(phone,     '^^')
  )
)
```

Attribute order is **alphabetical by column name**, enforced by the model generator. On load, a new sat row is inserted only when `hash_diff` differs from the previous row for the same parent `_hk`. This is the entire delta-detection mechanism — no triggers, no CDC, just hash comparison.

### 3.5 The `tools/data-vault/hash.mjs` + `hash.py` library

Both libraries implement the same algorithm bit-for-bit. They're the canonical source of truth for hashing logic and ship with a shared test vector file so any new dialect implementation can be verified against them.

---

## 4. Load patterns

### 4.1 Batch (default)

Stage → raw vault, run hourly or nightly. Each loader is idempotent: rerunning the same `load_date` produces no new rows because the hash diffs match.

**Load order constraint:** hubs first, then sats and links in parallel. This is the *only* ordering constraint — within hubs, links, and sats, all loaders can run concurrently.

### 4.2 Streaming (DV 2.1 first-class)

Source is a Kafka topic or equivalent. Two viable shapes:

| Shape | When |
|---|---|
| **Micro-batch into raw vault** | Source event rate is 100s-1000s/s, latency SLA is seconds-to-minutes. Buffer N seconds of events, batch-load. Idempotent because of hash keys + hash diffs. |
| **Stage → raw vault per event** | Source event rate is low or latency SLA is sub-second. Each event flows individually. More expensive per event; only justify with the SLA. |

**Late-arriving keys** (event references a business key that doesn't yet have a hub row): insert a *ghost hub row* with `record_source='deferred'` and let the proper insert deduplicate on hash key. Never block the load.

### 4.3 Real-time business vault

Avoid. The business vault is for rules; rules are batch by nature. If real-time derived attributes are needed, compute them upstream (in the event stream) and feed them as a source into the raw vault, not as a transformation on the raw vault.

---

## 5. Multi-active and effectivity satellites

### 5.1 Multi-active

A multi-active satellite stores **multiple active rows per parent at the same load date** (e.g. a customer with multiple email addresses). The primary key extends from `(parent_hk, load_date)` to `(parent_hk, load_date, sub_sequence)`.

Use only when the source truly has 1:N values per attribute group. Don't model a hierarchy as multi-active — that's a child hub + link.

### 5.2 Effectivity

An effectivity satellite tracks **when a link is active** (e.g. customer ↔ household membership). Columns: `start_date`, `end_date`, `is_active`. The link itself is insert-only and history-preserving; the effectivity sat layers temporal validity on top.

Effectivity is a **business vault** pattern, not raw — it requires interpretation (deciding when a relationship "ends").

### 5.3 When to use which

| Need | Use |
|---|---|
| Attribute history (descriptive context changes) | Standard satellite |
| Multiple concurrent values per attribute | Multi-active satellite |
| Relationship temporal validity | Effectivity satellite (on the link, in business vault) |
| Snapshots of state at regular intervals | PIT (business vault) |
| Multi-hop join precomputation | Bridge (business vault) |

---

## 6. Governance

### 6.1 Ownership

| Layer | Owner | Why |
|---|---|---|
| Stage | source-owning spoke | Source semantics live there |
| Raw vault | platform / data team | Cross-spoke integration |
| Business vault | data team + domain SMEs | Rules require domain knowledge |
| Information marts | consumer team | The consumer knows their access patterns |

### 6.2 Change management

- **Adding a hub, link, sat, or attribute:** non-breaking. Roll forward. No coordinated cutover.
- **Renaming a column:** breaking. Treat as expand/contract: add new column, dual-load, deprecate old, drop.
- **Changing the hash algorithm or separator:** breaking and rare. Requires a vault rebuild. Treat as a project, not a migration. Anchored by an ADR.
- **Source system changes:** stage absorbs the change. Raw vault stays stable. New columns become new sat attributes (and a new sat row when hash diff changes).

### 6.3 Lineage and documentation

The lineage doc generator (`tools/data-vault/lineage-doc.mjs`) emits Mermaid + Markdown from the model spec. Every PR that touches the vault must regenerate lineage docs. CI fails on drift (same pattern as `agents-glossary`).

### 6.4 Testing

- **Schema tests** (dbt): not_null on `_hk` and `load_date`; uniqueness on `(parent_hk, load_date)` for standard sats.
- **Hash test vectors** (`tools/data-vault/hash.test.mjs`): verify all dialects compute the same hash for the same input.
- **Idempotency tests:** rerun a load with the same input; assert zero new rows.
- **Round-trip tests:** raw vault → business vault → mart → assert sample known values.

### 6.5 Security

- Raw vault is **read-only** to all consumers except the loader role. No `UPDATE`, no `DELETE` ever.
- PII handling: sensitive attributes go in **separate satellites** so they can be ACL'd and aged out independently (e.g. `sat_customer_crm_pii` with row-level security).
- Right-to-be-forgotten: implemented as a **business vault tombstone link** that suppresses the entity from all downstream marts. The raw vault rows remain (compliance trail) but are no longer reachable from any mart.

---

## 7. Tooling

### 7.1 Reference loader: dbt + Datavault4dbt

dbt + Datavault4dbt is the recommended loader because:

- Macro-driven (`datavault4dbt.hub`, `.link`, `.sat`) — every loader is generated, not hand-written.
- Multi-dialect (Snowflake, Postgres, BigQuery, Databricks, Exasol).
- Idempotent and incremental out of the box.
- Plays well with dbt's testing and docs ecosystem.

But the methodology is loader-agnostic. The model spec (see [`tools/data-vault/model.schema.json`](../../tools/data-vault/model.schema.json)) is the single source of truth; the model generator emits dbt stubs *and* plain-DDL for shops not on dbt.

### 7.2 Toolkit overview

| Tool | Role |
|---|---|
| `tools/data-vault/model-generator.mjs` | YAML/JSON spec → DDL + dbt model stubs |
| `tools/data-vault/hash.mjs` + `hash.py` | Canonical hash key & hash diff implementations |
| `tools/data-vault/lineage-doc.mjs` | Spec → Mermaid + Markdown lineage docs |
| `tools/data-vault/adr-scaffold.mjs` | Pre-filled DV ADR template |

See [`tools/data-vault/README.md`](../../tools/data-vault/README.md).

### 7.3 The 3-agent team

See agent files for full role descriptions:

- [`data-vault-architect`](../../.claude/agents/categories/05-data-ai/data-vault-architect.md) — strategy, raw/business split, governance.
- [`data-vault-modeler`](../../.claude/agents/categories/05-data-ai/data-vault-modeler.md) — logical model design.
- [`data-vault-engineer`](../../.claude/agents/categories/05-data-ai/data-vault-engineer.md) — build, load, serve.

Routing rule of thumb: **architect decides "should we model this and how does it fit"; modeler decides "what shape — hub, link, sat, multi-active, effectivity"; engineer decides "how to load, test, and serve."**

---

## 8. Adoption roadmap

### Phase 0 — Foundations (this PR)

- ✅ Strategy doc (this file)
- ✅ Patterns doc
- ✅ Glossary
- ✅ ADR-026 anchor
- ✅ 3 agents
- ✅ 4 tools
- ✅ Routing wired in CLAUDE.md

### Phase 1 — First raw vault (next 1–2 PIs)

- Pick a single source with stable business keys (recommend: `crm.customer`).
- Author its model spec.
- Generate DDL + dbt stubs.
- Wire one staging loader.
- Ship one hub, two satellites, one link.
- Build one star-schema mart over it.
- Measure: load latency, idempotency, query latency.

### Phase 2 — Integration (PIs 2–4)

- Add a second source for the same entity (e.g. `billing.customer`).
- Build a same-as link in the business vault.
- Verify hash strategy across sources.
- Add PIT for one hot hub.

### Phase 3 — Real-time + graph (PIs 4–6)

- Stream a high-volume source (events) into raw vault.
- Late-arriving-key pattern in production.
- Graph projection of one link cluster onto ArcadeDB.

### Phase 4 — Mature platform (ongoing)

- DV in every analytics-bearing spoke.
- Mart catalog in [docs/data-vault/](.) curated by domain.
- Cost model per layer (stage / raw / business / mart) tracked through `finops-engineer`.

### Out of scope (for now)

- Vendor DV tools (WhereScape, Vaultspeed, BimlFlex, Erwin DV). Re-evaluate at Phase 4 if macro maintenance becomes the bottleneck.
- Active Data Vault (an emerging variant). Watch but don't adopt.

---

## 9. Anti-patterns to avoid

| Anti-pattern | Why it's bad | Do this instead |
|---|---|---|
| Editing the raw vault to "fix" data | Breaks insert-only contract; destroys audit trail | Fix it in business vault as a corrective satellite |
| Sequence keys instead of hash keys | Forces serial load; breaks cross-source idempotency | Always hash keys |
| MD5 hashes | Collision risk at large scale; weaker hash | SHA-256 only |
| One huge satellite with all attributes | Forces full-row rewrite on any change; hides PII | Split by source and by classification (PII, behavioral, transactional) |
| Multi-active when it's actually a child hub | Hides a real entity behind a flag | Hub + link |
| Skipping the business vault and going stage → mart | Loses integration layer; couples consumers to source shape | Always raw → (optional business) → mart |
| Materializing everything in business vault | Expensive and brittle | Virtualize by default, materialize only on SLA pressure |
| Hand-written loaders | Inconsistent, brittle, no test coverage | Macro-driven (dbt + Datavault4dbt or equivalent) |
| Mart writes back to raw | Inverts the dependency; impossible to rebuild | Marts are always downstream and disposable |

---

## 10. References

- Linstedt, D. & Olschimke, M. *Building a Scalable Data Warehouse with Data Vault 2.0*, 2nd ed.
- [Datavault4dbt](https://github.com/ScalefreeCOM/datavault4dbt) — Scalefree's open-source dbt package.
- [AutomateDV / dbtvault](https://automate-dv.com/) — alternative dbt package (formerly dbtvault).
- DV 2.1 supplement: Linstedt's published updates on streaming and managed self-service BI.
- AgentArmy: [`ARC-ADR-009 — Canonical Data Model (Arrow)`](../decisions/ARC-ADR-009-canonical-data-model-arrow.md), [`ARC-ADR-022 — Event Bus Bridges`](../decisions/ARC-ADR-022-event-bus-bridges.md).
