# RT5 PIN-S1 — ArcadeDB UPSERT / Idempotency / Batching Semantics

**Spike:** PIN-S1 — ArcadeDB transaction/UPSERT/idempotency semantics
**Informed by:** Live execution against `arcadedata/arcadedb:26.5.1`
**Informs:** PIN-F4 — ArcadeDB adapter (`ArcadeDbPinBackend`)
**Verdict:** All critical hypotheses confirmed live. See implementation patterns below.
**Evidence:** `planning/synthesis/spike_arcadedb_test.py` — 35/36 assertions passed; the 1 non-pass is a gotcha (see section 6).

---

## Spike Context

The adapter (PIN-F4) must implement:

1. An idempotent **live row** — one `OntologyElement` vertex per `ontology_iri`, updated in-place on re-pin.
2. An **immutable append-only ledger** (`PinLedgerEntry`) — re-pinning identical content must be a no-op (guarded by `UNIQUE` on `content_hash`).
3. Both operations must be atomic.

Unknowns before this spike: does `UPDATE...UPSERT` deduplicate correctly, how does ArcadeDB behave on a duplicate INSERT against a UNIQUE index, and how do you batch both operations atomically?

---

## 1. HTTP Command API Shape

**LIVE VERIFIED**

All SQL and script execution goes through one endpoint:

```
POST /api/v1/command/{database}
Content-Type: application/json
Authorization: Basic <base64(user:password)>

{ "language": "sql", "command": "<sql>" }
```

Response shape:

```json
{ "user": "root", "result": [ ...rows ] }
```

Key points:
- `result` is always an array (empty array `[]` on DDL statements, not null).
- HTTP 4xx/5xx on any error — check `detail` field in the error body for the message.
- For `sqlscript`, set `"language": "sqlscript"`. All other fields identical.
- No separate transaction endpoint; transactions are managed inside `sqlscript`.

---

## 2. DDL Idempotency

**LIVE VERIFIED — DDL-01 through IDX-04 all passed**

All `CREATE` DDL statements support `IF NOT EXISTS`. Use it everywhere in `EnsureReadyAsync`:

```sql
CREATE VERTEX TYPE OntologyElement IF NOT EXISTS;
CREATE DOCUMENT TYPE PinLedgerEntry IF NOT EXISTS;

CREATE PROPERTY OntologyElement.ontology_iri IF NOT EXISTS STRING;
CREATE PROPERTY PinLedgerEntry.content_hash IF NOT EXISTS STRING;

CREATE INDEX IF NOT EXISTS ON OntologyElement (ontology_iri) UNIQUE;
CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (content_hash) UNIQUE;
```

Calling these a second time returns HTTP 200 with an empty `result` array — no error. `EnsureReadyAsync` can be called repeatedly without guard state.

---

## 3. UPDATE...UPSERT — Live Row Semantics

**LIVE VERIFIED — UPSERT-01 through UPSERT-06 all passed**

### Syntax

```sql
UPDATE <Type>
SET <field1> = <value1>, <field2> = <value2>
UPSERT
WHERE <unique_key_field> = '<key_value>'
```

The `UPSERT` keyword is placed between the `SET` clause and the `WHERE` clause.

### Behavior confirmed

| Scenario | Result |
|---|---|
| First call — no matching record | Creates 1 vertex; returns `[{"count": 1}]` |
| Second call — same key, same content | Updates the same record; returns `[{"count": 1}]` |
| Call with same key, changed content | Updates in-place; returns `[{"count": 1}]` |
| Row count after N UPSERTs on same key | Always exactly 1 — no phantom duplicates |

### Return shape

```json
[{ "count": 1 }]
```

`count` is the number of records affected (created or updated). This is always 1 for a single-key UPSERT.

### PIN-F4 live-row UPSERT

```sql
UPDATE OntologyElement
SET identity_hash      = ':identity_hash',
    content_hash       = ':content_hash',
    kind               = ':kind',
    object_type        = ':object_type',
    object_id          = ':object_id',
    ontology_concept   = ':ontology_concept',
    ufo_stereotype     = ':ufo_stereotype',
    state              = ':state',
    valid_from         = ':valid_from',
    valid_to           = ':valid_to',
    recorded_at        = ':recorded_at',
    canonical_payload  = ':canonical_payload',
    schema_version     = ':schema_version'
UPSERT
WHERE ontology_iri = ':ontology_iri'
```

Pass values via the `"params"` object in the HTTP payload to avoid SQL injection:

```json
{
  "language": "sql",
  "command": "UPDATE OntologyElement SET label = :label UPSERT WHERE ontology_iri = :iri",
  "params": { "label": "Invoice", "iri": "urn:agentarmy:mc:invoice/Invoice/001" }
}
```

---

