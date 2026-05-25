# PIN-S2 — Bitemporal Query Patterns for the RT5 Pinning Ledger

**Spike:** PIN-S2 — Bitemporal "pin/snapshot" query patterns
**Time-box:** half session
**Depends on:** PIN-F2 (`PinnedElement` shape), PIN-F3 (in-memory store), PIN-F4 (ArcadeDB adapter)
**Feeds back to:** PIN-F4 (index needs), PIN-F3 (`IPinStore` query contract)

---

## 1. Record Shape (canonical reference)

From PIN-F2, every pinned object produces a `PinnedElement` with these temporal fields:

| Field | Axis | Semantics |
|---|---|---|
| `valid_from` | Valid time — start | When the object's state became true in the world (ISO-8601 string, never null) |
| `valid_to` | Valid time — end | When the object's state ceased to be true (ISO-8601 string or `null` = open-ended / current) |
| `recorded_at` | Transaction time | When `PinObjectAsync` / `PinRelatorAsync` wrote this ledger row (injected clock, never null, never updated) |
| `superseded_at` | Transaction time — end | When a later pin superseded this row (`null` = still the current version for this identity) |
| `identity_hash` | Identity | Stable hash across payload changes — identifies "which object" across all versions |
| `content_hash` | Content | Changes with any payload or valid-time change — identifies "which exact version" |

**Null-semantics contract (edge cases):**
- `valid_to IS NULL` — the object's valid-time interval is open-ended (currently valid; no known expiry).
- `superseded_at IS NULL` — this row is the current ledger entry for its `identity_hash` (has not been superseded by a re-pin).
- Both nulls together = the live, current, open-ended state.
- A row can have `valid_to` set (known expiry in domain time) while still being the current transaction-time record (`superseded_at IS NULL`); this is not a contradiction — the object is current in the ledger but the domain validity window has closed.

---

## 2. Query Taxonomy

Three query families cover all retrieval needs:

| Family | Fixes | Returns | Use-case |
|---|---|---|---|
| **Valid-time as-of** | `valid_from <= :asOf AND (valid_to IS NULL OR valid_to > :asOf)` | Domain view at a business moment | "What did the world look like on date D?" |
| **Transaction-time as-of** | `recorded_at <= :asOfTx AND (superseded_at IS NULL OR superseded_at > :asOfTx)` | Ledger view as it was known at a system moment | "What did we know at the time of pin T?" |
| **Bitemporal combination** | Both axes simultaneously | Precise point-in-bitemporalspace | "What did we _record_ about date D, as we knew it at system time T?" |

The combination is the canonical "what was the graph state at pin X" query.

---

## 3. In-Memory Store Semantics (PIN-F3)

The `InMemoryPinBackend` holds a `List<PinnedElement>` (the ledger) and a `Dictionary<string, PinnedElement>` (live index keyed on `identity_hash`). All queries are LINQ over the ledger list.

### 3.1 Valid-time as-of ("world view at business moment D")

```csharp
// Parameter: asOf — the business/domain point in time (ISO-8601 string comparable as string sort)
IEnumerable<PinnedElement> QueryValidAsOf(IReadOnlyList<PinnedElement> ledger, string asOf) =>
    ledger.Where(e =>
        string.Compare(e.ValidFrom, asOf, StringComparison.Ordinal) <= 0
        && (e.ValidTo is null || string.Compare(e.ValidTo, asOf, StringComparison.Ordinal) > 0)
    );
// Note: ValidTo IS NULL = open-ended interval; always included when asOf >= ValidFrom.
// Note: Comparison is ISO-8601 lexicographic sort, which preserves temporal order for
//       zero-padded strings (yyyy-MM-ddTHH:mm:ssZ). Callers must normalise to UTC before passing.
```

### 3.2 Transaction-time as-of ("ledger view as known at system moment T")

