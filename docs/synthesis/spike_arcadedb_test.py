#!/usr/bin/env python3
"""
PIN-S1 Spike: ArcadeDB UPSERT / Idempotency / Batching verification
LIVE against arcadedata/arcadedb:26.5.1 on localhost:12480

Security note: Uses http.client against 127.0.0.1:12480 (loopback-only spike
container). HTTP is intentional -- this is an isolated localhost test harness,
not production traffic. No user-supplied URL is accepted; host/port are
compile-time constants.
"""

import http.client
import json
import base64
import sys
from datetime import datetime, timezone

# Hard-coded loopback constants -- no user-supplied input reaches these.
_ARCADE_HOST = "127.0.0.1"   # nosec: localhost spike harness only
_ARCADE_PORT = 12480          # nosec: localhost spike harness only
_DB = "spike_pin_test"
_AUTH = base64.b64encode(b"root:SpikeTest2026!").decode()
_HEADERS = {
    "Authorization": "Basic " + _AUTH,
    "Content-Type": "application/json",
}

results = []


def _arcade_post(path: str, payload: dict) -> dict:
    """POST JSON payload to the ArcadeDB HTTP command API (loopback only)."""
    data = json.dumps(payload).encode()
    # http.client with a literal host constant -- no dynamic URL, no file:// risk.
    conn = http.client.HTTPConnection(_ARCADE_HOST, _ARCADE_PORT, timeout=10)
    try:
        conn.request("POST", path, body=data, headers=_HEADERS)
        resp = conn.getresponse()
        body_bytes = resp.read()
        body = json.loads(body_bytes) if body_bytes else {}
        if resp.status >= 400:
            return {
                "ok": False,
                "status": resp.status,
                "error": body.get("detail") or body.get("error") or resp.reason,
                "raw": body,
            }
        return {"ok": True, "status": resp.status, "rows": body.get("result", []), "raw": body}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": str(exc)}
    finally:
        conn.close()


def sql(command: str, params=None) -> dict:
    payload = {"language": "sql", "command": command}
    if params:
        payload["params"] = params
    return _arcade_post("/api/v1/command/" + _DB, payload)


def script(command_str: str) -> dict:
    return _arcade_post(
        "/api/v1/command/" + _DB,
        {"language": "sqlscript", "command": command_str},
    )


def record(test_id, description, result, assertion, evidence=None):
    passed = assertion(result)
    status = "PASS" if passed else "FAIL"
    entry = {
        "id": test_id,
        "description": description,
        "status": status,
        "result_ok": result.get("ok"),
        "evidence": evidence or str(result.get("rows") or result.get("error", "")),
    }
    results.append(entry)
    mark = "[PASS]" if passed else "[FAIL]"
    print("  " + mark + " " + test_id + ": " + description)
    if not passed:
        print("         Got: " + str(result))
    return passed


print("")
print("=== PIN-S1 ArcadeDB Spike Tests ===")
print("    Version: 26.5.1  DB: " + _DB + "  Time: " + datetime.now(timezone.utc).isoformat())
print("")

# -----------------------------------------------------------------
print("1. DDL: CREATE VERTEX / DOCUMENT types (idempotency)")
# -----------------------------------------------------------------

r = sql("CREATE VERTEX TYPE OntologyElement IF NOT EXISTS")
record("DDL-01", "CREATE VERTEX TYPE OntologyElement (first call)", r, lambda x: x["ok"])

r = sql("CREATE VERTEX TYPE OntologyElement IF NOT EXISTS")
record("DDL-02", "CREATE VERTEX TYPE IF NOT EXISTS (repeat - must be idempotent)", r,
       lambda x: x["ok"], "Second call must not error")

r = sql("CREATE DOCUMENT TYPE PinLedgerEntry IF NOT EXISTS")
record("DDL-03", "CREATE DOCUMENT TYPE PinLedgerEntry", r, lambda x: x["ok"])

r = sql("CREATE DOCUMENT TYPE PinLedgerEntry IF NOT EXISTS")
record("DDL-04", "CREATE DOCUMENT TYPE IF NOT EXISTS (repeat)", r, lambda x: x["ok"])

# -----------------------------------------------------------------
print("")
print("2. UNIQUE INDEX creation")
# -----------------------------------------------------------------

r = sql("CREATE PROPERTY OntologyElement.ontology_iri IF NOT EXISTS STRING")
record("IDX-01", "CREATE PROPERTY ontology_iri on OntologyElement", r, lambda x: x["ok"])

r = sql("CREATE INDEX IF NOT EXISTS ON OntologyElement (ontology_iri) UNIQUE")
record("IDX-02", "CREATE UNIQUE INDEX on ontology_iri (first call)", r, lambda x: x["ok"])

