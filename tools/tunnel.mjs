#!/usr/bin/env node
// AgentArmy dev tunnel wrapper — vendor-agnostic.
// Exposes a single `tunnel` surface (start/status/url/stop/logs) over
// pluggable backends so the agent and the human get the same commands
// regardless of which provider is underneath today (ngrok, cloudflared, …).
//
// Usage:
//   node tools/tunnel.mjs start [--vendor V] [--port P]
//   node tools/tunnel.mjs status
//   node tools/tunnel.mjs url
//   node tools/tunnel.mjs stop
//   node tools/tunnel.mjs logs [--lines N]
//
// Vendor priority (override with --vendor or TUNNEL_VENDOR env):
//   cloudflared > ngrok
// Default port: 3000 (frontend). Override with --port or TUNNEL_PORT.
//
// State (PID + public URL) is persisted to tools/.tunnel-state.json so
// `status` / `url` / `stop` work across shell invocations.
// Tunnel stdout/stderr appends to tools/logs/tunnel.log.YYYY-MM-DD (NDJSON
// where possible) so it slots into tail.mjs's query/clean pipeline.

import { spawn } from "node:child_process";
import {
  appendFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const LOG_DIR = path.join(ROOT, "tools", "logs");
const STATE = path.join(ROOT, "tools", ".tunnel-state.json");

const IS_WIN = process.platform === "win32";

// --- vendor discovery ---------------------------------------------------------
// Same auto-detect trick as tail.mjs: winget lands binaries in a deterministic
// per-package folder that isn't on PATH until shell restart. Override with
// NGROK_BIN / CLOUDFLARED_BIN env vars.
function ngrokBin() {
  return process.env.NGROK_BIN
    || (IS_WIN
        ? `${process.env.LOCALAPPDATA}\\Microsoft\\WinGet\\Packages\\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\\ngrok.exe`
        : "ngrok");
}
function cloudflaredBin() {
  if (process.env.CLOUDFLARED_BIN) return process.env.CLOUDFLARED_BIN;
  if (!IS_WIN) return "cloudflared";
  // The Cloudflare.cloudflared winget package installs into Program Files (x86),
  // NOT the per-user WinGet/Packages cache like ngrok does. Check both paths so
  // setup keeps working on machines where the install location varies.
  for (const candidate of [
    `${process.env["ProgramFiles(x86)"]}\\cloudflared\\cloudflared.exe`,
    `${process.env.ProgramFiles}\\cloudflared\\cloudflared.exe`,
    `${process.env.LOCALAPPDATA}\\Microsoft\\WinGet\\Packages\\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\\cloudflared.exe`,
  ]) {
    if (candidate && existsSync(candidate)) return candidate;
  }
  return "cloudflared"; // fall back to PATH (after shell restart)
}

// --- argv ---------------------------------------------------------------------
function parseArgs(argv) {
  const out = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) { out.flags[key] = next; i++; }
      else out.flags[key] = true;
    } else {
      out._.push(a);
    }
  }
  return out;
}
const ARGS = parseArgs(process.argv.slice(2));
const SUBCMD = ARGS._[0] || "status";

// --- state --------------------------------------------------------------------
// State shape (multi-tunnel aware):
//   { tunnels: { <name>: { vendor, pid, port, url, startedAt }, ... } }
// Legacy single-tunnel state ({vendor, pid, ...}) is auto-migrated as `frontend`.
function readState() {
  if (!existsSync(STATE)) return { tunnels: {} };
  try {
    const raw = JSON.parse(readFileSync(STATE, "utf8"));
    if (raw && typeof raw === "object" && raw.tunnels) return raw;
    if (raw && raw.pid) return { tunnels: { frontend: raw } }; // migration
    return { tunnels: {} };
  } catch { return { tunnels: {} }; }
}
function writeState(s) { writeFileSync(STATE, JSON.stringify(s, null, 2)); }
function setTunnel(name, entry) {
  const s = readState();
  s.tunnels[name] = entry;
  writeState(s);
}
function clearTunnel(name) {
  const s = readState();
  delete s.tunnels[name];
  if (Object.keys(s.tunnels).length === 0) {
    try { unlinkSync(STATE); } catch { /* ignore */ }
  } else {
    writeState(s);
  }
}

function pidAlive(pid) {
  try { process.kill(pid, 0); return true; }
  catch { return false; }
}

// Sensible default ports per named tunnel — keeps `tunnel start --name mcp`
// from needing --port. Override with --port at any time.
const DEFAULT_PORT = { frontend: 3000, mcp: 8765 };