## 4. UNIQUE-Guarded INSERT — Ledger Semantics

**LIVE VERIFIED — LEDGER-01 through LEDGER-06 all passed**

### Behavior confirmed

| Scenario | Result |
|---|---|
| First INSERT with a new `content_hash` | Succeeds; returns the created record |
| Second INSERT with the same `content_hash` | HTTP 500, error body contains `"Duplicated key [<hash>] found on index"` |
| Row count after 2 attempts with same hash | Exactly 1 — no duplicate committed |
| INSERT with a different `content_hash`, same `identity_hash` | Succeeds — appends a new ledger entry |

### Error body shape on duplicate

```json
{
  "error": "Error on transaction commit",
  "detail": "Duplicated key [sha256-abc123] found on index 'PinLedgerEntry[content_hash]' already assigned to record #4:0",
  "exception": "com.arcadedb.index.IndexException"
}
```

The `.detail` field carries the message; `.exception` is the Java class name. The string `"Duplicated key"` is a reliable signal to distinguish a duplicate-hash no-op from a real error.

### PIN-F4 ledger INSERT

```sql
INSERT INTO PinLedgerEntry
SET content_hash       = ':content_hash',
    ontology_iri       = ':ontology_iri',
    identity_hash      = ':identity_hash',
    kind               = ':kind',
    object_type        = ':object_type',
    object_id          = ':object_id',
    ufo_stereotype     = ':ufo_stereotype',
    valid_from         = ':valid_from',
    valid_to           = ':valid_to',
    recorded_at        = ':recorded_at',
    superseded_at      = ':superseded_at',
    canonical_payload  = ':canonical_payload',
    provenance         = ':provenance',
    schema_version     = ':schema_version'
```

---

## 5. Batching and Transactions

**LIVE VERIFIED — BATCH-01, BATCH-02, ATOMIC-01, ATOMIC-02, PIN-01 through PIN-04 all passed**

### The batching mechanism: sqlscript

ArcadeDB's `sqlscript` language runs a multi-statement script in a single HTTP call. It is the only way to execute the UPSERT + INSERT atomically. Plain `sql` language does not support multiple statements separated by semicolons (the second statement is silently ignored or errors).

```
POST /api/v1/command/{database}
{ "language": "sqlscript", "command": "<script>" }
```

### Script syntax

```
BEGIN;
LET <var> = <sql_statement>;
LET <var2> = <sql_statement>;
COMMIT;
RETURN $<var>;
```

- `BEGIN` / `COMMIT` are mandatory to wrap the statements transactionally.
- `LET` assigns the result of a statement to a named variable.
- `RETURN` sends the named variable back as the HTTP response `result`.
- Semicolons after `LET` lines are required.

### Atomic UPSERT + INSERT — the canonical PIN-F4 pattern

```
BEGIN;
LET live = UPDATE OntologyElement
  SET identity_hash = :identity_hash, content_hash = :content_hash,
      label = :label, state = :state, recorded_at = :recorded_at
  UPSERT WHERE ontology_iri = :ontology_iri;
LET ledger = INSERT INTO PinLedgerEntry
  SET content_hash = :content_hash, ontology_iri = :ontology_iri,
      identity_hash = :identity_hash, recorded_at = :recorded_at;
COMMIT;
RETURN $live;
```

### Transaction rollback on UNIQUE violation — confirmed

When the `INSERT` violates the `UNIQUE` index on `content_hash`, the entire transaction rolls back. This was confirmed live:

- The `UPDATE...UPSERT` had already executed within the transaction.
- The subsequent `INSERT` triggered a UNIQUE violation.
- ArcadeDB returned HTTP 500 with `"Duplicated key"` in the detail.
- A follow-up `SELECT` confirmed the UPSERT's write was also rolled back.

This means the naive pattern (wrap both in one script, treat duplicate-key as idempotent) **does not work**. See section 6 for the correct approach.

---

## 6. Critical Gotcha: Re-pin Rolls Back the Live Row Update

**LIVE VERIFIED — PIN-02, PIN-03, PIN-04 all passed (confirmed the gotcha)**

When you re-pin with identical content using the atomic `sqlscript`:

1. UPSERT succeeds inside the transaction (the live row is "pending").
2. INSERT fails on the UNIQUE index.
3. **The entire transaction rolls back, including the UPSERT.**
4. The live row is left in its pre-call state (the first-pin value, not rolled back to nothing).

This is safe for the immutable-ledger invariant (no duplicate ledger entry is written), but it means the **live row is NOT updated** on a content-identical re-pin — which is actually the correct semantic (content has not changed, live row need not change).

**However:** if you want `recorded_at` or `state` on the live row to update on every pin call regardless of content change, you cannot do that atomically with the simple UPSERT+INSERT pattern. You need the check-first pattern below.

