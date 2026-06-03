# Incremental Loading in dlt

Strategy for efficiently loading only new/changed data.

## Why Incremental?

| Approach | Speed | Cost | Latency |
|----------|-------|------|---------|
| **Full Reload** | Slow | High | High |
| **Incremental** | Fast | Low | Low |

Incremental loading queries only new/changed records since last run.

## Common Strategies

### 1. Timestamp (Last Modified)

```python
@dlt.resource
def fetch_records(api_key: str, state):
    last_run = dlt.current.source_state()
    start_time = last_run.get("last_timestamp", "2024-01-01")
    
    records = api.get_records(
        modified_after=start_time
    )
    
    for record in records:
        yield record
        state["last_timestamp"] = record["modified_at"]
```

### 2. Cursor (ID-based)

```python
@dlt.resource
def fetch_records(api_key: str):
    state = dlt.current.source_state()
    last_id = state.get("last_id", 0)
    
    records = api.get_records(after_id=last_id)
    
    for record in records:
        yield record
        state["last_id"] = record["id"]
```

### 3. Change Data Capture (CDC)

For databases with WAL/CDC:

```python
@dlt.resource
def fetch_changes(state):
    lsn = state.get("lsn", "0/0")
    changes = db.get_wal_changes(from_lsn=lsn)
    
    for change in changes:
        yield change
        state["lsn"] = change["lsn"]
```

## State Management

dlt tracks state per source:

```python
# Initialize state
state = {}

# Update during extraction
state["last_run"] = datetime.now()
state["last_id"] = max_id

# dlt persists between runs
```

## Testing Incremental

```python
def test_incremental_loading():
    # First run
    state = {}
    records1 = list(fetch_records(state=state))
    assert len(records1) > 0
    
    # Second run (should get only new)
    records2 = list(fetch_records(state=state))
    # Verify only new records loaded
```

## Related

- **[dlt Pipelines](dlt-pipelines.md)**
- **[dlt Sources](dlt-sources.md)**