```csharp
// Parameter: asOfTx — the system clock moment (ISO-8601 string, UTC)
IEnumerable<PinnedElement> QueryTxAsOf(IReadOnlyList<PinnedElement> ledger, string asOfTx) =>
    ledger.Where(e =>
        string.Compare(e.RecordedAt, asOfTx, StringComparison.Ordinal) <= 0
        && (e.SupersededAt is null || string.Compare(e.SupersededAt, asOfTx, StringComparison.Ordinal) > 0)
    );
// SupersededAt IS NULL = still current in the ledger; included for all asOfTx >= RecordedAt.
```

### 3.3 Bitemporal combination ("graph state at pin X")

```csharp
// Parameters: asOf (valid time), asOfTx (transaction time)
IEnumerable<PinnedElement> QueryBitemporal(
    IReadOnlyList<PinnedElement> ledger, string asOf, string asOfTx) =>
    ledger.Where(e =>
        // Valid-time axis
        string.Compare(e.ValidFrom, asOf, StringComparison.Ordinal) <= 0
        && (e.ValidTo is null || string.Compare(e.ValidTo, asOf, StringComparison.Ordinal) > 0)
        // Transaction-time axis
        && string.Compare(e.RecordedAt, asOfTx, StringComparison.Ordinal) <= 0
        && (e.SupersededAt is null || string.Compare(e.SupersededAt, asOfTx, StringComparison.Ordinal) > 0)
    );
```

### 3.4 Live view — current state, both axes open

```csharp
// Returns the single current version for each identity_hash (SupersededAt IS NULL,
// ValidTo IS NULL = open-ended). This is what GetLiveAsync exposes.
IEnumerable<PinnedElement> QueryLive(IReadOnlyList<PinnedElement> ledger) =>
    ledger.Where(e => e.SupersededAt is null && e.ValidTo is null);

// Alternatively, use the live Dictionary<string,PinnedElement> directly for O(1) lookup:
PinnedElement? GetLive(Dictionary<string, PinnedElement> liveIndex, string identityHash) =>
    liveIndex.GetValueOrDefault(identityHash);
```

### 3.5 History series — all versions for a single object

```csharp
// Returns all ledger entries for one identity, ordered by RecordedAt ascending.
// This is what GetHistoryAsync exposes. The series expresses how the ledger's
// knowledge of this object evolved over transaction time.
IEnumerable<PinnedElement> QueryHistory(
    IReadOnlyList<PinnedElement> ledger, string identityHash) =>
    ledger
        .Where(e => e.IdentityHash == identityHash)
        .OrderBy(e => e.RecordedAt, StringComparer.Ordinal);
```

### 3.6 Scoped history by type/concept (supporting GetHistoryAsync overloads)

```csharp
// All versions of all objects of a given UFO kind, ordered by RecordedAt.
IEnumerable<PinnedElement> QueryHistoryByKind(
    IReadOnlyList<PinnedElement> ledger, string ufoStereotype) =>
    ledger
        .Where(e => e.UfoStereotype == ufoStereotype)
        .OrderBy(e => e.RecordedAt, StringComparer.Ordinal);

// All versions of all objects of a given ontology concept.
IEnumerable<PinnedElement> QueryHistoryByConcept(
    IReadOnlyList<PinnedElement> ledger, string ontologyConcept) =>
    ledger
        .Where(e => e.OntologyConcept == ontologyConcept)
        .OrderBy(e => e.RecordedAt, StringComparer.Ordinal);
```

---

## 4. ArcadeDB SQL (PIN-F4)

ArcadeDB SQL is ANSI-SQL-shaped; ISO-8601 strings sort correctly with `<=` / `>` comparisons when stored as `STRING` and normalised to UTC. All queries target the `PinLedgerEntry` document class (the immutable ledger) and the `OntologyElement` vertex class (the live view).

### 4.1 Valid-time as-of

```sql
-- What was the graph state at business moment :asOf?
-- Parameterised: :asOf = ISO-8601 string (UTC-normalised)
SELECT *
FROM PinLedgerEntry
WHERE valid_from <= :asOf
  AND (valid_to IS NULL OR valid_to > :asOf)
ORDER BY recorded_at ASC;

-- Scope to a single object by identity:
SELECT *
FROM PinLedgerEntry
WHERE identity_hash = :identityHash
  AND valid_from <= :asOf
  AND (valid_to IS NULL OR valid_to > :asOf)
ORDER BY recorded_at ASC;
```

