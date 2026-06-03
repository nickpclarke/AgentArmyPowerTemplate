# dlt Source Connectors

Building data extractors for dlt pipelines.

## Source Structure

```
source_name/
├── __init__.py
├── pipeline.py          # Extraction logic
├── schema.py            # Type hints
├── connector.py         # Source implementation
└── README.md            # Docs
```

## Creating a Source

### 1. Define Schema

```python
# schema.py
from typing import TypedDict

class Record(TypedDict):
    id: int
    name: str
    value: float
    timestamp: str
```

### 2. Implement Connector

```python
# connector.py
import dlt

@dlt.resource(
    name="records",
    write_disposition="replace"
)
def fetch_records(api_key: str):
    """Extract records from API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    # Make requests, yield records
    yield record_data
```

### 3. Create Pipeline

```python
# pipeline.py
import dlt

def run_pipeline(api_key: str, destination: str):
    pipeline = dlt.pipeline(
        pipeline_name="my_source",
        destination=destination,
        dataset_name="raw_data"
    )
    
    data = fetch_records(api_key)
    load_info = pipeline.run(data)
    return load_info
```

## Incremental Loading

See [dlt Incremental Loading](dlt-incremental.md) for state management and delta strategies.

## Testing

```python
# test_connector.py
import pytest
from connector import fetch_records

def test_fetch_records():
    records = list(fetch_records("test-key"))
    assert len(records) > 0
    assert "id" in records[0]
```

## Graph Sources

We provide specialized graph sources to handle node and edge extraction.

### Neo4j Graph Source
Extracts nodes and relationships using Cypher queries:
```python
from dlt_pipelines.sources.graph.neo4j import neo4j_source

source = neo4j_source(
    uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
)
```

### Postgres Graph Source
Extracts graph data from relational tables or custom SQL:
```python
from dlt_pipelines.sources.graph.postgres_graph import postgres_graph_source

source = postgres_graph_source(
    connection_string="postgresql://user:password@localhost:5432/dbname",
    nodes_table="users",
    edges_table="follows",
)
```

### Hugging Face Graph Source
Loads graph/network datasets from Hugging Face Hub:
```python
from dlt_pipelines.sources.graph.huggingface_graph import huggingface_graph_source

source = huggingface_graph_source(
    dataset_name="scitldr",
    source_column="source",
    target_column="target",
)
```

## Delegating Source Development

Create issue with:
- **Source Name** (e.g., "Stripe API connector")
- **API Documentation** (link to docs)
- **Authentication** (API key, OAuth, etc.)
- **Data Schema** (expected fields/types)
- **Incremental Loading** (full refresh or delta?)

Assign `dlt-engineer`. They'll implement and test.

## Related

- **[dlt Pipelines](dlt-pipelines.md)**
- **[Incremental Loading](dlt-incremental.md)**