r = sql("CREATE INDEX IF NOT EXISTS ON OntologyElement (ontology_iri) UNIQUE")
record("IDX-03", "CREATE UNIQUE INDEX IF NOT EXISTS (repeat - idempotent)", r, lambda x: x["ok"])

for prop in ["identity_hash", "content_hash", "label", "state", "recorded_at"]:
    sql("CREATE PROPERTY OntologyElement." + prop + " IF NOT EXISTS STRING")

for prop in ["content_hash", "ontology_iri", "identity_hash", "recorded_at", "valid_from", "valid_to"]:
    sql("CREATE PROPERTY PinLedgerEntry." + prop + " IF NOT EXISTS STRING")

r = sql("CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (content_hash) UNIQUE")
record("IDX-04", "CREATE UNIQUE INDEX on PinLedgerEntry.content_hash", r, lambda x: x["ok"])

print("  [INFO] Additional properties created")

# -----------------------------------------------------------------
print("")
print("3. UPDATE...UPSERT semantics (live row)")
# -----------------------------------------------------------------

UPSERT_SQL = (
    "UPDATE OntologyElement "
    "SET identity_hash = 'hash-001', label = 'Invoice', state = 'active', "
    "recorded_at = '2026-01-01T00:00:00Z' "
    "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001'"
)

r = sql(UPSERT_SQL)
record("UPSERT-01", "First UPDATE...UPSERT creates vertex (count=1)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("count") == 1 if x.get("rows") else False,
       "rows=" + str(r.get("rows")))

r = sql(UPSERT_SQL)
record("UPSERT-02", "Repeat UPSERT same content -> count=1 (no duplicate)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("count") == 1 if x.get("rows") else False,
       "rows=" + str(r.get("rows")))

