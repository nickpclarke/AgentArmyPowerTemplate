# ArcadeDB Cockpit Backend Contract

This contract describes the backend capabilities the cockpit should eventually consume. The current extension ships a dependency-free local Node proxy, but these endpoints are the stable shape to preserve if the proof moves into `platform/backend-core` or a dedicated service.

## Design Principles

- Keep browser clients credential-free. ArcadeDB credentials stay server-side.
- Prefer mounted runtime secrets with `ARCADEDB_PASSWORD_FILE`; accept `ARCADEDB_PASSWORD` only from ignored local files or runtime secret injection.
- Prefer read-only navigation endpoints and make mutation opt-in.
- Expose graph, document, vector, and instrumentation capabilities as product concepts, not raw database plumbing.
- Keep query-language flexibility behind backend policy: ArcadeDB supports SQL plus graph-oriented languages through the HTTP command endpoint, but the cockpit should not need to know which language each backend capability uses.

## Recommended Backend Packages

Use these only when the backend graduates beyond the current no-install proxy:

| Need | Package / interface | Why |
|---|---|---|
| No-driver baseline | built-in `fetch` or FastAPI `httpx` | ArcadeDB HTTP/JSON API works from any language and exposes command/query endpoints. |
| SQL-heavy backend paths | `pg` / PostgreSQL wire protocol | ArcadeDB documents PostgreSQL wire compatibility for stacks that already speak SQL through a standard driver. |
| Graph-driver ergonomics | `neo4j-driver` / BOLT | ArcadeDB documents Neo4j BOLT compatibility, useful when graph traversal tooling expects a Neo4j-like driver. |
| Backend API contract | FastAPI + Pydantic or OpenAPI-first TypeScript | The Claude backend already uses FastAPI and Pydantic; keep generated client types stable for the cockpit. |
| Runtime validation | Zod (TypeScript) or Pydantic (Python) | Validate query requests, graph snapshots, and metric payloads at the service boundary. |

## Capability Endpoints

### `GET /api/v1/cockpit/health`

Returns ArcadeDB readiness and backend instrumentation health.

```json
{
  "status": "ok",
  "arcadedb": {
    "ready": true,
    "url": "http://arcadedb:2480",
    "databases": ["knowledge"],
    "latency_ms": 31
  },
  "capabilities": {
    "read_only_queries": true,
    "mutations": false,
    "graph_traversal": true,
    "vector_search": true
  }
}
```

### `GET /api/v1/cockpit/schema?db=knowledge`

Returns type inventory, counts, fields, indexes, and sample records.

```json
{
  "database": "knowledge",
  "types": [
    {
      "name": "Chunk",
      "kind": "document",
      "count": 128,
      "fields": ["content", "source", "source_id", "kind", "embedding"],
      "indexes": [{ "field": "embedding", "type": "LSM_VECTOR" }]
    }
  ]
}
```

### `GET /api/v1/cockpit/graph?db=knowledge&limit=250`

Returns a cockpit-ready graph snapshot. The backend may compose this from `SELECT`, `MATCH`, or `TRAVERSE`.

```json
{
  "database": "knowledge",
  "nodes": [
    { "id": "db:knowledge", "label": "knowledge", "type": "database", "meta": {} }
  ],
  "edges": [
    { "from": "db:knowledge", "to": "type:Chunk", "type": "contains", "weight": 0.7 }
  ],
  "stats": {
    "records": 140,
    "edges": 212,
    "types": 3
  }
}
```

### `POST /api/v1/cockpit/query`

Runs a policy-checked query. Default policy should allow read-only statements only.

```json
{
  "db": "knowledge",
  "language": "sql",
  "query": "SELECT FROM Chunk LIMIT 10",
  "params": {},
  "mode": "read"
}
```

Response:

```json
{
  "rows": [],
  "elapsed_ms": 18,
  "read_only": true,
  "warnings": []
}
```

### `POST /api/v1/cockpit/traverse`

Navigates from a record ID with depth, direction, and edge/type constraints. Backend can implement this with ArcadeDB `TRAVERSE`, `MATCH`, or Cypher depending on the model.

```json
{
  "db": "knowledge",
  "start": "#12:0",
  "direction": "both",
  "max_depth": 2,
  "limit": 100
}
```

### `POST /api/v1/cockpit/vector-neighbors`

Returns vector-neighbor context for an existing record or supplied embedding. This should wrap ArcadeDB vector index capabilities so the cockpit can show similarity constellations without owning embedding logic.

```json
{
  "db": "knowledge",
  "type": "Chunk",
  "field": "embedding",
  "record_id": "#14:2",
  "k": 12
}
```

### `GET /api/v1/cockpit/metrics`

Returns recent command timings, error counts, sampled query history, and database-size signals.

```json
{
  "average_command_ms": 22,
  "recent_commands": [
    { "label": "graph-snapshot", "elapsed_ms": 19, "rows": 120, "at": "2026-05-24T02:20:00Z" }
  ],
  "errors": []
}
```

## Backend Gates

- Mutating SQL requires an explicit environment flag and should be logged.
- Raw ArcadeDB credentials never appear in frontend responses.
- Diagnostics and cockpit logs may report whether credentials came from `ARCADEDB_PASSWORD_FILE` or `ARCADEDB_PASSWORD`, but never the value.
- Query endpoint rejects multi-statement payloads unless a trusted admin mode is enabled.
- Traversal and graph endpoints enforce limits to avoid runaway graph expansion.
- Vector endpoints never require the browser to send provider keys.

## Current Extension Mapping

| Contract endpoint | Current local proxy |
|---|---|
| `GET /api/v1/cockpit/health` | `GET /api/health` |
| `GET /api/v1/cockpit/schema` | `GET /api/schema` |
| `GET /api/v1/cockpit/graph` | `GET /api/graph` |
| `POST /api/v1/cockpit/query` | `POST /api/query` |
| `GET /api/v1/cockpit/metrics` | `GET /api/telemetry` |

The extension intentionally uses shorter local paths while the contract remains the future backend target.

## References

- ArcadeDB HTTP/JSON API: https://docs.arcadedb.com/arcadedb/reference/http-api/http.html
- ArcadeDB languages and drivers: https://docs.arcadedb.com/arcadedb/languages-drivers.html
- ArcadeDB PostgreSQL protocol plugin: https://docs.arcadedb.com/arcadedb/how-to/connectivity/postgres.html
- ArcadeDB Neo4j BOLT protocol: https://docs.arcadedb.com/arcadedb/how-to/connectivity/bolt.html
- ArcadeDB SQL overview: https://docs.arcadedb.com/arcadedb/reference/sql/sql-introduction.html
