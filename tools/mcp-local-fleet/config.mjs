// Config + bearer-token bootstrap for the local-fleet MCP server.
//
// Token flow (user picked auto-generate + KV write on first run):
//   1. Try to read KV secret `local-fleet-mcp-key` via `az keyvault secret show`.
//   2. If missing, generate 48 bytes of CSPRNG → base64url, write to KV via
//      `az keyvault secret set`, and PRINT IT ONCE so the operator can copy
//      into cloud-agent configs. Subsequent starts re-read silently.
//   3. Token lives in memory only after that; never logged.
//
// Allowlist: cloud agents can only name services from this set. Adding new
// services is an explicit code change here — the API surface refuses to do
// anything to unknown names.

import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";

// Repo root, resolved from this file's location (cwd-independent).
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

export const PORT = parseInt(process.env.MCP_PORT || "8765", 10);
export const HOST = process.env.MCP_HOST || "127.0.0.1"; // never bind 0.0.0.0; tunnel exposes
export const VAULT = process.env.MCP_VAULT || "akv01-agentarmy";
export const SECRET_NAME = process.env.MCP_SECRET_NAME || "local-fleet-mcp-key";

// Deployment-environment label for THIS server instance. Cloud agents see it
// in tools/list `_meta.target` and pick the right server for the workload.
// Today's only instance: `local-home` (Nicky's office PC docker host reached
// via the cloudflared tunnel at mcp.untool.ai). Same code can power a
// `dev-cloud` instance pointed at an Azure VM tomorrow — just set MCP_TARGET.
//
// Taxonomy (live + planned):
//   local-home   — operator's personal dev box (a PC in their office). Today.
//   local-runner — a self-hosted runner box on the operator's LAN.
//   dev-cloud    — Azure / ACA / GCP dev VM speaking docker.
//   test-cloud   — same shape but the test environment.
//   prod-edge    — edge nodes (very narrow tool surface; build/deploy only).
//
// Optional per-tool narrowing: a tool can declare `availableOn: ["dev-cloud"]`
// to refuse to be exposed for other instance targets. Default = any.
export const INSTANCE_TARGET = process.env.MCP_TARGET || "local-home";

// ---- Cloudflare Access edge enforcement (Self-Hosted Application) -------
// CF Access is configured as an Access Application gating mcp.untool.ai/*.
// It enforces auth at the edge — user (email PIN or Managed OAuth via
// claude.ai Connector), service token (CF-Access-Client-Id/Secret headers
// for cloud microVMs), or cloudflared access curl. After it authenticates
// the principal, it injects `Cf-Access-Jwt-Assertion` on forwarded
// requests, which we verify in cfaccess-edge.mjs for defense-in-depth +
// identity attribution.
//
// Setup steps:
//   1. CF Zero Trust → Access → Applications → Add → Self-hosted
//   2. Domain: mcp.untool.ai (or mcp.untool.ai/mcp* path-scoped)
//   3. (For claude.ai web-UI Connector) Advanced settings →
//      oauth_configuration.enabled + dynamic_client_registration with
//      allowed_uris: ["https://claude.ai/*"]. Memory:
//      cf-managed-oauth-for-mcp.
//   4. Note the application's AUD tag — set as CF_ACCESS_EDGE_APP_AUD env
//   5. Team domain is `untool.cloudflareaccess.com`
export const CF_ACCESS_EDGE_TEAM_DOMAIN = process.env.CF_ACCESS_EDGE_TEAM_DOMAIN
  || "untool.cloudflareaccess.com";
// MUST be set before edge enforcement is meaningful — without it, any CF
// Access user on the team domain could call us. Empty by default to keep
// existing behavior while the CF dashboard side is being set up.
export const CF_ACCESS_EDGE_APP_AUD = process.env.CF_ACCESS_EDGE_APP_AUD || "";

// Defense-in-depth email allowlist applied by cfaccess-edge.mjs after JWT
// signature + issuer + audience verification pass. CF Access already
// enforces email policy at the edge, so this is the second wall — useful
// if an operator misconfigures the CF Access policy. Comma-separated.
export const CF_ACCESS_EMAIL_ALLOWLIST = (
  process.env.CF_ACCESS_EMAIL_ALLOWLIST || "nick@livecreative.com"
).split(",").map((s) => s.trim()).filter(Boolean);

// Azure CLI on Windows is `az.cmd` (a batch wrapper). Node 18+ refuses to
// spawn .cmd/.bat directly (CVE-2024-27980); the workaround is to route
// through cmd.exe explicitly. shell:false stays — no expansion of our args.
const IS_WIN = process.platform === "win32";

function runAz(args, opts = {}) {
  if (IS_WIN) {
    return execFileSync("cmd.exe", ["/c", "az", ...args], opts);
  }
  return execFileSync(process.env.AZ_BIN || "az", args, opts);
}

