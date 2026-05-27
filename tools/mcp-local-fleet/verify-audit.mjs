#!/usr/bin/env node
// Verify the integrity of an audit log file by re-walking its hash chain.
//
// Usage:
//   node tools/mcp-local-fleet/verify-audit.mjs                    # today
//   node tools/mcp-local-fleet/verify-audit.mjs 2026-05-27        # explicit date
//   node tools/mcp-local-fleet/verify-audit.mjs --all              # every audit log
//
// Exits 0 if every record's hash chain is intact; non-zero on any tampering.
// Audit log is append-only NDJSON where each record has `prev_hash` (sha256 of
// the previous record's serialised JSON minus its own `hash` field) and `hash`
// (sha256 of THIS record's serialised JSON minus its own `hash` field). Any
// deletion, reorder, or edit in the middle of the file breaks the chain at
// that point and every record after.

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const LOG_DIR = path.join(ROOT, "tools", "logs");

const sha256 = (s) => createHash("sha256").update(s, "utf8").digest("hex");

function todayStamp() {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,"0")}-${String(d.getUTCDate()).padStart(2,"0")}`;
}

function verifyFile(filePath) {
  if (!existsSync(filePath)) { console.error(`  no file: ${filePath}`); return { ok: false, broken: 0, total: 0 }; }
  const lines = readFileSync(filePath, "utf8").split("\n").filter(Boolean);
  let expectedPrev = "GENESIS"; // gets set to the first hashed record's hash
  let chainStarted = false;
  let legacyCount = 0;
  let broken = 0;
  for (let i = 0; i < lines.length; i++) {
    let rec;
    try { rec = JSON.parse(lines[i]); }
    catch (e) {
      console.error(`  line ${i + 1}: JSON parse failed — ${e.message}`);
      broken++;
      continue;
    }
    // Legacy records (pre hash-chain deployment) have no hash/prev_hash fields.
    // Skip them with a one-line note; the chain begins at the first record
    // that has both fields.
    if (rec.hash === undefined && rec.prev_hash === undefined) {
      legacyCount++;
      continue;
    }
    const stated = rec.hash;
    const { hash: _drop, ...payload } = rec;
    const expected = sha256(JSON.stringify(payload));
    if (!chainStarted) {
      // First hashed record — must claim prev_hash=GENESIS to start a fresh chain.
      if (payload.prev_hash !== "GENESIS") {
        console.error(`  line ${i + 1}: first hashed record's prev_hash=${payload.prev_hash?.slice(0,12)}… (expected GENESIS)`);
        broken++;
      }
      chainStarted = true;
    } else if (payload.prev_hash !== expectedPrev) {
      console.error(`  line ${i + 1}: prev_hash mismatch (rec=${(payload.prev_hash||"").slice(0,12)}…, expected=${expectedPrev.slice(0,12)}…)`);
      broken++;
    }
    if (stated !== expected) {
      console.error(`  line ${i + 1}: hash mismatch (rec=${(stated||"").slice(0,12)}…, computed=${expected.slice(0,12)}…)`);
      broken++;
    }
    expectedPrev = stated;
  }
  if (legacyCount > 0) console.log(`  (skipped ${legacyCount} pre-hash-chain legacy record(s))`);
  return { ok: broken === 0, broken, total: lines.length };
}

const arg = process.argv[2];
let files = [];
if (arg === "--all") {
  files = readdirSync(LOG_DIR).filter((f) => /^mcp-audit\.log\.\d{4}-\d{2}-\d{2}$/.test(f)).map((f) => path.join(LOG_DIR, f));
} else {
  const stamp = arg || todayStamp();
  files = [path.join(LOG_DIR, `mcp-audit.log.${stamp}`)];
}

let allOk = true;
for (const f of files) {
  console.log(`verifying ${path.basename(f)}…`);
  const r = verifyFile(f);
  if (r.ok) console.log(`  OK — ${r.total} records, hash chain intact`);
  else { allOk = false; console.error(`  FAIL — ${r.broken} broken record(s) of ${r.total}`); }
}
process.exit(allOk ? 0 : 1);
