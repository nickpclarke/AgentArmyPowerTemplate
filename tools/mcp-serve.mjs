#!/usr/bin/env node
// mcp-serve — reconcile the declarative MCP registry (tools/mcp-registry.json) into a
// live, persistent serving plane for BOTH cloud and local Claudes. For each server it
// ensures: (1) a tunnel ingress path on mcp.untool.ai → 127.0.0.1:<port> (reusing the
// existing CF Access app + service tokens — never a new subdomain/app), (2) a persistent
// AgentArmy-* logon Scheduled Task, and (3) the .mcp.json block (local + cloud).
//
//   node tools/mcp-serve.mjs list                 # registry + derived routing
//   node tools/mcp-serve.mjs status               # live: task state + port reachability
//   node tools/mcp-serve.mjs reconcile            # DRY-RUN (default): show the plan, change nothing
//   node tools/mcp-serve.mjs reconcile --apply     # apply: ingress + tasks + emit .mcp.json
//
// The aggressive add-and-use loop: append a server row, `reconcile --apply`, and it is
// live + persistent + reachable cloud+local. See memory feedback_serve_capabilities_via_mcp.
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";
import net from "node:net";
import path from "node:path";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const HOME = homedir();
const AGENT_DIR = path.join(HOME, ".agentarmy");

const CF = {
  account: process.env.CF_ACCOUNT_ID || "83c22623f5df9f4f7829061c1bdabe0a",
  tunnel: process.env.CF_TUNNEL_ID || "a713c7c2-217f-4449-9809-249499e3d294",
  vault: process.env.MCP_VAULT || "akv01-agentarmy",
  tokenSecret: process.env.CF_DNS_TOKEN_SECRET || "Cf-access-dns",
};

const C = { reset: "\x1b[0m", dim: "\x1b[2m", green: "\x1b[32m", yellow: "\x1b[33m", red: "\x1b[31m", cyan: "\x1b[36m" };
const log = (s = "") => process.stdout.write(s + "\n");
const ok = (s) => log(`${C.green}✓${C.reset} ${s}`);
const plan = (s) => log(`${C.yellow}→${C.reset} ${s}`);
const die = (s) => { log(`${C.red}✗ ${s}${C.reset}`); process.exit(1); };

let _python, _node = process.execPath;
function which(bin) { try { return execFileSync("where", [bin], { encoding: "utf8" }).split(/\r?\n/)[0].trim(); } catch { return bin; } }
function python() { return (_python ||= which("python")); }

function resolve(str) {
  return String(str)
    .replaceAll("${REPO}", REPO).replaceAll("${HOME}", HOME)
    .replaceAll("${PYTHON}", python()).replaceAll("${NODE}", _node);
}

function loadRegistry() {
  const p = path.join(REPO, "tools", "mcp-registry.json");
  if (!existsSync(p)) die(`no registry at ${p}`);
  const reg = JSON.parse(readFileSync(p, "utf8"));
  reg.hostname ||= "mcp.untool.ai";
  for (const s of reg.servers) {
    s.taskName ||= `AgentArmy-MCP-${s.name}`;
    s._launcher = resolve(s.launcher || path.join(AGENT_DIR, `serve-mcp-${s.name}.cmd`));
    s._generate = !s.launcher; // generate a launcher only when none was supplied
  }
  return reg;
}