### 4.2 Transaction-time as-of

```sql
-- What did the ledger contain as of system moment :asOfTx?
-- Parameterised: :asOfTx = ISO-8601 string (UTC-normalised)
SELECT *
FROM PinLedgerEntry
WHERE recorded_at <= :asOfTx
  AND (superseded_at IS NULL OR superseded_at > :asOfTx)
ORDER BY recorded_at ASC;

-- Scope to a single object:
SELECT *
FROM PinLedgerEntry
WHERE identity_hash = :identityHash
  AND recorded_at <= :asOfTx
  AND (superseded_at IS NULL OR superseded_at > :asOfTx)
ORDER BY recorded_at ASC;
```

### 4.3 Bitemporal combination — "graph state at pin X"

```sql
-- The canonical bitemporal point query: what did we record about domain time :asOf,
-- as the ledger stood at system time :asOfTx?
-- Parameterised: :asOf = ISO-8601 valid-time; :asOfTx = ISO-8601 transaction-time
SELECT *
FROM PinLedgerEntry
WHERE valid_from <= :asOf
  AND (valid_to IS NULL OR valid_to > :asOf)
  AND recorded_at <= :asOfTx
  AND (superseded_at IS NULL OR superseded_at > :asOfTx)
ORDER BY identity_hash, recorded_at ASC;

-- Scoped to one object:
SELECT *
FROM PinLedgerEntry
WHERE identity_hash = :identityHash
  AND valid_from <= :asOf
  AND (valid_to IS NULL OR valid_to > :asOf)
  AND recorded_at <= :asOfTx
  AND (superseded_at IS NULL OR superseded_at > :asOfTx);
```

### 4.4 Live view — current, open-ended state

```sql
-- The live view: current transaction-time row with open-ended valid interval.
-- Prefer the OntologyElement live vertex class for O(1) lookup (maintained by UPSERT in PIN-F4).
SELECT *
FROM OntologyElement
WHERE identity_hash = :identityHash;

-- Or query the ledger directly for the current row (no expiry on either axis):
SELECT *
FROM PinLedgerEntry
WHERE identity_hash = :identityHash
  AND superseded_at IS NULL
  AND valid_to IS NULL;

-- All live objects of a given concept:
SELECT *
FROM OntologyElement
WHERE ontology_concept = :concept;
```

### 4.5 History series — all versions for a single object

```sql
-- Full transaction-time history for one identity, oldest-first.
-- Use for audit, diff, and replay.
SELECT *
FROM PinLedgerEntry
WHERE identity_hash = :identityHash
ORDER BY recorded_at ASC;

-- History with valid-time context — useful for timeline visualisation:
SELECT identity_hash, content_hash, valid_from, valid_to,
       recorded_at, superseded_at, state, ufo_stereotype
FROM PinLedgerEntry
WHERE identity_hash = :identityHash
ORDER BY recorded_at ASC;
```

### 4.6 History series scoped to concept or stereotype

```sql
-- All ledger entries for a given ontology concept, ordered by recording time.
SELECT *
FROM PinLedgerEntry
WHERE ontology_concept = :concept
ORDER BY identity_hash, recorded_at ASC;

-- All entries for a UFO stereotype (e.g. 'relator', 'kind', 'event').
SELECT *
FROM PinLedgerEntry
WHERE ufo_stereotype = :ufoStereotype
ORDER BY identity_hash, recorded_at ASC;
```

### 4.7 Relator-specific queries (hyperedge-as-vertex)

The `ingest-evidence` relator persists as a `HyperEdge` vertex with `BINDS_ROLE` edges. Bitemporal queries on relators follow the same pattern but target the relator vertex class.