r = sql("SELECT count(*) AS n FROM OntologyElement WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001'")
record("UPSERT-03", "Only 1 OntologyElement row after 2 UPSERTs (no phantom duplicates)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 1 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

UPSERT_UPDATED = (
    "UPDATE OntologyElement "
    "SET identity_hash = 'hash-001', label = 'Invoice-v2', state = 'active', "
    "recorded_at = '2026-01-02T00:00:00Z' "
    "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001'"
)
r = sql(UPSERT_UPDATED)
record("UPSERT-04", "UPSERT with changed content -> count=1 (update in-place)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("count") == 1 if x.get("rows") else False,
       "rows=" + str(r.get("rows")))

r = sql("SELECT label FROM OntologyElement WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001'")
record("UPSERT-05", "After content update: label is Invoice-v2", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("label") == "Invoice-v2" if x.get("rows") else False,
       "rows=" + str(r.get("rows")))

r = sql(
    "UPDATE OntologyElement SET label = 'Invoice-v3' "
    "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001'"
)
record("UPSERT-06", "UPSERT result shape: {count: N}", r,
       lambda x: x["ok"] and "count" in (x.get("rows", [{}])[0] if x.get("rows") else {}),
       "rows=" + str(r.get("rows")))

# -----------------------------------------------------------------
print("")
print("4. UNIQUE-guarded INSERT (ledger no-op on duplicate)")
# -----------------------------------------------------------------

LEDGER_SQL = (
    "INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-abc123', "
    "ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001', "
    "identity_hash = 'hash-001', "
    "recorded_at = '2026-01-01T00:00:00Z'"
)

r = sql(LEDGER_SQL)
record("LEDGER-01", "First INSERT into ledger succeeds", r,
       lambda x: x["ok"],
       "rows=" + str(r.get("rows")))

r_dup = sql(LEDGER_SQL)
record("LEDGER-02", "Duplicate INSERT (same content_hash) fails with error", r_dup,
       lambda x: not x["ok"],
       "ok=" + str(r_dup.get("ok")) + " error=" + str(r_dup.get("error")))

record("LEDGER-03", "Duplicate error message references uniqueness/index", r_dup,
       lambda x: any(kw in str(x.get("error", "")).lower()
                     for kw in ["unique", "duplicate", "constraint", "exist", "index"]),
       "error=" + str(r_dup.get("error")))

r = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE content_hash = 'sha256-abc123'")
record("LEDGER-04", "Only 1 ledger row after 2 INSERT attempts", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 1 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

r = sql(
    "INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-def456', "
    "ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/001', "
    "identity_hash = 'hash-001', "
    "recorded_at = '2026-01-02T00:00:00Z'"
)
record("LEDGER-05", "INSERT with different content_hash creates new ledger entry", r,
       lambda x: x["ok"],
       "rows=" + str(r.get("rows")))

r = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE identity_hash = 'hash-001'")
record("LEDGER-06", "2 ledger entries for same identity (2 distinct pins)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 2 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

# -----------------------------------------------------------------
print("")
print("5. sqlscript BEGIN/COMMIT batch (two operations in one transaction)")
# -----------------------------------------------------------------

r_script = script(
    "BEGIN;\n"
    "LET e1 = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-script-001', ontology_iri = 'urn:script:001', "
    "identity_hash = 'hash-script', recorded_at = '2026-01-01T00:00:00Z';\n"
    "LET e2 = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-script-002', ontology_iri = 'urn:script:002', "
    "identity_hash = 'hash-script', recorded_at = '2026-01-01T00:00:00Z';\n"
    "COMMIT;\n"
    "RETURN $e2;"
)
record("BATCH-01", "sqlscript BEGIN/COMMIT batch: two INSERTs in one transaction", r_script,
       lambda x: x["ok"],
       "ok=" + str(r_script.get("ok")) + " error=" + str(r_script.get("error")))

r = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE identity_hash = 'hash-script'")
record("BATCH-02", "Both script-inserted rows committed", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 2 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

# -----------------------------------------------------------------
print("")
print("6. Transaction rollback on UNIQUE violation (atomicity)")
# -----------------------------------------------------------------

sql(
    "INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-atomic-001', ontology_iri = 'urn:atomic:001', "
    "identity_hash = 'h1', recorded_at = '2026-01-01T00:00:00Z'"
)

r_atomic = script(
    "BEGIN;\n"
    "LET n1 = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-atomic-new', ontology_iri = 'urn:atomic:new', "
    "identity_hash = 'h-new', recorded_at = '2026-01-01T00:00:00Z';\n"
    "LET n2 = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-atomic-001', ontology_iri = 'urn:atomic:dup', "
    "identity_hash = 'h-dup', recorded_at = '2026-01-01T00:00:00Z';\n"
    "COMMIT;\n"
    "RETURN $n1;"
)
record("ATOMIC-01", "Script with UNIQUE violation fails (whole batch rejected)", r_atomic,
       lambda x: not x["ok"],
       "ok=" + str(r_atomic.get("ok")) + " error=" + str(r_atomic.get("error")))

r = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE content_hash = 'sha256-atomic-new'")
record("ATOMIC-02", "Rolled-back record NOT in ledger (atomicity confirmed)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 0 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

# -----------------------------------------------------------------
print("")
print("7. PIN-F4 pattern: UPSERT live + INSERT ledger in one sqlscript")
# -----------------------------------------------------------------

r_pin = script(
    "BEGIN;\n"
    "LET live = UPDATE OntologyElement "
    "SET identity_hash = 'hash-inv-002', label = 'Invoice-002', state = 'active', "
    "recorded_at = '2026-02-01T00:00:00Z' "
    "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002';\n"
    "LET ledger = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-inv002-v1', "
    "ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002', "
    "identity_hash = 'hash-inv-002', recorded_at = '2026-02-01T00:00:00Z';\n"
    "COMMIT;\n"
    "RETURN $live;"
)
record("PIN-01", "First pin: UPSERT live + INSERT ledger in one sqlscript transaction", r_pin,
       lambda x: x["ok"],
       "ok=" + str(r_pin.get("ok")) + " rows=" + str(r_pin.get("rows")))

r_repin = script(
    "BEGIN;\n"
    "LET live = UPDATE OntologyElement "
    "SET identity_hash = 'hash-inv-002', label = 'Invoice-002', state = 'active', "
    "recorded_at = '2026-02-01T00:00:00Z' "
    "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002';\n"
    "LET ledger = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-inv002-v1', "
    "ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002', "
    "identity_hash = 'hash-inv-002', recorded_at = '2026-02-01T00:00:00Z';\n"
    "COMMIT;\n"
    "RETURN $live;"
)
record("PIN-02", "Re-pin same content: whole tx fails (INSERT violates UNIQUE -> rollback)", r_repin,
       lambda x: not x["ok"],
       "ok=" + str(r_repin.get("ok")) + " error=" + str(r_repin.get("error")))

r = sql("SELECT count(*) AS n FROM OntologyElement WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002'")
record("PIN-03", "Live row persisted from first pin (exists after failed re-pin)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 1 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

r = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE content_hash = 'sha256-inv002-v1'")
record("PIN-04", "Only 1 ledger entry for inv002-v1 (re-pin was no-op)", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 1 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

# -----------------------------------------------------------------
print("")
print("8. Safe re-pin pattern: check-before-insert to avoid tx rollback")
# -----------------------------------------------------------------

r_check = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE content_hash = 'sha256-inv002-v1'")
already_pinned = r_check.get("rows", [{}])[0].get("n", 0) > 0
record("SAFE-01", "Pre-check: content_hash lookup returns correct count", r_check,
       lambda x: x["ok"],
       "already_pinned=" + str(already_pinned) + " count=" + str(r_check.get("rows")))

if already_pinned:
    record("SAFE-02", "Safe re-pin: skipped (content already pinned)", {"ok": True},
           lambda x: x["ok"], "skipped=True - content_hash found, no INSERT attempted")
else:
    r_safe = script(
        "BEGIN;\n"
        "LET live = UPDATE OntologyElement "
        "SET identity_hash = 'hash-inv-002', label = 'Invoice-002', state = 'active', "
        "recorded_at = '2026-02-01T00:00:00Z' "
        "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002';\n"
        "LET ledger = INSERT INTO PinLedgerEntry "
        "SET content_hash = 'sha256-inv002-v1', "
        "ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002', "
        "identity_hash = 'hash-inv-002', recorded_at = '2026-02-01T00:00:00Z';\n"
        "COMMIT;\n"
        "RETURN $live;"
    )
    record("SAFE-02", "Safe re-pin with check first succeeds", r_safe, lambda x: x["ok"])

r_safe_new = script(
    "BEGIN;\n"
    "LET live = UPDATE OntologyElement "
    "SET identity_hash = 'hash-inv-002', label = 'Invoice-002-updated', state = 'active', "
    "recorded_at = '2026-02-02T00:00:00Z' "
    "UPSERT WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002';\n"
    "LET ledger = INSERT INTO PinLedgerEntry "
    "SET content_hash = 'sha256-inv002-v2', "
    "ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002', "
    "identity_hash = 'hash-inv-002', recorded_at = '2026-02-02T00:00:00Z';\n"
    "COMMIT;\n"
    "RETURN $live;"
)
record("SAFE-03", "Pin with new content succeeds: live updated + new ledger entry", r_safe_new,
       lambda x: x["ok"],
       "ok=" + str(r_safe_new.get("ok")) + " rows=" + str(r_safe_new.get("rows")))

r = sql("SELECT count(*) AS n FROM PinLedgerEntry WHERE identity_hash = 'hash-inv-002'")
record("SAFE-04", "2 ledger entries for inv-002 after two distinct content pins", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("n") == 2 if x.get("rows") else False,
       "count=" + str(r.get("rows")))

r = sql("SELECT label FROM OntologyElement WHERE ontology_iri = 'urn:agentarmy:mc:invoice/Invoice/002'")
record("SAFE-05", "Live row updated to Invoice-002-updated", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("label") == "Invoice-002-updated" if x.get("rows") else False,
       "rows=" + str(r.get("rows")))

# -----------------------------------------------------------------
print("")
print("9. Composite UNIQUE INDEX (identity_hash, recorded_at)")
# -----------------------------------------------------------------

r = sql("CREATE INDEX IF NOT EXISTS ON PinLedgerEntry (identity_hash, recorded_at) UNIQUE")
record("CIDX-01", "CREATE composite UNIQUE INDEX (identity_hash, recorded_at)", r, lambda x: x["ok"],
       "ok=" + str(r.get("ok")) + " error=" + str(r.get("error")))

# -----------------------------------------------------------------
print("")
print("10. HTTP API response shape confirmation")
# -----------------------------------------------------------------

r = sql("SELECT count(*) AS n FROM OntologyElement")
record("HTTP-01", "HTTP command API returns {result: [...rows]} shape", r,
       lambda x: x["ok"] and "raw" in x and "result" in x.get("raw", {}),
       "keys=" + str(list(r.get("raw", {}).keys())))

r = sql("SELECT count(*) AS total FROM PinLedgerEntry")
record("HTTP-02", "SQL count query works on document type", r,
       lambda x: x["ok"] and x.get("rows", [{}])[0].get("total", -1) >= 0 if x.get("rows") else False,
       "rows=" + str(r.get("rows")))

# -----------------------------------------------------------------
# Summary
# -----------------------------------------------------------------
passed = [x for x in results if x["status"] == "PASS"]
failed = [x for x in results if x["status"] == "FAIL"]

print("")
print("=== SUMMARY ===")
print("  Total: " + str(len(results)) + "  PASS: " + str(len(passed)) + "  FAIL: " + str(len(failed)))

if failed:
    print("")
    print("  Failed tests:")
    for f in failed:
        print("    - " + f["id"] + ": " + f["description"])
        print("      evidence: " + str(f.get("evidence")))

print("")
print("=== JSON RESULTS ===")
print(json.dumps(results, indent=2, default=str))

sys.exit(0 if not failed else 1)
