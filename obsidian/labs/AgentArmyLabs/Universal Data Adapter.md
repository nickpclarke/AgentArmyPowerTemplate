---
tags: [platform, data, database, vision]
track: data
---
# Universal Data Adapter

Connection registry + capability-based connectors + dlt pipelines, to connect to many databases from one place (ArcadeDB first, BigQuery next).

- **Design:** ADR 0001 (backend-core PR #12) · Epic #13 (PI-1).
- **Adopt:** dlt · arcadedb-python · ADBC + sqlalchemy-bigquery; build the thin adapter.

> [!important] Convergence
> Its **CDM / schema vocabulary** should be the *same canonical model* as [[Middle-Core]] — connectors, connections, pipelines, and capabilities are modeled objects. See [[One Model, Many Projections]] and [[Model-Driven Platform]].

See also: [[Data & Database Science Track]].
