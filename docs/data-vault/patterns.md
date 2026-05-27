# Data Vault 2.1 — Implementation Patterns

Concrete idioms for the constructs called out in [strategy.md](strategy.md). Examples use ANSI-ish SQL; dialect-specific notes are inline. dbt examples use [Datavault4dbt](https://github.com/ScalefreeCOM/datavault4dbt) macros.

## 1. Hash key — hub

**Plain SQL (any dialect with `sha2`/`sha256` and `concat_ws`):**

```sql
-- stg_customer
SELECT
  lower(to_hex(sha256(upper(trim(customer_id))::bytea))) AS customer_hk,
  customer_id,
  first_name, last_name, email,
  current_timestamp AS load_date,
  'crm.salesforce' AS record_source
FROM raw.crm_customer;
```

**Datavault4dbt:**

```sql
-- models/staging/stg_customer.sql
{{ config(materialized='view') }}

{{ datavault4dbt.stage(
    include_source_columns=true,
    source_model='raw_crm_customer',
    hashed_columns={ 'customer_hk': 'customer_id' },
    derived_columns={
      'load_date':     'CURRENT_TIMESTAMP()',
      'record_source': "'crm.salesforce'"
    }
) }}
```

## 2. Hash key — link

```sql
SELECT
  lower(to_hex(sha256(
    concat_ws('||',
      coalesce(upper(trim(customer_id)), '^^'),
      coalesce(upper(trim(order_id)),    '^^')
    )::bytea
  ))) AS customer_order_hk,
  lower(to_hex(sha256(upper(trim(customer_id))::bytea))) AS customer_hk,
  lower(to_hex(sha256(upper(trim(order_id))::bytea)))    AS order_hk,
  current_timestamp AS load_date,
  'billing.invoice' AS record_source
FROM raw.invoice_line;
```

Each parent `_hk` is computed independently — the link's `_hk` is *not* derivable from the parents; it's a hash of the underlying business keys. This is so the link is collision-safe even when business keys collide across hubs.

## 3. Hash diff — satellite delta detection

Columns must be in a deterministic order. **Alphabetical by column name** is the convention enforced by the model generator.

```sql
lower(to_hex(sha256(concat_ws('||',
  coalesce(email,      '^^'),  -- alphabetical
  coalesce(first_name, '^^'),
  coalesce(last_name,  '^^'),
  coalesce(phone,      '^^')
)::bytea))) AS customer_crm_hd
```

## 4. Hub loader

Idempotent insert: a hub row is written once per unique business key.

```sql
INSERT INTO vault.hub_customer (customer_hk, customer_id, load_date, record_source)
SELECT s.customer_hk, s.customer_id, s.load_date, s.record_source
FROM staging.stg_customer s
LEFT JOIN vault.hub_customer h USING (customer_hk)
WHERE h.customer_hk IS NULL;
```

**Datavault4dbt:**

```sql
-- models/raw_vault/hubs/hub_customer.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.hub(
    hashkey='customer_hk',
    business_keys='customer_id',
    source_models=['stg_customer']
) }}
```

## 5. Link loader

Same pattern as hub — insert once per unique link hash key.

```sql
-- models/raw_vault/links/lnk_customer_order.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.link(
    link_hashkey='customer_order_hk',
    foreign_hashkeys=['customer_hk', 'order_hk'],
    source_models=['stg_invoice_line']
) }}
```

## 6. Satellite loader (standard)

Insert only when `hash_diff` differs from the most recent row for the same `parent_hk`.

```sql
-- models/raw_vault/satellites/sat_customer_crm.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.sat_v0(
    parent_hashkey='customer_hk',
    src_hashdiff='customer_crm_hd',
    src_payload=['first_name', 'last_name', 'email', 'phone'],
    source_model='stg_customer'
) }}
```

The macro handles the "compare hash diff to latest row" logic, so the load is naturally idempotent: rerunning yields zero new rows when the source hasn't changed.

## 7. Multi-active satellite

For 1:N attribute values at the same load date. The PK gains a `sub_sequence`.

```sql
-- models/raw_vault/satellites/sat_customer_emails_multi.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.ma_sat_v0(
    parent_hashkey='customer_hk',
    src_hashdiff='customer_emails_hd',
    src_payload=['email_address', 'email_type'],
    sub_sequence='email_seq',
    source_model='stg_customer_emails'
) }}
```

Use **only** when the source genuinely emits multiple rows per entity at the same point in time. A 1:N relationship between *entities* is a link + child hub, not multi-active.

## 8. Effectivity satellite (link)

Tracks when a link is active. **Business vault** construct.

```sql
-- models/business_vault/effectivity/eff_sat_customer_household_bv.sql
{{ config(materialized='incremental') }}

{{ datavault4dbt.eff_sat(
    parent_hashkey='customer_household_hk',
    src_driving_key='customer_hk',
    src_ldts='load_date',
    src_rsrc='record_source',
    source_model='lnk_customer_household'
) }}
```

The "driving key" is the side that *causes* the relationship to end (a customer leaves a household; the household persists). Picking the wrong driving key inverts the effectivity logic.

## 9. PIT (point-in-time) table

Materialized snapshots so consumers don't have to find "the latest satellite row as of T" at query time.

```sql
-- models/business_vault/pit/pit_customer.sql
{{ config(materialized='table') }}

{{ datavault4dbt.pit(
    hashkey='customer_hk',
    source_hub='hub_customer',
    source_satellites=[
      'sat_customer_crm',
      'sat_customer_billing',
      'sat_customer_preferences'
    ],
    snapshot_relation=ref('snapshot_dates_daily'),
    src_ldts='load_date'
) }}
```

Cadence: daily for most hubs, hourly for hot ones, real-time for none (defeats the purpose).

## 10. Bridge table

Denormalizes multi-hop link traversal. Always business vault, almost always materialized.

```sql
-- models/business_vault/bridge/bridge_customer_to_product_bv.sql
{{ config(materialized='table') }}

SELECT
  c.customer_hk,
  c.customer_id,
  o.order_id,
  p.product_hk,
  p.product_sku,
  oi.quantity,
  oi.line_total
FROM {{ ref('hub_customer') }} c
JOIN {{ ref('lnk_customer_order') }} lco USING (customer_hk)
JOIN {{ ref('hub_order') }} o USING (order_hk)
JOIN {{ ref('lnk_order_item') }} loi USING (order_hk)
JOIN {{ ref('sat_order_item') }} oi USING (order_item_hk)
JOIN {{ ref('hub_product') }} p USING (product_hk);
```

Only build a bridge for traversal paths that breach query SLA. Don't preemptively bridge every two-hop path.

## 11. Same-as link (identity resolution)

When two hubs in raw vault represent the same real-world entity (CRM customer + billing customer):

```sql
-- models/business_vault/sas_links/sas_customer_bv.sql
{{ config(materialized='incremental') }}

WITH matched AS (
  SELECT
    lower(to_hex(sha256(concat_ws('||',
      coalesce(crm.customer_hk,     '^^'),
      coalesce(billing.customer_hk, '^^')
    )::bytea))) AS same_as_customer_hk,
    crm.customer_hk     AS crm_customer_hk,
    billing.customer_hk AS billing_customer_hk,
    current_timestamp   AS load_date,
    'identity-resolver' AS record_source
  FROM {{ ref('hub_customer_crm') }} crm
  INNER JOIN {{ ref('hub_customer_billing') }} billing
    ON normalize_email(crm.email) = normalize_email(billing.email)
)
SELECT * FROM matched
{% if is_incremental() %}
  WHERE same_as_customer_hk NOT IN (SELECT same_as_customer_hk FROM {{ this }})
{% endif %}
```

The match function (here: email normalization) is the **business rule** — that's why it's business vault.

## 12. Computed satellite

A satellite where the attributes are derived, not extracted.

```sql
-- models/business_vault/sats/sat_customer_metrics_bv.sql
{{ config(materialized='incremental') }}

WITH base AS (
  SELECT
    c.customer_hk,
    COUNT(DISTINCT o.order_hk)                 AS lifetime_order_count,
    SUM(oi.line_total)                         AS lifetime_value,
    MAX(o.order_date)                          AS most_recent_order_date,
    current_timestamp                          AS load_date,
    'business-rules.customer-metrics-v1'       AS record_source
  FROM {{ ref('hub_customer') }} c
  LEFT JOIN {{ ref('lnk_customer_order') }} lco USING (customer_hk)
  LEFT JOIN {{ ref('hub_order') }} o USING (order_hk)
  LEFT JOIN {{ ref('lnk_order_item') }} loi USING (order_hk)
  LEFT JOIN {{ ref('sat_order_item') }} oi USING (order_item_hk)
  GROUP BY c.customer_hk
)
SELECT
  *,
  lower(to_hex(sha256(concat_ws('||',
    coalesce(lifetime_order_count::text,  '^^'),
    coalesce(lifetime_value::text,        '^^'),
    coalesce(most_recent_order_date::text,'^^')
  )::bytea))) AS customer_metrics_hd
FROM base;
```

**Version the rule** in `record_source` (`customer-metrics-v1`). When the rule changes, increment to v2 — the old computed sat rows stay (audit trail), new rows reflect the new rule.

## 13. Streaming load (micro-batch)

Buffer events for N seconds, batch into staging, then run the standard loaders. Idempotency comes from hash keys + hash diffs — replaying events is safe.

```python
# pseudocode for a Kafka → stage → raw vault micro-batch consumer
async def micro_batch_loader(topic, batch_seconds=10):
    buf = []
    async for event in consume(topic):
        buf.append(event)
        if len(buf) >= 1000 or elapsed(buf[0].ts) > batch_seconds:
            await stage_batch(buf)   # writes to staging.stg_X with hash keys
            await run_raw_vault_loaders()   # dbt invoke / direct SQL
            buf.clear()
```

Late-arriving keys: a `ghost hub row` is inserted with `record_source='deferred'` so the link can land immediately; the real hub row replaces it when the parent event arrives (no actual replace — the hash key already matches, so the second insert deduplicates).

## 14. Information mart — star schema

A dimension from a hub + its sats:

```sql
-- models/marts/dim_customer.sql
{{ config(materialized='table') }}

SELECT
  c.customer_hk          AS customer_key,
  c.customer_id          AS natural_key,
  crm.first_name,
  crm.last_name,
  crm.email,
  bill.billing_address,
  bill.payment_method,
  metrics.lifetime_value,
  metrics.lifetime_order_count
FROM {{ ref('hub_customer') }} c
LEFT JOIN {{ ref('sat_customer_crm') }} crm        ON c.customer_hk = crm.customer_hk
LEFT JOIN {{ ref('sat_customer_billing') }} bill   ON c.customer_hk = bill.customer_hk
LEFT JOIN {{ ref('sat_customer_metrics_bv') }} metrics ON c.customer_hk = metrics.customer_hk
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY c.customer_hk
  ORDER BY GREATEST(crm.load_date, bill.load_date, metrics.load_date) DESC
) = 1;
```

(Use `QUALIFY` on Snowflake/BigQuery/Databricks; on Postgres use a subquery with `DISTINCT ON`.)

A fact from a link + its sats:

```sql
-- models/marts/fct_order.sql
SELECT
  loi.customer_order_hk  AS order_key,
  c.customer_hk          AS customer_key,
  o.order_hk             AS order_pk,
  o.order_date           AS order_date_key,
  oi.line_total          AS revenue,
  oi.quantity            AS units
FROM {{ ref('lnk_customer_order') }} lco
JOIN {{ ref('hub_customer') }} c USING (customer_hk)
JOIN {{ ref('hub_order') }} o USING (order_hk)
JOIN {{ ref('lnk_order_item') }} loi USING (order_hk)
JOIN {{ ref('sat_order_item') }} oi USING (order_item_hk);
```

## 15. Information mart — graph projection

Hubs → nodes, links → edges. See [ARC-ADR-016](../decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) for the reification rules.

```cypher
// ArcadeDB / Cypher projection from DV
CREATE VERTEX TYPE Customer IF NOT EXISTS;
CREATE VERTEX TYPE Order IF NOT EXISTS;
CREATE EDGE   TYPE PLACED IF NOT EXISTS;

INSERT INTO Customer FROM SELECT customer_hk AS id, ... FROM hub_customer;
INSERT INTO Order    FROM SELECT order_hk    AS id, ... FROM hub_order;

CREATE EDGE PLACED FROM (SELECT FROM Customer WHERE id = :customer_hk)
                    TO (SELECT FROM Order    WHERE id = :order_hk)
SET load_date = :load_date, record_source = :record_source;
```

The projection is **rebuildable** — if the graph schema needs to change, drop and reproject from the raw vault. The graph is a mart, not a source of truth.

## 16. Test patterns

**Schema tests (dbt):**

```yaml
# models/raw_vault/_schema.yml
version: 2
models:
  - name: hub_customer
    columns:
      - name: customer_hk
        tests: [not_null, unique]
      - name: customer_id
        tests: [not_null, unique]
      - name: load_date
        tests: [not_null]
      - name: record_source
        tests: [not_null]
  - name: sat_customer_crm
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [customer_hk, load_date]
    columns:
      - name: customer_hk
        tests: [not_null]
      - name: customer_crm_hd
        tests: [not_null]
```

**Hash test vectors:** see `tools/data-vault/hash.test.mjs` and `hash.test.py`. Same vectors must pass in both languages.

**Idempotency assertion:**

```sql
-- macro: assert_idempotent
{% macro assert_idempotent(model_name) %}
  WITH before AS (SELECT COUNT(*) AS n FROM {{ ref(model_name) }})
  ... -- run loader
  AFTER AS (SELECT COUNT(*) AS n FROM {{ ref(model_name) }})
  SELECT CASE WHEN before.n != after.n
              THEN error('non-idempotent: ' || (after.n - before.n) || ' new rows')
         END
{% endmacro %}
```
