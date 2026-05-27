#!/usr/bin/env node
// Rotate the static bearer token used by the local-fleet MCP server.
//
// What this does (in order):
//   1. Generate a fresh 48-char base64url token via CSPRNG.
//   2. Write it to Azure Key Vault (akv01-agentarmy/local-fleet-mcp-key).
//      The previous version stays in KV's version history — recover with
//      `az keyvault secret list-versions` if you need to roll back.
//   3. Update .claude/settings.local.json env block (gitignored) so the
//      local Claude Code session picks it up on next restart.
//   4. Print the new value ONCE so you can paste it into cloud-agent secret
//      stores (or routine prompts).
//   5. Print a kill command for the running MCP server so the operator
//      restarts it to invalidate the in-memory copy of the old token.
//
// When to rotate:
//   - You suspect a leak (token pasted into a public conversation, log,
//     screenshot, etc.).
//   - After a security incident, even precautionarily.
//   - On a schedule (quarterly recommended).
//
// What this does NOT do:
//   - Restart the MCP server for you (intentional — gives you the moment to
//     update cloud-agent configs first if needed).
//   - Touch CF Access OIDC. JWT auth path is separately managed by CF.
//   - Auto-update microVM / Codespace secrets. Each consumer environment
//     must be updated manually with the new value.

import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const SETTINGS_PATH = path.join(ROOT, ".claude", "settings.local.json");
const VAULT = process.env.MCP_VAULT || "akv01-agentarmy";
const SECRET_NAME = process.env.MCP_SECRET_NAME || "local-fleet-mcp-key";

// Same Windows az.cmd workaround as config.mjs.
const IS_WIN = process.platform === "win32";
function runAz(args, opts = {}) {
  if (IS_WIN) return execFileSync("cmd.exe", ["/c", "az", ...args], opts);
  return execFileSync(process.env.AZ_BIN || "az", args, opts);
}

function newToken() { return randomBytes(36).toString("base64url"); }

function writeToKv(token) {
  runAz([
    "keyvault", "secret", "set",
    "--vault-name", VAULT,
    "--name", SECRET_NAME,
    "--value", token,
    "--output", "none",
  ], { stdio: ["ignore", "ignore", "pipe"] });
}

function updateLocalSettings(token) {
  if (!existsSync(SETTINGS_PATH)) {
    console.log(`(skip local settings update — ${SETTINGS_PATH} doesn't exist)`);
    return;
  }
  const s = JSON.parse(readFileSync(SETTINGS_PATH, "utf8"));
  s.env = s.env || {};
  s.env.LOCAL_FLEET_MCP_TOKEN = token;
  writeFileSync(SETTINGS_PATH, JSON.stringify(s, null, 2) + "\n");
}

// --- main ---------------------------------------------------------------------
console.log(`rotating bearer token for ${VAULT}/${SECRET_NAME}…`);

const tok = newToken();
try {
  writeToKv(tok);
  console.log(`  ✓ written to KV (length ${tok.length})`);
} catch (e) {
  console.error(`  ✗ KV write failed: ${e.message}`);
  console.error("  Aborting — local settings NOT updated; old token still in use.");
  console.error("  Make sure `az login` is done and the identity has Set on this vault.");
  process.exit(1);
}

try {
  updateLocalSettings(tok);
  console.log(`  ✓ .claude/settings.local.json env updated`);
} catch (e) {
  console.error(`  ✗ local settings update failed: ${e.message}`);
  console.error("  KV is now ahead of local. Re-run, or manually update settings.");
  process.exit(2);
}

console.log("");
console.log("┌─────────────────────────────────────────────────────────────────┐");
console.log("│  NEW TOKEN — copy ONCE for cloud-agent configs                   │");
console.log("├─────────────────────────────────────────────────────────────────┤");
console.log(`│  ${tok}`);
console.log("└─────────────────────────────────────────────────────────────────┘");
console.log("");
console.log("Restart the MCP server to invalidate the in-memory old token:");
console.log("  1) find the listener:  netstat -ano | grep ':8765 '");
console.log("  2) taskkill //PID <pid> //F   (Windows) | kill <pid>  (POSIX)");
console.log("  3) restart:  node tools/mcp-local-fleet/server.mjs &");
console.log("");
console.log("Update consumer environments (each needs LOCAL_FLEET_MCP_TOKEN):");
console.log("  - cloud microVMs / Codespaces with the token in their secret store");
console.log("  - any /schedule routine prompts that inlined the token");
console.log("  - any external system using the static-bearer path");
console.log("");
console.log("Previous versions remain in KV history (rollback):");
console.log(`  az keyvault secret list-versions --vault-name ${VAULT} --name ${SECRET_NAME}`);