// --- logging ------------------------------------------------------------------
function ensureLogDir() { if (!existsSync(LOG_DIR)) mkdirSync(LOG_DIR, { recursive: true }); }
function todayStamp() {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,"0")}-${String(d.getUTCDate()).padStart(2,"0")}`;
}
function logPath() { return path.join(LOG_DIR, `tunnel.log.${todayStamp()}`); }
function appendLog(record) {
  ensureLogDir();
  appendFileSync(logPath(), JSON.stringify(record) + "\n");
}

// --- vendor adapters ----------------------------------------------------------
// Each adapter returns: { cmd, args, parseLine(line) -> {url?, ready?} }
// parseLine reads one stdout/stderr line; if it contains the public URL we
// pluck it. ready=true once we believe the tunnel is serving traffic.

const VENDORS = {
  cloudflared: {
    available: () => true, // checked at spawn time via existsSync
    bin: cloudflaredBin,
    args: (port) => ["tunnel", "--no-autoupdate", "--url", `http://localhost:${port}`],
    // cloudflared writes a banner like:
    //   2026-05-27T02:00:00Z INF +--------------------------------------------------------------------------------------------+
    //   2026-05-27T02:00:00Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |
    //   2026-05-27T02:00:00Z INF |  https://random-words-xxxx.trycloudflare.com                                              |
    parseLine: (line) => {
      const m = line.match(/(https:\/\/[a-z0-9-]+\.trycloudflare\.com)/i);
      if (m) return { url: m[1], ready: true };
      return {};
    },
  },
  ngrok: {
    available: () => true,
    bin: ngrokBin,
    args: (port) => ["http", String(port), "--log=stdout", "--log-format=json"],
    // ngrok with --log-format=json emits structured records; we look for
    // {"msg":"started tunnel", "url":"https://…ngrok-free.dev"}
    parseLine: (line) => {
      try {
        const j = JSON.parse(line);
        if (j.msg === "started tunnel" && j.url) return { url: j.url, ready: true };
      } catch { /* not JSON, ignore */ }
      const m = line.match(/url=(https:\/\/[^\s"]+)/);
      if (m) return { url: m[1], ready: true };
      return {};
    },
  },
};

function pickVendor() {
  const forced = ARGS.flags.vendor || process.env.TUNNEL_VENDOR;
  if (forced) {
    if (!VENDORS[forced]) {
      console.error(`Unknown vendor: ${forced}. Known: ${Object.keys(VENDORS).join(", ")}`);
      process.exit(2);
    }
    return forced;
  }
  // Default priority: cloudflared first (free, stable), ngrok second.
  if (existsSync(cloudflaredBin())) return "cloudflared";
  if (existsSync(ngrokBin())) return "ngrok";
  return "cloudflared"; // optimistic; will error at spawn if missing
}

// --- subcommands --------------------------------------------------------------
async function cmdStart() {
  const name = ARGS.flags.name || "frontend";
  const state = readState();
  const existing = state.tunnels[name];
  if (existing && pidAlive(existing.pid)) {
    console.log(`already running: ${name} ${existing.vendor} pid=${existing.pid} url=${existing.url || "(provisioning)"}`);
    return;
  }
  if (existing) clearTunnel(name);

  const vendor = pickVendor();
  const port = ARGS.flags.port || process.env.TUNNEL_PORT || DEFAULT_PORT[name] || "3000";
  const adapter = VENDORS[vendor];
  const bin = adapter.bin();
  const args = adapter.args(port);

  if (!existsSync(bin) && bin.includes("\\")) {
    console.error(`${vendor} binary not found at: ${bin}`);
    console.error(`Install it (winget install ${vendor === "ngrok" ? "Ngrok.Ngrok" : "Cloudflare.cloudflared"}) or set ${vendor.toUpperCase()}_BIN.`);
    process.exit(1);
  }

  console.log(`starting tunnel '${name}' via ${vendor} → http://localhost:${port}`);
  const child = spawn(bin, args, {
    cwd: ROOT,
    detached: true,
    stdio: ["ignore", "pipe", "pipe"],
    shell: false,
  });
  child.unref();

  let url = null;
  const onLine = (line, source) => {
    appendLog({ ts: new Date().toISOString(), tunnel: name, vendor, source, msg: line.trim() });
    const parsed = adapter.parseLine(line);
    if (parsed.url && !url) {
      url = parsed.url;
      setTunnel(name, { vendor, pid: child.pid, port, url, startedAt: new Date().toISOString() });
      console.log(`url:  ${url}`);
      console.log(`pid:  ${child.pid}`);
      console.log(`logs: tools/logs/tunnel.log.${todayStamp()}`);
      console.log(`stop: node tools/tunnel.mjs stop --name ${name}`);
      // Detach this Node process so the tunnel survives.
      setTimeout(() => process.exit(0), 200);
    }
  };

  for (const [stream, source] of [[child.stdout, "stdout"], [child.stderr, "stderr"]]) {
    let buf = "";
    stream.on("data", (chunk) => {
      buf += chunk.toString("utf8");
      let idx;
      while ((idx = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, idx);
        buf = buf.slice(idx + 1);
        if (line.trim()) onLine(line, source);
      }
    });
  }

  child.on("exit", (code) => {
    if (!url) {
      console.error(`${vendor} exited (code ${code}) before publishing a URL — check tools/logs/tunnel.log.${todayStamp()}`);
      clearTunnel(name);
      process.exit(code || 1);
    }
  });

  // Provisioning timeout: 25s is enough for both vendors in healthy networks.
  setTimeout(() => {
    if (!url) {
      console.error(`${vendor} did not publish a URL within 25s — killing`);
      try { process.kill(child.pid); } catch { /* ignore */ }
      clearTunnel(name);
      process.exit(1);
    }
  }, 25_000);
}

function fmtTunnelRow(name, t) {
  const alive = pidAlive(t.pid);
  return `  ${name.padEnd(10)} ${t.vendor.padEnd(12)} pid=${String(t.pid).padEnd(6)} ${alive?"alive":"DEAD "} :${t.port}  ${t.url}`;
}

function cmdStatus() {
  const s = readState();
  const wanted = ARGS.flags.name;
  const entries = Object.entries(s.tunnels).filter(([n]) => !wanted || n === wanted);
  if (entries.length === 0) {
    console.log(wanted ? `tunnel '${wanted}' not running` : "no tunnels running");
    if (wanted) process.exitCode = 1;
    return;
  }
  console.log(`  ${"NAME".padEnd(10)} ${"VENDOR".padEnd(12)} ${"PID".padEnd(10)} STATE PORT  URL`);
  let anyDead = false;
  for (const [name, t] of entries) {
    console.log(fmtTunnelRow(name, t));
    if (!pidAlive(t.pid)) anyDead = true;
  }
  if (anyDead) process.exitCode = 1;
}

function cmdUrl() {
  const s = readState();
  const name = ARGS.flags.name || "frontend";
  const t = s.tunnels[name];
  if (!t) { console.error(`tunnel '${name}' not running`); process.exit(1); }
  if (!pidAlive(t.pid)) { console.error(`tunnel '${name}' state stale (pid ${t.pid} dead)`); process.exit(1); }
  console.log(t.url);
}

function cmdStop() {
  const s = readState();
  const all = ARGS.flags.all === true;
  const name = ARGS.flags.name;
  if (!all && !name) {
    // Backwards-compat: stop the frontend (or only tunnel) if no flags given.
    const names = Object.keys(s.tunnels);
    if (names.length === 0) { console.log("no tunnels running"); return; }
    if (names.length === 1) { return stopOne(names[0], s); }
    console.error(`multiple tunnels running (${names.join(", ")}) — use --name <n> or --all`);
    process.exit(2);
  }
  const targets = all ? Object.keys(s.tunnels) : [name];
  for (const n of targets) stopOne(n, s);
}
function stopOne(n, s) {
  const t = s.tunnels[n];
  if (!t) { console.log(`tunnel '${n}' not running`); return; }
  if (pidAlive(t.pid)) {
    try { process.kill(t.pid); console.log(`stopped '${n}' pid ${t.pid}`); }
    catch (e) { console.error(`kill ${t.pid} failed: ${e.message}`); process.exitCode = 1; }
  } else {
    console.log(`'${n}' already dead — clearing stale state`);
  }
  clearTunnel(n);
}

function cmdLogs() {
  const lines = parseInt(ARGS.flags.lines || "30", 10);
  const p = logPath();
  if (!existsSync(p)) { console.log(`no log yet: ${p}`); return; }
  const all = readFileSync(p, "utf8").trim().split("\n");
  for (const line of all.slice(-lines)) {
    try {
      const r = JSON.parse(line);
      console.log(`${r.ts}  [${r.source}]  ${r.msg}`);
    } catch { console.log(line); }
  }
}

function help() {
  console.log(`AgentArmy dev tunnel (tools/tunnel.mjs) — vendor-agnostic, multi-tunnel

  node tools/tunnel.mjs start [--name frontend] [--vendor cloudflared|ngrok] [--port N]
  node tools/tunnel.mjs status [--name N]         # one or all
  node tools/tunnel.mjs url    [--name N]         # just the URL (default: frontend)
  node tools/tunnel.mjs stop   [--name N | --all]
  node tools/tunnel.mjs logs   [--lines 30]      # tail today's tunnel log

  Named tunnels (default ports):
    frontend → :3000   (the Next.js app)
    mcp      → :8765   (local-fleet MCP control plane; see tools/mcp-local-fleet/)
    <anything else>    → must pass --port

  Default vendor: cloudflared if installed, else ngrok. Override with --vendor
  or TUNNEL_VENDOR env. State in tools/.tunnel-state.json (gitignored). Logs
  append to tools/logs/tunnel.log.YYYY-MM-DD (purged by tools/tail.mjs clean).

  Examples:
    node tools/tunnel.mjs start                      # bring up frontend
    node tools/tunnel.mjs start --name mcp           # second tunnel for MCP
    node tools/tunnel.mjs url --name mcp             # print MCP public URL
    node tools/tunnel.mjs stop --all                 # tear down everything
`);
}

switch (SUBCMD) {
  case "start":  await cmdStart(); break;
  case "status": cmdStatus(); break;
  case "url":    cmdUrl(); break;
  case "stop":   cmdStop(); break;
  case "logs":   cmdLogs(); break;
  case "help": case "--help": case "-h": help(); break;
  default:
    console.error(`unknown subcommand: ${SUBCMD}`);
    help();
    process.exit(2);
}
