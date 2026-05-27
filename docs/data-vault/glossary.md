# Data Vault 2.1 — Glossary

Definitions for terms used in [strategy.md](strategy.md) and [patterns.md](patterns.md). Where DV 2.1 changed or clarified a 2.0 definition, the change is called out.

## Layers

**Stage** — Source-shaped landing tables with audit and hash columns added. Not part of the vault proper; thrown away on reload.

**Raw Vault** — Insert-only, schema-on-write integration layer. Hubs, links, satellites, references. No business rules.

**Business Vault** — Insert-only derivation layer. Same construct types as raw, plus PIT and bridge. Where business rules live.

**Information Mart** — Consumption layer. Star, snowflake, OBT, graph. Disposable; rebuilt from vault.

## Constructs

**Hub** — A unique business entity. One row per natural business key. The integration anchor for a concept (e.g. `hub_customer`).

**Link** — A relationship between two or more hubs. Modeled as its own table so that the relationship has its own history.

**Satellite (Sat)** — Descriptive context for a hub or link, with history. Multiple sats per parent is normal — split by source and by sensitivity.

**Reference (Ref)** — Code lookups (country code, currency, status). Either a flat `ref_*` table or a thin hub + sat for ones that need history.

**Multi-Active Satellite (MAS)** — A satellite with multiple active rows per parent at the same load date. Use only for genuine 1:N values, not for hierarchies.

**Effectivity Satellite (Eff-Sat)** — A satellite that tracks *when a link is active*, with `start_date`, `end_date`, `is_active`. Business vault construct.

**Same-As Link (SAS Link)** — A link that unifies entities across sources after identity resolution. Business vault construct.

**PIT (Point-in-Time)** — A materialized snapshot per hub + load_date giving the latest sat row pointers at each snapshot. Business vault construct. Cuts query cost when reconstructing entity state at time T.

**Bridge** — A denormalized projection of a multi-hop link path, for query performance. Business vault construct.

## Keys and audit

**Business Key (BK)** — The natural identifier of a business concept (customer ID, order number, ISBN). Sometimes composite.

**Hash Key (HK)** — A SHA-256 hash of the canonicalized business key. Replaces sequence surrogate keys. Columns named `<entity>_hk`. Enables parallel load and cross-platform consistency.

**Hash Diff (HD)** — A SHA-256 hash of the concatenated descriptive attributes (alphabetical order) on a satellite, used for delta detection. Columns named `<sat>_hd`.

**Load Date (LDTS)** — UTC timestamp of when the row entered the warehouse. Microsecond precision. Mandatory on every vault row.

**Record Source (RSRC)** — Opaque string identifying the source (e.g. `crm.salesforce.contact`, `business-rules.customer-metrics-v1`). Mandatory on every vault row.

**Ghost Hub Row** — A placeholder hub row inserted with `record_source='deferred'` when a link references a business key whose parent event hasn't arrived yet. Replaced (by deduplication on hash key) when the real event lands.

## Hashing

**SHA-256** — The mandated DV 2.1 hash algorithm. Hex-encoded, lowercase, 64 chars. MD5 is forbidden (collision risk at warehouse scale).

**Canonical Ordering** — The deterministic rule for concatenating attributes before hashing. For hash keys: business-key order as declared in the model. For hash diffs: alphabetical by column name.

**Null Sentinel** — The literal string used in place of NULL during hashing. Default `^^`. Critical because NULL in a business key is a meaningful value.

**Unicode NFC Normalization** — Canonical Composition form. Run on every string before hashing so `é` (one code point) and `e + ́` (two code points) hash identically.

## Load mechanics

**Insert-Only** — The vault never updates or deletes. New facts arrive as new rows. The cornerstone of auditability.

**Idempotent Load** — Rerunning the same load produces zero new rows. Achieved through hash-key uniqueness and hash-diff comparison.

**Parallel Load** — All hubs can load in parallel; all links and sats can load in parallel after hubs. The only ordering constraint.

**Late-Arriving Key** — A link references a hub whose row hasn't been loaded yet. Solved by ghost hubs (DV 2.1 first-class pattern).

**Micro-Batch** — A streaming load shape where events are buffered for N seconds (or N events) and then batch-loaded. DV 2.1's preferred streaming pattern.

## What changed in 2.1 vs 2.0

| Term | 2.0 | 2.1 |
|---|---|---|
| Real-time load | "Possible but use carefully" | First-class with explicit micro-batch and continuous patterns; ghost-hub pattern formalized |
| NoSQL / graph | Out of scope | In scope as a mart projection target |
| Self-service BI | Implicit | Information mart layer formalized with star / snowflake / OBT / graph projections and virtualize-by-default rule |
| Business vault patterns | "Use as needed" | Formal catalog: same-as links, computed sats, PIT, bridge; materialization decision tree |
| PIT/Bridge classification | Often called "query assistance" | Explicitly business vault constructs |
| Hash algorithm | MD5 acceptable | SHA-256 mandated for new vaults |
| Tool model | ETL-tool vendor implied | dbt / ELT / macro-driven assumed |

## Adjacent concepts (often confused)

**Anchor Modeling** — A different methodology, not DV. Similar goals (integration, history) but different shape (no hubs/links distinction, attribute-per-table).

**Activity Schema** — A single-table event-log warehouse pattern. Complementary to DV (can be a mart), not a replacement.

**One Big Table (OBT)** — A wide denormalized mart shape. A *projection from* DV, not an alternative to DV.

**Lakehouse Medallion (Bronze/Silver/Gold)** — A storage layering convention from Databricks. Roughly: bronze ≈ stage, silver ≈ raw vault, gold ≈ marts. The DV vocabulary is more precise about *what's in each layer and why*.

**SCD Type 2** — A dimensional pattern for tracking history in a star schema. The raw vault's satellite *is* a generalized SCD2; marts built from the vault may flatten it back into SCD2 dims if BI tools expect them.

**Kimball Bus Matrix** — A planning artifact for star schema design. Useful as an *input* to DV modeling (it identifies the conformed dimensions ≈ hubs) but doesn't replace DV's integration role.
