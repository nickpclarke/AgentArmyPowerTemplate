# dlt Data Pipelines

dlt (data load tool) is a lightweight Python framework for building production-grade ETL/ELT pipelines.

## What is dlt?

dlt handles:
- **Source extraction** — APIs, files, databases, webhooks
- **Incremental loading** — Full refresh + delta loading
- **Schema inference** — Automatic type detection
- **Schema evolution** — Handle schema changes
- **Destination wiring** — DuckDB, BigQuery, Snowflake, Postgres, Parquet

## When to Use dlt

**Use dlt for:**
- Production data pipelines
- Incremental loading (only changed data)
- Multiple destinations
- Schema changes over time
- Data quality validation
- SEC EDGAR extraction

**Manual scripts for:**
- One-off exploration
- Fixed schema
- Single destination
- No future changes

## Architecture

```
Source → Extract → Transform → Load → Destination
  ↓         ↓          ↓         ↓         ↓
 API   Connector   Pipeline   Schema   DuckDB
  +       +          +         +      BigQuery
File      +        Python      +     Snowflake
  +       +          +         +      Postgres
 DB       +        SQL         +      Parquet
```

## Pipelines Directory

```
pipelines/
├── dlt_pipelines/
│   ├── sources/
│   │   ├── world_bank/
│   │   ├── census/
│   │   └── web_scraper/
│   ├── destinations.py
│   └── utils/
├── scripts/
│   ├── run_world_bank.py
│   ├── run_census.py
│   └── run_web_scraper.py
└── tests/
    └── test_*.py
```

## Delegating Pipeline Work

Create an issue with:
1. Source specification (API docs, auth)
2. Destination target (DuckDB, BigQuery, etc.)
3. Incremental loading strategy (full + delta?)
4. Schema requirements
5. Data quality checks

Assign `dlt-engineer`. They'll implement the source and wiring.

## Learn More

- **[dlt Sources](dlt-sources.md)** — Source connector patterns
- **[Incremental Loading](dlt-incremental.md)** — Delta strategies
- **[dlt Documentation](https://dlthub.com/docs)** — Official docs