// ---- Allowlist (auto-enrolling) --------------------------------------------
// Two service tiers — see ARC-ADR-023 (container tiering). Platform services
// run in docker (logs via `docker logs <name>`); spoke processes are local
// node/python (logs via `tools/tail.mjs query --service <name>`).
//
// The allowlist AUTO-DERIVES from the fleet's own declared roster so a NEW
// fleet member gets access the moment its manifest merges — no edit here:
//   1. templates/local-stack/docker-compose.yml — authoritative for runnable
//      platform services (real service + container names; build/up-capable).
//   2. templates/*/image.json — the full fleet roster (adds function-tier
//      images not in local-stack: forge, hmac-verify, jwt-introspect, ...).
//   3. SPOKES — local node/python processes (no image.json).
// SECURITY: this is NOT caller input — it's the repo's own code-reviewed
// manifests + compose, so the invariant "allowlist = fleet-declared services
// only" holds exactly as before; we've only removed the duplicate hand-edit.
// CORE_FALLBACK guarantees the original platform set always resolves even if
// discovery hiccups (a parse error can never *remove* access).

const SPOKES = {
  frontend: { tier: "spoke", logSource: "tail" },
  middle:   { tier: "spoke", logSource: "tail" },
  back:     { tier: "spoke", logSource: "tail" },
};

const CORE_FALLBACK = {
  arcadedb:       { tier: "platform", logSource: "docker", container: "agentarmy-arcadedb" },
  postgres:       { tier: "platform", logSource: "docker", container: "agentarmy-postgres" },
  nats:           { tier: "platform", logSource: "docker", container: "agentarmy-nats" },
  "event-bridge": { tier: "platform", logSource: "docker", container: "agentarmy-event-bridge" },
};

// image.json short-name → compose service name, where the repo disagrees.
const COMPOSE_ALIAS = { "fuseki-ontology": "fuseki" };

function discoverFleetServices() {
  const svc = {};

  // 1. local-stack compose — authoritative service + container names.
  try {
    const compose = readFileSync(
      join(REPO_ROOT, "templates", "local-stack", "docker-compose.yml"), "utf8");
    let cur = null;
    for (const line of compose.split("\n")) {
      const s = line.match(/^ {2}([a-z][a-z0-9-]+):\s*$/);
      if (s) { cur = s[1]; continue; }
      const c = line.match(/^\s+container_name:\s*(\S+)/);
      if (c && cur) svc[cur] = { tier: "platform", logSource: "docker", container: c[1] };
    }
  } catch { /* compose optional — CORE_FALLBACK covers the platform set */ }

  // 2. templates/*/image.json — auto-enroll every declared image.
  try {
    const tdir = join(REPO_ROOT, "templates");
    for (const e of readdirSync(tdir, { withFileTypes: true })) {
      if (!e.isDirectory()) continue;
      const mf = join(tdir, e.name, "image.json");
      if (!existsSync(mf)) continue;
      let m; try { m = JSON.parse(readFileSync(mf, "utf8")); } catch { continue; }
      let key = String(m.name || e.name).replace(/^agentarmy-/, "");
      key = COMPOSE_ALIAS[key] || key;
      if (svc[key]) continue; // compose already defined it (authoritative)
      svc[key] = {
        tier: m.tier || "function",
        logSource: "docker",
        container: m.name || `agentarmy-${key}`,
      };
    }
  } catch { /* templates optional */ }

  return svc;
}

export const ALLOWED_SERVICES = {
  ...CORE_FALLBACK,
  ...discoverFleetServices(),
  ...SPOKES,
};

export function resolveBearerToken() {
  // Returns the token string. Side-effects: prints to console once on first
  // generation. Throws if `az` isn't available — operator must install / log in.
  try {
    const out = runAz([
      "keyvault", "secret", "show",
      "--vault-name", VAULT,
      "--name", SECRET_NAME,
      "--query", "value", "-o", "tsv",
    ], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
    if (out) return out;
  } catch {
    // Likely "secret not found" — fall through to generate.
  }

  // Generate + persist.
  const tok = randomBytes(36).toString("base64url"); // 48 chars
  try {
    runAz([
      "keyvault", "secret", "set",
      "--vault-name", VAULT,
      "--name", SECRET_NAME,
      "--value", tok,
      "--output", "none",
    ], { stdio: ["ignore", "ignore", "pipe"] });
  } catch (e) {
    throw new Error(`Failed to write KV secret '${SECRET_NAME}' in vault '${VAULT}': ${e.message}\nMake sure 'az login' is done and the identity has Set on this vault.`);
  }
  console.log("");
  console.log("┌─────────────────────────────────────────────────────────────────┐");
  console.log("│ local-fleet MCP token created (copy ONCE for cloud-agent configs)│");
  console.log("├─────────────────────────────────────────────────────────────────┤");
  console.log(`│ ${tok}`);
  console.log("├─────────────────────────────────────────────────────────────────┤");
  console.log(`│ also stored in KV: ${VAULT} secret '${SECRET_NAME}'`);
  console.log("│ retrievable any time:                                            │");
  console.log(`│   az keyvault secret show --vault-name ${VAULT} \\`);
  console.log(`│     --name ${SECRET_NAME} --query value -o tsv`);
  console.log("└─────────────────────────────────────────────────────────────────┘");
  console.log("");
  return tok;
}