```sql
-- Live relator for a given relator type:
SELECT *
FROM HyperEdge
WHERE relator_type = :relatorType
  AND superseded_at IS NULL
  AND valid_to IS NULL;

-- Bitemporal query on a relator vertex:
SELECT *
FROM HyperEdge
WHERE identity_hash = :relatorIdentityHash
  AND valid_from <= :asOf
  AND (valid_to IS NULL OR valid_to > :asOf)
  AND recorded_at <= :asOfTx
  AND (superseded_at IS NULL OR superseded_at > :asOfTx);

-- Retrieve role bindings for a relator version (two-hop: relator -> BINDS_ROLE -> participant):
SELECT expand(outE('BINDS_ROLE'))
FROM HyperEdge
WHERE @rid = :relatorRid;
```

---

## 5. Index Needs (Feedback to PIN-F4)

The PIN-F4 DDL already specifies several indexes. This spike confirms and extends them based on the query patterns above.

### 5.1 Confirmed required indexes

| Index | Type | Columns | Covers |
|---|---|---|---|
| `idx_ledger_identity_tx` | Composite (range) | `(identity_hash, recorded_at)` | History series (Sec 4.5); transaction-time scoped to one object |
| `idx_ledger_identity_superseded` | Composite | `(identity_hash, superseded_at, recorded_at)` | Live lookup via ledger; transaction-time as-of |
| `idx_ledger_identity_valid` | Composite (range) | `(identity_hash, valid_from, recorded_at)` | Valid-time as-of scoped to one object |
| `idx_element_iri_content` | Unique | `(ontology_iri, content_hash)` | Idempotency guard on insert |
| `idx_element_type_valid` | Composite | `(type, valid_from, valid_to)` | Valid-time range scan across a concept |

### 5.2 Additional indexes identified by this spike

| Index | Type | Columns | Rationale |
|---|---|---|---|
| `idx_ledger_bitemporal` | Composite (range) | `(identity_hash, valid_from, recorded_at, superseded_at)` | The full bitemporal combination query (Sec 4.3) filtered to one object; avoids a merge of two separate range scans |
| `idx_ledger_concept_recorded` | Composite | `(ontology_concept, recorded_at)` | Concept-scoped history series (Sec 4.6); supports time-ordered audit per concept |
| `idx_ledger_stereotype_recorded` | Composite | `(ufo_stereotype, recorded_at)` | Stereotype-scoped history (Sec 4.6); supports grouping endurants vs relators vs events over time |
| `idx_ledger_superseded_null` | Partial (filter: `superseded_at IS NULL`) | `(identity_hash)` | Fast current-version lookup via ledger when the live vertex is not available; ArcadeDB supports partial index via `WHERE` clause in DDL |
| `idx_hyperedge_relator_type_valid` | Composite | `(relator_type, valid_from, valid_to)` | Relator live-view and valid-time scan (Sec 4.7) — mirrors the existing element index but for the `HyperEdge` vertex class |
| `idx_role_binding_name` | Hash | `role_name` | Already specified in PIN-F4; confirmed necessary for role traversal (Sec 4.7) |

### 5.3 Index guidance notes

- ArcadeDB SQL does not support function-based indexes. All bitemporal fields must be stored as ISO-8601 UTC strings (never locale-formatted dates) so that string lexicographic order equals temporal order.
- ArcadeDB composite indexes are used via `ORDER BY` on the index key columns. Prefix the most selective column first (`identity_hash` before `recorded_at`) to maximise pruning.
- For the `valid_to IS NULL` and `superseded_at IS NULL` conditions, ArcadeDB's partial index (filtered index) is the most efficient approach. Without it, a full scan is required for the null branch of every OR predicate. Partial index DDL example:
  ```sql
  CREATE INDEX PinLedgerEntry[identity_hash]
      ON PinLedgerEntry (identity_hash)
      NOTUNIQUE
      WHERE superseded_at IS NULL;
  ```
- The `OntologyElement` live vertex class is the preferred target for live-view queries. It is maintained by `UPDATE ... UPSERT` in PIN-F4. Avoid querying the ledger for the live view in hot paths — the live vertex is O(1) via identity_hash.

