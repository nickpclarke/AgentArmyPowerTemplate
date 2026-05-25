# PIN-S2 — Bitemporal pin/snapshot query findings

## Scope

Assume `PinLedgerEntry` rows carry `identity_hash`, `recorded_at`, `superseded_at`, `valid_from`, `valid_to`, and the immutable payload for one pinned version.

## Query templates

### 1) Live view

```sql
SELECT FROM PinLedgerEntry
WHERE identity_hash = :identity_hash
  AND superseded_at IS NULL
ORDER BY recorded_at DESC
LIMIT 1;
```

For historical replay at an earlier transaction time, tighten this to `recorded_at <= :tx_time` and replace the live predicate with `(superseded_at IS NULL OR superseded_at > :tx_time)`.

### 2) State as of a valid time

```sql
SELECT FROM PinLedgerEntry
WHERE identity_hash = :identity_hash
  AND valid_from <= :valid_at
  AND (valid_to IS NULL OR valid_to > :valid_at)
ORDER BY recorded_at DESC
LIMIT 1;
```

Add `recorded_at <= :tx_time` when the caller needs a valid-time snapshot from an earlier transaction boundary rather than the latest correction.

### 3) Full history

```sql
SELECT FROM PinLedgerEntry
WHERE identity_hash = :identity_hash
ORDER BY recorded_at ASC;
```

## Index recommendations

- Add `(identity_hash, superseded_at, recorded_at)` for the live-row lookup path.
- Add `(identity_hash, recorded_at)` for full history and transaction-time replay.
- Add `(identity_hash, valid_from, recorded_at)` for valid-time snapshots; keep `valid_to` as a post-filter because the query already consumes one range predicate on `valid_from`.

These recommendations feed back into PIN-F4 so the ArcadeDB adapter is indexed for identity-local reads, not just global type scans.
