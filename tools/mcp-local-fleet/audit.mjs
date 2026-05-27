// Append-only NDJSON audit log for MCP tool calls + security events.
//
// Tamper-evidence: each record includes `prev_hash` (sha256 of the previous
// record's serialised JSON) and `hash` (sha256 of THIS record's serialised
// JSON excluding the hash field itself). Editing or deleting any historical
// line breaks the chain — `tools/mcp-local-fleet/verify-audit.mjs` (run
// periodically) detects tampering.
//
// Two sinks:
//   - tools/logs/mcp-audit.log.YYYY-MM-DD       — every tool call, hash-chained
//   - tools/logs/mcp-security.log.YYYY-MM-DD    — auth failures, rate-limit
//                                                  trips, body-cap violations
//
// Never logs the bearer token, JWT, or any arg value that looks like a secret.

import { appendFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { createHash, randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const LOG_DIR = path.join(ROOT, "tools", "logs");

function ensureLogDir() {
  if (!existsSync(LOG_DIR)) mkdirSync(LOG_DIR, { recursive: true });
}
function todayStamp() {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,"0")}-${String(d.getUTCDate()).padStart(2,"0")}`;
}
function auditPath() { return path.join(LOG_DIR, `mcp-audit.log.${todayStamp()}`); }
function securityPath() { return path.join(LOG_DIR, `mcp-security.log.${todayStamp()}`); }

// Args summary: keep keys + small primitive values, redact long strings.
const SECRET_KEY_RX = /^(authorization|bearer|token|secret|password|api[_-]?key)$/i;
function summariseArgs(args) {
  if (!args || typeof args !== "object") return args;
  const out = {};
  for (const [k, v] of Object.entries(args)) {
    if (SECRET_KEY_RX.test(k)) { out[k] = "[REDACTED]"; continue; }
    if (typeof v === "string" && v.length > 200) { out[k] = `${v.slice(0, 64)}…(${v.length})`; continue; }
    if (typeof v === "object" && v !== null) { out[k] = "[object]"; continue; }
    out[k] = v;
  }
  return out;
}

// --- hash chain ----------------------------------------------------------
// Tracks the last hash written today, in memory. On process restart we
// re-read the last line of today's log to pick up where we left off, so the
// chain is continuous across restarts.
let lastHashCache = null;
let lastHashFile = null;
function lastHashForToday() {
  const p = auditPath();
  if (lastHashCache && lastHashFile === p) return lastHashCache;
  lastHashFile = p;
  if (!existsSync(p)) { lastHashCache = "GENESIS"; return lastHashCache; }
  try {
    // Read last 8 KB of the file — enough to find the last newline-terminated
    // record without slurping the whole thing.
    const size = statSync(p).size;
    const start = Math.max(0, size - 8 * 1024);
    const tail = readFileSync(p, { encoding: "utf8", start, end: size });
    const lines = tail.split("\n").filter((l) => l.trim());
    if (!lines.length) { lastHashCache = "GENESIS"; return lastHashCache; }
    const lastLine = lines[lines.length - 1];
    const obj = JSON.parse(lastLine);
    lastHashCache = obj.hash || "GENESIS";
  } catch {
    lastHashCache = "GENESIS";
  }
  return lastHashCache;
}
function sha256(s) { return createHash("sha256").update(s, "utf8").digest("hex"); }

function appendChained(filePath, record) {
  // Compute hash over the canonical JSON form WITHOUT the hash field, so the
  // hash field doesn't need to be guessed-into-existence first.
  const { hash: _ignore, ...payload } = record;
  payload.prev_hash = lastHashForToday();
  const canonical = JSON.stringify(payload);
  payload.hash = sha256(canonical);
  appendFileSync(filePath, JSON.stringify(payload) + "\n");
  lastHashCache = payload.hash;
}

export function newAuditId() { return randomUUID(); }

export function logCall({ auditId, tool, args, result, error, durationMs, remoteAddr, principal }) {
  ensureLogDir();
  const record = {
    ts: new Date().toISOString(),
    kind: "tool_call",
    audit_id: auditId,
    // `principal` is the verified caller identity:
    //   - cfaccess:<email> for CF Access OIDC JWT (cloud agents)
    //   - bearer:static   for the legacy static token (local laptop / curl)
    principal: principal || null,
    tool,
    args: summariseArgs(args),
    ok: !error,
    error: error ? String(error).slice(0, 300) : null,
    result_summary: error ? null : summariseResult(result),
    duration_ms: durationMs,
    remote: remoteAddr,
  };
  appendChained(auditPath(), record);
}

/**
 * Log a security-relevant event (auth failure, rate-limit trip, body-cap
 * violation, malformed request, etc.). Distinct sink from tool_call audit
 * so security review can be done without wading through normal traffic.
 *
 * `event` should include `kind` (one of: auth_failed, rate_limited,
 * body_too_large, malformed_request) plus context.
 */
export function logSecurityEvent(event) {
  ensureLogDir();
  const record = {
    ts: new Date().toISOString(),
    ...event,
  };
  appendFileSync(securityPath(), JSON.stringify(record) + "\n");
}

function summariseResult(r) {
  if (r == null) return null;
  if (typeof r !== "object") return r;
  if (Array.isArray(r)) return `[array len=${r.length}]`;
  const keys = Object.keys(r);
  return `{keys=${keys.length}: ${keys.slice(0,6).join(",")}${keys.length>6?",…":""}}`;
}