function cfToken() {
  try {
    // `az` is az.cmd on Windows — run via cmd.exe so PATHEXT resolves it (execFileSync can't exec a .cmd directly).
    return execFileSync("cmd", ["/c", "az", "keyvault", "secret", "show", "--vault-name", CF.vault, "--name", CF.tokenSecret, "--query", "value", "-o", "tsv"], { encoding: "utf8" }).trim();
  } catch (e) { die(`could not read CF token (${CF.tokenSecret}) from Key Vault: ${e.message}`); }
}
async function cfApi(p, method = "GET", body) {
  const res = await fetch(`https://api.cloudflare.com/client/v4${p}`, {
    method, headers: { Authorization: `Bearer ${cfToken()}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await res.json();
  if (!j.success) die(`CF API ${method} ${p} failed: ${JSON.stringify(j.errors)}`);
  return j.result;
}

function ps(script) { return execFileSync("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script], { encoding: "utf8" }); }

// ── ingress ────────────────────────────────────────────────────────────────
// Desired mcp.<host> rules: a path rule per non-default server (path before default),
// then the no-path default (host catch). Non-mcp host rules + the 404 catch-all are
// preserved verbatim.
function desiredMcpRules(reg) {
  const rules = [];
  for (const s of reg.servers.filter((x) => !x.default && x.path))
    rules.push({ hostname: reg.hostname, path: `^${s.path}`, service: `http://localhost:${s.port}` });
  const def = reg.servers.find((x) => x.default);
  if (def) rules.push({ hostname: reg.hostname, service: `http://localhost:${def.port}` });
  return rules;
}
const sig = (r) => `${r.path || ""}=>${r.service}`;
function sameRules(a, b) {
  return JSON.stringify(a.map(sig).sort()) === JSON.stringify(b.map(sig).sort());
}

async function reconcileIngress(reg, apply) {
  const cur = await cfApi(`/accounts/${CF.account}/cfd_tunnel/${CF.tunnel}/configurations`);
  const ingress = cur.config.ingress;
  const existingMcp = ingress.filter((r) => r.hostname === reg.hostname);
  const desired = desiredMcpRules(reg);
  if (sameRules(existingMcp, desired)) { ok(`ingress: ${reg.hostname} routes match registry (${desired.length} rule(s))`); return; }
  plan(`ingress: ${reg.hostname} routes differ — rebuilding ${desired.length} rule(s):`);
  for (const r of desired) plan(`    ${(r.path || "(default)").padEnd(14)} -> ${r.service}`);
  if (!apply) return;
  const preserved = ingress.filter((r) => r.hostname && r.hostname !== reg.hostname);
  const catchAll = ingress.find((r) => !r.hostname) || { service: "http_status:404" };
  const newIngress = [...preserved, ...desired, catchAll];
  mkdirSync(path.join(REPO, "tmp"), { recursive: true });
  writeFileSync(path.join(REPO, "tmp", "tunnel-config-before-reconcile.json"), JSON.stringify(cur, null, 2));
  const newConfig = { ...cur.config, ingress: newIngress };
  await cfApi(`/accounts/${CF.account}/cfd_tunnel/${CF.tunnel}/configurations`, "PUT", { config: newConfig });
  ok(`ingress updated (backup: tmp/tunnel-config-before-reconcile.json)`);
}

// ── tasks ────────────────────────────────────────────────────────────────
function taskState(name) {
  try { return ps(`(Get-ScheduledTask -TaskName '${name}' -ErrorAction Stop).State`).trim(); } catch { return null; }
}
function generateLauncher(s) {
  const lines = ["@echo off", `REM Generated by tools/mcp-serve.mjs for MCP '${s.name}'. Edit the registry + reconcile, not this file.`];
  for (const [k, v] of Object.entries(s.env || {})) lines.push(`set "${k}=${resolve(v)}"`);
  if (s.cwd) lines.push(`cd /d "${resolve(s.cwd)}"`);
  lines.push(resolve(s.run));
  mkdirSync(AGENT_DIR, { recursive: true });
  writeFileSync(s._launcher, lines.join("\r\n") + "\r\n");
}
function reconcileTask(s, apply) {
  const state = taskState(s.taskName);
  const launcherOk = existsSync(s._launcher);
  if (s._generate && (!launcherOk || apply)) { if (apply) { generateLauncher(s); } else { plan(`task ${s.taskName}: would generate launcher ${s._launcher}`); } }
  if (!s._generate && !launcherOk) { plan(`${C.red}task ${s.taskName}: launcher missing: ${s._launcher} (write it, then reconcile)${C.reset}`); if (!apply) return; }
  if (state === "Running") { ok(`task ${s.taskName}: Running`); return; }
  if (state && !apply) { plan(`task ${s.taskName}: ${state} → would Start`); return; }
  if (!state && !apply) { plan(`task ${s.taskName}: not registered → would register (logon, restart-on-failure) + Start`); return; }
  // apply:
  const arg = `-NoProfile -WindowStyle Hidden -Command "& '${s._launcher}'"`;
  const reg = [
    `$u="$env:USERDOMAIN\\$env:USERNAME"`,
    `$a=New-ScheduledTaskAction -Execute "powershell.exe" -Argument '${arg.replace(/'/g, "''")}'`,
    `$t=New-ScheduledTaskTrigger -AtLogOn -User $u`,
    `$s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew`,
    `$p=New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Limited`,
    `Register-ScheduledTask -TaskName '${s.taskName}' -Force -Action $a -Trigger $t -Settings $s -Principal $p | Out-Null`,
    `Start-ScheduledTask -TaskName '${s.taskName}'`,
  ].join("; ");
  ps(reg);
  ok(`task ${s.taskName}: registered + started`);
}

// ── .mcp.json emit ────────────────────────────────────────────────────────
function mcpBlock(reg) {
  const servers = {};
  for (const s of reg.servers) {
    const ROUTE = s.default ? "/mcp" : s.path;
    const UP = s.name.toUpperCase().replaceAll("-", "_");
    const headers = {};
    if (s.auth === "bearer") headers.Authorization = `Bearer \${${UP}_MCP_TOKEN}`;
    headers["CF-Access-Client-Id"] = "${CF_ACCESS_CLIENT_ID}";
    headers["CF-Access-Client-Secret"] = "${CF_ACCESS_CLIENT_SECRET}";
    servers[s.name] = { type: "http", url: `\${${UP}_MCP_URL:-http://127.0.0.1:${s.port}${ROUTE}}`, headers };
  }
  return { mcpServers: servers };
}

// ── commands ────────────────────────────────────────────────────────────
function cmdList(reg) {
  log(`${C.cyan}MCP registry${C.reset}  host=${reg.hostname}  (${reg.servers.length} server(s))`);
  for (const s of reg.servers) {
    const route = s.default ? "(default /mcp + /healthz)" : s.path;
    log(`  ${C.cyan}${s.name.padEnd(14)}${C.reset} :${s.port}  ${String(route).padEnd(26)} auth=${s.auth.padEnd(6)} task=${s.taskName}`);
    log(`    ${C.dim}cloud: https://${reg.hostname}${s.default ? "/mcp" : s.path}  •  ${s.description || ""}${C.reset}`);
  }
}
function portUp(port) {
  return new Promise((res) => { const sock = net.connect({ host: "127.0.0.1", port, timeout: 1500 }, () => { sock.destroy(); res(true); }); sock.on("error", () => res(false)); sock.on("timeout", () => { sock.destroy(); res(false); }); });
}
async function cmdStatus(reg) {
  log(`${C.cyan}MCP serving status${C.reset}`);
  for (const s of reg.servers) {
    const state = taskState(s.taskName) || "—";
    const up = await portUp(s.port);
    const mark = state === "Running" && up ? C.green + "✓" : C.red + "✗";
    log(`  ${mark}${C.reset} ${s.name.padEnd(14)} task=${state.padEnd(10)} :${s.port} ${up ? "listening" : C.red + "DOWN" + C.reset}`);
  }
}
async function cmdReconcile(reg, apply) {
  log(`${C.cyan}reconcile${C.reset} ${apply ? C.yellow + "(APPLY)" + C.reset : C.dim + "(dry-run — pass --apply to change anything)" + C.reset}`);
  await reconcileIngress(reg, apply);
  for (const s of reg.servers) reconcileTask(s, apply);
  const block = mcpBlock(reg);
  const out = path.join(REPO, "tools", "mcp-registry.generated.mcp.json");
  if (apply) { writeFileSync(out, JSON.stringify(block, null, 2) + "\n"); ok(`.mcp.json block written: ${path.relative(REPO, out)} (copy into consumers' .mcp.json)`); }
  else { plan(`.mcp.json block (preview):`); log(JSON.stringify(block, null, 2)); }
}

const cmd = process.argv[2] || "help";
const apply = process.argv.includes("--apply");
const reg = ["help", "-h", "--help"].includes(cmd) ? null : loadRegistry();
if (cmd === "list") cmdList(reg);
else if (cmd === "status") await cmdStatus(reg);
else if (cmd === "reconcile") await cmdReconcile(reg, apply);
else log(`mcp-serve — declarative MCP serving plane\n\n  list                 registry + derived routing\n  status               live task state + port reachability\n  reconcile [--apply]  ensure tunnel ingress + persistent tasks + emit .mcp.json (dry-run unless --apply)\n`);