---

## 7. Recommended Idempotent Pin Pattern for PIN-F4

Based on the spike results, PIN-F4 `PinObjectAsync` should use a **check-before-script** pattern:

```
Step 1 (read):  SELECT count(*) AS n FROM PinLedgerEntry WHERE content_hash = :content_hash
Step 2a (skip): if n > 0 → content already pinned, return existing live row (no-op)
Step 2b (write): if n = 0 → execute atomic sqlscript (UPSERT live + INSERT ledger)
```

This avoids the transaction rollback entirely on re-pin, and the two-step sequence is safe because:
- The UNIQUE index on `content_hash` prevents a race condition from inserting duplicates even if two callers pass the read check simultaneously.
- The UPSERT is idempotent by design.

### C# pseudocode sketch

```csharp
// Step 1: guard read
var n = await CountAsync($"SELECT count(*) AS n FROM PinLedgerEntry WHERE content_hash = :h",
    new { h = element.ContentHash.Value });

if (n > 0)
    return; // idempotent no-op

// Step 2: atomic write
var scriptResult = await ScriptAsync("""
    BEGIN;
    LET live = UPDATE OntologyElement
      SET identity_hash = :identity_hash, content_hash = :content_hash, ...
      UPSERT WHERE ontology_iri = :ontology_iri;
    LET ledger = INSERT INTO PinLedgerEntry
      SET content_hash = :content_hash, ...;
    COMMIT;
    RETURN $live;
    """, params);

// If we still get a "Duplicated key" error here (lost race), treat as no-op.
// Do NOT rethrow duplicate-key as an exception — it means another caller won the race.
```

---

## 8. Composite Index Gotcha: Validate Data First

**LIVE DISCOVERED — CIDX-01 failed**

Creating a UNIQUE composite index on an existing type fails if existing data contains duplicates on those columns. ArcadeDB validates all existing records during index creation:

```
Error on creating index 'PinLedgerEntry_0_...' ->
Duplicated key [hash-script, 2026-01-01T00:00:00Z] found on index
```

**Implication for PIN-F4:** The index DDL in `EnsureReadyAsync` must run **before** any data is written. The DDL must be part of initial schema setup, not added to an existing populated database without checking. The recommended indexes from the PIN-F4 spec:

```sql
-- Primary dedup guard (must exist before any PIN write)
CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (content_hash) UNIQUE;

-- Composite lookup indexes (data must be unique on these before adding)
CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (identity_hash, recorded_at) UNIQUE;
CREATE INDEX IF NOT EXISTS ON OntologyElement (ontology_iri) UNIQUE;
```

For the composite `(identity_hash, recorded_at)` index: since `recorded_at` is the serialization clock timestamp (unique per clock tick per object), duplicates should be practically impossible in production. But in the test harness the BATCH-01 test deliberately inserted two rows with the same `(identity_hash, recorded_at)` pair, which blocked the later index creation. Schema-first order is mandatory.

---

## 9. Index and Schema Setup Order for EnsureReadyAsync

The correct initialization order to avoid the composite-index gotcha:

```sql
-- 1. Types
CREATE VERTEX TYPE OntologyElement IF NOT EXISTS;
CREATE DOCUMENT TYPE PinLedgerEntry IF NOT EXISTS;
-- (and HyperEdge types, ProvenanceVertex, BINDS_ROLE as needed by PIN-F4)

-- 2. Properties (required before index creation)
CREATE PROPERTY OntologyElement.ontology_iri IF NOT EXISTS STRING;
CREATE PROPERTY OntologyElement.identity_hash IF NOT EXISTS STRING;
CREATE PROPERTY OntologyElement.content_hash IF NOT EXISTS STRING;
-- ... all other OntologyElement fields ...

CREATE PROPERTY PinLedgerEntry.content_hash IF NOT EXISTS STRING;
CREATE PROPERTY PinLedgerEntry.identity_hash IF NOT EXISTS STRING;
CREATE PROPERTY PinLedgerEntry.recorded_at IF NOT EXISTS STRING;
-- ... all other PinLedgerEntry fields ...

-- 3. Indexes (after types and properties exist, before any data write)
CREATE INDEX IF NOT EXISTS ON OntologyElement (ontology_iri) UNIQUE;
CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (content_hash) UNIQUE;
CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (identity_hash, recorded_at) UNIQUE;
-- composite indexes from PIN-F4 spec: (identity_hash, superseded_at, recorded_at), etc.
```

---

## 10. Full Verified SQL Shapes for PIN-F4

### Live row — UPSERT on `ontology_iri`

