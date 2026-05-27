// Multi-token bearer registry — app-layer "service tokens" for cloud agents.
//
// Why this exists:
//   - One shared bearer means revoking access for one cloud agent revokes
//     every agent. Bad blast radius when a token leaks.
//   - True CF Access service tokens (edge-enforced) require CF Access
//     Application enforcement on mcp.untool.ai — a separate CF dashboard
//     re-architecture. This is the app-layer equivalent until then.
//
// How it works:
//   - At startup, enumerate all KV secrets in `akv01-agentarmy` whose name
//     matches `local-fleet-mcp-token-*` PLUS the legacy `local-fleet-mcp-key`.
//   - Each becomes a labelled bearer: name = token-id-for-audit.
//   - checkAuth tries every token, constant-time compare.
//   - Audit log records `principal: token:<name>` so every call is
//     attributable to a specific cloud-agent identity.
//
// Revocation:
//   - `az keyvault secret delete --vault-name akv01-agentarmy --name local-fleet-mcp-token-<name>`
//   - Server picks up the change on next restart (no live re-read for
//     simplicity — KV-list-on-every-request would dominate latency).
//
// Adding a new agent token:
//   - `az keyvault secret set --vault-name akv01-agentarmy --name local-fleet-mcp-token-claude-routine-1 --value $(openssl rand -base64 36 | tr -d /+= | head -c 48)`
//   - Restart the MCP server. Token is now accepted.

import { execFileSync } from "node:child_process";
import { timingSafeEqual } from "node:crypto";

import { VAULT } from "./config.mjs";

const TOKEN_PREFIX = "local-fleet-mcp-token-";
const LEGACY_NAME  = "local-fleet-mcp-key";

const IS_WIN = process.platform === "win32";
function runAz(args, opts = {}) {
  if (IS_WIN) return execFileSync("cmd.exe", ["/c", "az", ...args], opts);
  return execFileSync(process.env.AZ_BIN || "az", args, opts);
}

/**
 * Enumerate all bearer tokens for this server instance. Called once at
 * server startup. Returns { name: Buffer("Bearer <token>") } map.
 *
 * Includes the legacy `local-fleet-mcp-key` as identity "static-legacy" for
 * backwards compat — existing curl tests and consumers don't break.
 */
export function loadAllTokens() {
  const tokens = new Map();

  // Always include the legacy key first.
  try {
    const legacy = runAz([
      "keyvault", "secret", "show",
      "--vault-name", VAULT,
      "--name", LEGACY_NAME,
      "--query", "value", "-o", "tsv",
    ], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
    if (legacy) tokens.set("static-legacy", Buffer.from(`Bearer ${legacy}`, "utf8"));
  } catch { /* legacy might not exist — that's fine */ }

  // Now list all secrets matching the per-agent token prefix.
  try {
    const listOut = runAz([
      "keyvault", "secret", "list",
      "--vault-name", VAULT,
      "--query", `[?starts_with(name, '${TOKEN_PREFIX}')].name`,
      "-o", "tsv",
    ], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
    if (listOut) {
      for (const name of listOut.split("\n").map((s) => s.trim()).filter(Boolean)) {
        try {
          const val = runAz([
            "keyvault", "secret", "show",
            "--vault-name", VAULT,
            "--name", name,
            "--query", "value", "-o", "tsv",
          ], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
          if (val) {
            const principalName = name.slice(TOKEN_PREFIX.length) || name;
            tokens.set(principalName, Buffer.from(`Bearer ${val}`, "utf8"));
          }
        } catch { /* skip individual fetch failures */ }
      }
    }
  } catch (e) {
    // KV list failed — not fatal if legacy was loaded. Server can still run
    // with just the legacy token.
    if (tokens.size === 0) {
      throw new Error(`failed to load any tokens from KV ${VAULT}: ${e.message}`);
    }
  }

  return tokens;
}

/**
 * Verify an Authorization header against the loaded token registry.
 * Returns { matched: true, principal: "token:<name>" } on success;
 *         { matched: false } otherwise.
 *
 * Constant-time on each compare; length pre-check avoids the throw path.
 */
export function verifyAgainstRegistry(authHeader, registry) {
  if (!authHeader) return { matched: false };
  const buf = Buffer.from(authHeader, "utf8");
  for (const [name, expected] of registry) {
    if (buf.length !== expected.length) continue;
    try {
      if (timingSafeEqual(buf, expected)) {
        return { matched: true, principal: `token:${name}` };
      }
    } catch { /* skip */ }
  }
  return { matched: false };
}