---

## 6. Edge Cases and Behaviour Contracts

### 6.1 Open-ended valid_to

A `valid_to = NULL` record is included in any valid-time range query where `asOf >= valid_from`. The predicate `(valid_to IS NULL OR valid_to > :asOf)` handles this correctly. Callers must not assume `null` means "never expires" — it means "no known expiry at recording time." A future re-pin can set `valid_to` to a concrete value, which supersedes the open-ended version and creates a new ledger row.

### 6.2 Null superseded_at = current version

A `superseded_at = NULL` row is the current ledger entry for its `identity_hash`. When `PinObjectAsync` is called with a changed payload, the backend sets `superseded_at = now()` on the previous row (in a guarded UPDATE) and inserts a fresh row with `superseded_at = NULL`. The live vertex is UPSERTed in the same operation. These two writes must be atomic or wrapped in a retry with an idempotency guard on `content_hash` to avoid double-insert on retry.

### 6.3 Re-pinning identical content (idempotency)

If `identity_hash` and `content_hash` are both unchanged, PIN-F3 must skip ledger insertion entirely (no-op). In ArcadeDB (PIN-F4) the guarded INSERT targets the unique index on `(ontology_iri, content_hash)` — a duplicate will produce a constraint violation that the adapter catches and swallows. The live vertex UPSERT is still safe to issue (idempotent by design).

### 6.4 PinGraphAsync — relator and participant alignment

When `PinGraphAsync` pins a full knowledge-drop graph, all participant objects and the relator are pinned in the same logical operation. The transaction timestamp (`recorded_at`) must be the same value for all entries written in one `PinGraphAsync` call (use one clock read at the start of the method). This ensures that a bitemporal query at exactly that transaction timestamp returns a complete and consistent graph snapshot.

### 6.5 Query ordering of history series

`GetHistoryAsync` must order by `recorded_at` ascending. If two ledger entries share the same `recorded_at` (possible if the clock resolution is coarse), the tiebreaker should be `content_hash` (deterministic) rather than insertion order (non-deterministic).

### 6.6 Valid-time intervals and the temporal pulse

The reification design (Reification-and-Hyperedges.md) aligns a relator version's `valid_from`/`recorded_at` with the global temporal pulse tick. If the caller does not supply an explicit `valid_from`, the pinner should default it to `recorded_at` (the serialisation timestamp), making the temporal origin of each version unambiguous.

---

## 7. Summary: Live View vs History Series

| Query | In-memory (PIN-F3) | ArcadeDB (PIN-F4) | Time complexity |
|---|---|---|---|
| Live single object | `liveIndex[identityHash]` (Dictionary) | `SELECT FROM OntologyElement WHERE identity_hash = :id` | O(1) via live index |
| Live all objects of concept | LINQ `.Where(e => e.OntologyConcept == c && e.SupersededAt == null && e.ValidTo == null)` | `SELECT FROM OntologyElement WHERE ontology_concept = :c` | O(n concept members) |
| History series | LINQ `.Where(e => e.IdentityHash == id).OrderBy(e => e.RecordedAt)` | `SELECT FROM PinLedgerEntry WHERE identity_hash = :id ORDER BY recorded_at ASC` | O(versions) |
| Valid-time as-of | LINQ filter on `ValidFrom` / `ValidTo` | Indexed range on `(identity_hash, valid_from)` | O(log n + results) |
| Transaction-time as-of | LINQ filter on `RecordedAt` / `SupersededAt` | Indexed range on `(identity_hash, superseded_at, recorded_at)` | O(log n + results) |
| Bitemporal combination | LINQ AND of both predicates | Composite range on `(identity_hash, valid_from, recorded_at, superseded_at)` | O(log n + results) |
| Relator + role bindings | Scan relator ledger, follow `RoleBinding` list | Two-hop graph: `HyperEdge` vertex + `outE('BINDS_ROLE')` expand | O(role count) per relator |
