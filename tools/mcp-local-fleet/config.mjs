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

// ---- Cloudflare Access OIDC (preferred auth for cloud agents) -----------
// When set, the server accepts JWTs signed by this CF Access SaaS app
// alongside the legacy static bearer token. claude.ai's MCP custom connector
// drives users through CF's OAuth Authorization Code flow and presents the
// resulting access token as `Authorization: Bearer <jwt>` on every call.
//
// Hardcoded defaults below correspond to the "Local Fleet MCP" CF Access
// SaaS app on the untool.cloudflareaccess.com team. Override per-instance
// with CF_ACCESS_ISSUER / CF_ACCESS_AUDIENCE / CF_ACCESS_EMAIL_ALLOWLIST envs.
export const CF_ACCESS_ISSUER = process.env.CF_ACCESS_ISSUER
  || "https://untool.cloudflareaccess.com/cdn-cgi/access/sso/oidc/dce8d3bc779a4c2fc3eaf015f3fdd339a4d0f34613ade8234d967839bacc7190";
// Audience (claude.ai sends OIDC client_id as aud). Leave empty until you've
// created the connector and have its client_id — then export it as env.
export const CF_ACCESS_AUDIENCE = process.env.CF_ACCESS_AUDIENCE || "";
// Comma-separated emails permitted to invoke tools via CF Access JWT.
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

// Two service tiers — see ARC-ADR-023 (container tiering). Platform services
// run in docker (logs via `docker logs <name>`); spoke processes are local
// node/python (logs via `tools/tail.mjs query --service <name>`).
export const ALLOWED_SERVICES = {
  // Spokes (local processes; backed by tail.mjs NDJSON)
  frontend: { tier: "spoke", logSource: "tail" },
  middle:   { tier: "spoke", logSource: "tail" },
  back:     { tier: "spoke", logSource: "tail" },
  // Platform containers (backed by docker logs)
  arcadedb:      { tier: "platform", logSource: "docker", container: "agentarmy-arcadedb" },
  postgres:      { tier: "platform", logSource: "docker", container: "agentarmy-postgres" },
  nats:          { tier: "platform", logSource: "docker", container: "agentarmy-nats" },
  "event-bridge":{ tier: "platform", logSource: "docker", container: "agentarmy-event-bridge" },
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