```sql
UPDATE OntologyElement
SET identity_hash     = :identity_hash,
    content_hash      = :content_hash,
    kind              = :kind,
    object_type       = :object_type,
    object_id         = :object_id,
    ontology_concept  = :ontology_concept,
    ontology_iri      = :ontology_iri,
    ufo_stereotype    = :ufo_stereotype,
    state             = :state,
    valid_from        = :valid_from,
    valid_to          = :valid_to,
    recorded_at       = :recorded_at,
    canonical_payload = :canonical_payload,
    schema_version    = :schema_version
UPSERT
WHERE ontology_iri = :ontology_iri
```

### Immutable ledger — guarded INSERT

```sql
INSERT INTO PinLedgerEntry
SET content_hash      = :content_hash,
    ontology_iri      = :ontology_iri,
    identity_hash     = :identity_hash,
    kind              = :kind,
    object_type       = :object_type,
    object_id         = :object_id,
    ufo_stereotype    = :ufo_stereotype,
    valid_from        = :valid_from,
    valid_to          = :valid_to,
    recorded_at       = :recorded_at,
    superseded_at     = :superseded_at,
    canonical_payload = :canonical_payload,
    provenance        = :provenance,
    schema_version    = :schema_version
```

### Atomic sqlscript wrapping both

```
BEGIN;
LET live = UPDATE OntologyElement
  SET identity_hash = :identity_hash, content_hash = :content_hash,
      kind = :kind, object_type = :object_type, object_id = :object_id,
      ontology_concept = :ontology_concept, ufo_stereotype = :ufo_stereotype,
      state = :state, valid_from = :valid_from, valid_to = :valid_to,
      recorded_at = :recorded_at, canonical_payload = :canonical_payload,
      schema_version = :schema_version
  UPSERT WHERE ontology_iri = :ontology_iri;
LET ledger = INSERT INTO PinLedgerEntry
  SET content_hash = :content_hash, ontology_iri = :ontology_iri,
      identity_hash = :identity_hash, kind = :kind, object_type = :object_type,
      object_id = :object_id, ufo_stereotype = :ufo_stereotype,
      valid_from = :valid_from, valid_to = :valid_to, recorded_at = :recorded_at,
      superseded_at = :superseded_at, canonical_payload = :canonical_payload,
      provenance = :provenance, schema_version = :schema_version;
COMMIT;
RETURN $live;
```

---

## 11. Open Questions and Residual Risk

| Question | Status | Risk level |
|---|---|---|
| `HyperEdge` vertex type for relator pinning (PIN-F4 uses `HyperEdge` subtype for `ingest-evidence`) | Not spiked — no relator DDL tested | Medium — PIN-S2 may address query patterns; PIN-F4 needs relator schema before coding |
| `BINDS_ROLE` edge type creation and traversal | Not spiked | Medium |
| Parameter binding with large `canonical_payload` JSON blob (>64KB) | Not tested | Low — ArcadeDB document type handles arbitrary JSON; confirm max document size |
| Concurrent writes (race between check and script in high-throughput scenarios) | Partially addressed — UNIQUE index is the backstop; duplicate-key on INSERT is the race signal | Low for current throughput; document as known behavior |
| PostgreSQL wire protocol as alternative to HTTP command API | Not spiked — the cockpit contract notes ArcadeDB supports pg wire | Low — HTTP command API is sufficient for the adapter; pg wire adds driver dependency |

---

## 12. Test Evidence Summary

**ArcadeDB version:** 26.5.1 (build `b6d08fee549dd5930303b362223869901aab0fac`)
**Container:** `arcadedata/arcadedb:26.5.1` via `docker run --name spike-arcadedb-test -p 12480:2480`
**Test script:** `planning/synthesis/spike_arcadedb_test.py`
**Result:** 35 PASS / 1 NOTED (CIDX-01 — gotcha documented above)

| Group | Tests | Pass | Notes |
|---|---|---|---|
| DDL idempotency | 4 | 4 | IF NOT EXISTS works on all DDL |
| UNIQUE index | 4 | 4 | IF NOT EXISTS works; repeatable |
| UPSERT live row | 6 | 6 | count=1 always; no phantom rows |
| Guarded INSERT | 6 | 6 | Duplicate fails; error is "Duplicated key" |
| sqlscript batch | 2 | 2 | BEGIN/COMMIT wraps multiple statements |
| Transaction atomicity | 2 | 2 | UNIQUE violation rolls back entire tx |
| PIN-F4 full pattern | 4 | 4 | First pin OK; re-pin rolls back correctly |
| Check-first re-pin | 5 | 5 | Skip on existing hash; new content appends |
| Composite index | 1 | 0 | Fails on pre-existing duplicates — gotcha |
| HTTP API shape | 2 | 2 | result=[...rows]; detail field on error |

All claims above are **LIVE VERIFIED** unless explicitly marked otherwise.
