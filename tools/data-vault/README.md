# `tools/data-vault/` — Data Vault 2.1 toolkit

Strategy and patterns live in [`docs/data-vault/`](../../docs/data-vault/). This directory holds the executables.

| File | Purpose |
|---|---|
| `model-generator.mjs` | YAML/JSON model spec → DDL + dbt model stubs (Datavault4dbt-compatible) |
| `hash.mjs` + `hash.py` | Canonical SHA-256 hash-key & hash-diff library (Node + Python, bit-identical) |
| `hash.vectors.json` | Shared test vectors — both implementations must produce these exact hashes |
| `lineage-doc.mjs` | Model spec → Mermaid ER + flow diagrams + Markdown lineage docs |
| `adr-scaffold.mjs` | Pre-fills a DV-2.1-flavored ADR (`ARC-ADR-NNN-…`) under `docs/decisions/` |
| `yaml-mini.mjs` | Tiny zero-dep YAML parser for the spec subset (used by the generators) |
| `model.schema.json` | JSON Schema for the model spec |
| `examples/sample-model.yaml` | Reference spec; used by self-tests |

All tools are zero-dep, Node 22+, run from the repo root.

## Quickstart

```bash
# 1. Author or copy a model spec
cp tools/data-vault/examples/sample-model.yaml my-vault/model.yaml
$EDITOR my-vault/model.yaml

# 2. Validate
node tools/data-vault/model-generator.mjs --spec my-vault/model.yaml --validate

# 3. Generate dbt stubs + DDL for all dialects
node tools/data-vault/model-generator.mjs --spec my-vault/model.yaml \
    --out my-vault/build --target all

# 4. Generate lineage docs (commit these — CI checks for drift)
node tools/data-vault/lineage-doc.mjs --spec my-vault/model.yaml \
    --out docs/data-vault/lineage

# 5. Verify hash library on your dialect
node   tools/data-vault/hash.mjs --hub customer_id --value C-12345
python tools/data-vault/hash.py  --hub customer_id --value C-12345
# both must print the same digest
```

## `model-generator.mjs`

```
--spec <file>         path to .yaml / .yml / .json spec
--validate            structural validation only, no output
--out <dir>           output directory
--target <t>          dbt | ddl-snowflake | ddl-postgres | ddl-bigquery | ddl-databricks | all
                      (default: dbt)
```

Validation enforces:
- Snake-case names; hubs match `^hub_`, links `^lnk_`, sats `^(sat|eff_sat)_`, refs `^ref_`
- Link hubs all exist
- Satellite parents (hub or link) all exist
- Effectivity satellites hang off a link, not a hub
- Required fields: `model.name`, `model.dialect`, `model.version`; `hub.business_keys`, `hub.record_source`; `sat.attributes`

Generated `dbt/` tree:
```
dbt/
├── dbt_project.yml                 # skeleton; merge into your existing project
├── models/
│   ├── _schema.yml                 # not_null / unique / parent_hk tests
│   ├── staging/stg_<entity>.sql    # Datavault4dbt stage stubs
│   └── raw_vault/
│       ├── hubs/         hub_<entity>.sql
│       ├── links/        lnk_<from>_<to>.sql
│       ├── satellites/   sat_<parent>_<source>.sql
│       └── references/   ref_<entity>.sql
```

Generated `ddl/<dialect>/<model>.sql` is plain DDL for shops not on dbt. Dialect type mapping:

| Logical | snowflake | postgres | bigquery | databricks |
|---|---|---|---|---|
| hash key | `BINARY(32)` | `BYTEA` | `BYTES` | `BINARY` |
| timestamp | `TIMESTAMP_NTZ` | `TIMESTAMP` | `TIMESTAMP` | `TIMESTAMP` |
| string-unbounded | `STRING` | `TEXT` | `STRING` | `STRING` |

## `hash.mjs` / `hash.py`

DV 2.1 canonical hash. Algorithm:

1. **Business keys:** UTF-8 NFC normalize → trim → upper-case (unless case_sensitive) → join with `||` (null = `^^`) → SHA-256 → lowercase hex.
2. **Satellite hash diff:** UTF-8 NFC normalize attribute values → sort attributes alphabetically by name → join with `||` (null = `^^`) → SHA-256 → lowercase hex. **No trim, no case-fold** — descriptive content keeps its shape.

CLI:
```bash
# hub / single-key
node hash.mjs --hub customer_id --value C-12345

# link / composite (key=value pairs in declared order)
node hash.mjs --link customer_id=C-12345 order_id=O-99

# sat hash diff (alphabetical order applied automatically)
node hash.mjs --diff first_name=Ada last_name=Lovelace email=null

# vector tests
node hash.mjs --test
python hash.py --test

# recompute vectors after a deliberate algorithm change (requires ADR)
node hash.mjs --update-vectors && python hash.py --test
```

Both must pass `--test` on the same vectors file. Test vectors are the contract — change them only with an ADR (use `adr-scaffold.mjs --category hash-algo`).

## `lineage-doc.mjs`

```
--spec <file>     YAML or JSON model spec
--out <dir>       output directory (default: docs/data-vault/lineage)
```

Outputs three files:
- `lineage.md` — Markdown overview, hub/link/sat tables, embedded Mermaid
- `lineage.mmd` — Mermaid `erDiagram` source
- `lineage-flow.mmd` — Mermaid `flowchart LR` source-to-mart

Wire into CI per spoke:
```yaml
- run: node tools/data-vault/lineage-doc.mjs --spec my-vault/model.yaml --out docs/data-vault/lineage
- run: git diff --exit-code docs/data-vault/lineage/
```

## `adr-scaffold.mjs`

```
--topic "<short phrase>"           required
--category <key>                   placement | hash-algo | identity | streaming
                                   | materialization | mart-shape | pii | generic
--status <s>                       Proposed (default) | Accepted | Rejected
```

Each category pre-fills the right decision drivers and option block. Categories track [`docs/data-vault/strategy.md`](../../docs/data-vault/strategy.md) so the ADR doesn't drift from methodology.

Auto-numbering: scans `docs/decisions/` for the highest `ARC-ADR-NNN` and increments.

## Self-tests

```bash
node tools/data-vault/hash.mjs --test
python tools/data-vault/hash.py --test
node tools/data-vault/model-generator.mjs --spec tools/data-vault/examples/sample-model.yaml --validate
node tools/data-vault/model-generator.mjs --spec tools/data-vault/examples/sample-model.yaml --out /tmp/dv-test --target all
node tools/data-vault/lineage-doc.mjs --spec tools/data-vault/examples/sample-model.yaml --out /tmp/dv-lineage
```

All five must exit 0.

## Agent team

Use [`data-vault-architect`](../../.claude/agents/categories/05-data-ai/data-vault-architect.md), [`data-vault-modeler`](../../.claude/agents/categories/05-data-ai/data-vault-modeler.md), and [`data-vault-engineer`](../../.claude/agents/categories/05-data-ai/data-vault-engineer.md). Boundaries are MECE: architect decides *what and why*, modeler decides *shape*, engineer decides *load and serve*.
