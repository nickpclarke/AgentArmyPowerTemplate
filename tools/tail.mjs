#!/usr/bin/env node
// AgentArmy dev-log multiplexer.
// Spawn / tail / query / clean for the local fleet (frontend-core, middle-core,
// backend-core). Single-file, no deps, NDJSON on disk with daily rotation and
// a short TTL so e2e build-test loops can be debugged without drowning in logs.
//
// Usage:
//   node tools/tail.mjs                       # default: tail --all --follow
//   node tools/tail.mjs spawn [--service S]   # supervise dev servers, capture stdout
//   node tools/tail.mjs tail  [--service S]   # follow today's log files
//   node tools/tail.mjs query [opts]          # grep on-disk NDJSON
//   node tools/tail.mjs clean [--days N]      # purge logs older than N days (default 3)
//
// Query options:
//   --service front|middle|back|all  (repeatable)
//   --grep PATTERN                   (regex, case-insensitive)
//   --since 5m|2h|1d                 (relative window)
//   --level info|warn|error          (min level)
//   --limit N                        (default 200, --limit 0 = unlimited)
//
// Service registry assumes sibling repos under C:\Dev\. Override with:
//   FRONTEND_DIR=… MIDDLE_DIR=… BACKEND_DIR=…
//
// On every invocation we purge files older than --days (default 3).

import { spawn } from "node:child_process";
import {
  createReadStream,
  createWriteStream,
  existsSync,
  mkdirSync,
  readdirSync,
  statSync,
  unlinkSync,
  watch,
} from "node:fs";
import path from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const LOG_DIR = path.join(ROOT, "tools", "logs");
const RETENTION_DAYS_DEFAULT = 3;

const SIBLING_DEFAULTS = {
  front: process.env.FRONTEND_DIR || "C:/Dev/frontend-core",
  middle: process.env.MIDDLE_DIR || "C:/Dev/middle-core",
  back: process.env.BACKEND_DIR || "C:/Dev/backend-core",
};

// No shell. Argv arrays + platform-aware launchers so we avoid spawning a shell
// process (which would propagate current-shell settings; Semgrep CWE-78 / OS
// command injection). Use `python -m uvicorn` rather than the `uvicorn` shim so
// the launch works whether or not the Scripts/ directory is on PATH.
const IS_WIN = process.platform === "win32";
const NPM = IS_WIN ? "npm.cmd" : "npm";
const PY = IS_WIN ? "python" : "python3";
// ngrok winget install lands here on Windows but isn't on PATH until a shell
// restart. Auto-detect so `tail.mjs spawn --service ngrok` works without forcing
// the user to log out. NGROK_BIN env var overrides.
const NGROK = process.env.NGROK_BIN
  || (IS_WIN
      ? `${process.env.LOCALAPPDATA}\\Microsoft\\WinGet\\Packages\\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\\ngrok.exe`
      : "ngrok");

const SERVICES = {
  front: {
    name: "front", color: "36" /*cyan*/, port: 3000,
    cwd: SIBLING_DEFAULTS.front,
    cmd: NPM, args: ["run", "dev"],
  },
  middle: {
    name: "middle", color: "35" /*magenta*/, port: 8100,
    cwd: SIBLING_DEFAULTS.middle,
    // --factory because middle-core's Dockerfile uses create_app; --reload for dev.
    cmd: PY,
    args: ["-m", "uvicorn", "agent_runtime.app:create_app", "--factory",
           "--host", "127.0.0.1", "--port", "8100", "--reload"],
  },
  back: {
    name: "back", color: "32" /*green*/, port: 8000,
    cwd: SIBLING_DEFAULTS.back,
    cmd: PY,
    args: ["-m", "uvicorn", "app.main:app",
           "--host", "127.0.0.1", "--port", "8000", "--reload"],
  },
  // Public HTTPS for the frontend ONLY. Middle/back stay on localhost behind
  // the Next.js BFF (ARC-ADR-002 JWT injector). When external API monetisation
  // arrives, fronted by api-gateway-engineer (Azure APIM), not by a raw tunnel.
  // ngrok inspector lives at http://127.0.0.1:4040 — public URL appears there
  // and in stdout. Requires `ngrok config add-authtoken …` once.
  ngrok: {
    name: "ngrok", color: "33" /*yellow*/, port: 4040,
    cwd: ROOT,
    cmd: NGROK,
    args: ["http", "3000", "--log=stdout", "--log-format=json"],
  },
  // --- platform containers (logs come from `docker logs --follow`) ---
  // These services run inside Docker; spawning them is out of scope for
  // tail.mjs (use compose/agentarmy-doctor for lifecycle). We just want their
  // stdout in the same NDJSON pipeline so the MCP control plane and humans
  // can grep them with the same query commands.
  arcadedb:      { name: "arcadedb",      color: "34" /*blue*/,    dockerContainer: "agentarmy-arcadedb" },
  postgres:      { name: "postgres",      color: "32" /*green*/,   dockerContainer: "agentarmy-postgres" },
  nats:          { name: "nats",          color: "33" /*yellow*/,  dockerContainer: "agentarmy-nats" },
  "event-bridge":{ name: "event-bridge",  color: "35" /*magenta*/, dockerContainer: "agentarmy-event-bridge" },
};

// Whether a service entry should be launched as a local subprocess (cmd/args)
// or attached to via `docker logs --follow` (dockerContainer).
function isDockerService(svc) { return Boolean(svc?.dockerContainer); }

// ---------- tiny ANSI helpers (no deps) ----------
const isTTY = process.stdout.isTTY;
const ansi = (code, s) => (isTTY ? `\x1b[${code}m${s}\x1b[0m` : s);
const dim = (s) => ansi("2", s);
const red = (s) => ansi("31", s);
const yellow = (s) => ansi("33", s);
const cyan = (s) => ansi("36", s);

// ---------- argv ----------
function parseArgs(argv) {
  const out = { _: [], flags: {}, services: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      const hasVal = next !== undefined && !next.startsWith("--");
      if (key === "service" && hasVal) { out.services.push(next); i++; }
      else if (hasVal) { out.flags[key] = next; i++; }
      else out.flags[key] = true;
    } else {
      out._.push(a);
    }
  }
  return out;
}

const ARGS = parseArgs(process.argv.slice(2));
const SUBCMD = ARGS._[0] || "tail";

// ---------- log dir / rotation ----------
function ensureLogDir() {
  if (!existsSync(LOG_DIR)) mkdirSync(LOG_DIR, { recursive: true });
}
function todayStamp(d = new Date()) {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function logPathFor(service, stamp = todayStamp()) {
  return path.join(LOG_DIR, `${service}.log.${stamp}`);
}
function purgeOlderThan(days) {
  if (!existsSync(LOG_DIR)) return 0;
  const cutoff = Date.now() - days * 86400 * 1000;
  let removed = 0;
  for (const f of readdirSync(LOG_DIR)) {
    if (!/\.log\.\d{4}-\d{2}-\d{2}$/.test(f)) continue;
    const p = path.join(LOG_DIR, f);
    try {
      if (statSync(p).mtimeMs < cutoff) { unlinkSync(p); removed++; }
    } catch { /* ignore */ }
  }
  return removed;
}

// ---------- writer: per-service NDJSON appender with daily rotation ----------
function makeWriter(service) {
  let currentStamp = todayStamp();
  let stream = createWriteStream(logPathFor(service, currentStamp), { flags: "a" });
  return {
    write(record) {
      const stamp = todayStamp();
      if (stamp !== currentStamp) {
        stream.end();
        currentStamp = stamp;
        stream = createWriteStream(logPathFor(service, currentStamp), { flags: "a" });
      }
      stream.write(JSON.stringify(record) + "\n");
    },
    close() { stream.end(); },
  };
}

// ---------- line classifier ----------
// Best-effort level extraction from arbitrary stdout. Most uvicorn / Next lines
// contain a recognisable token; everything else gets a default level.
function classify(raw, defaultLevel = "info") {
  const u = raw.toUpperCase();
  if (/\b(ERROR|FATAL|CRITICAL|EXCEPTION|TRACEBACK|UNHANDLED|TERMINATED)\b/.test(u)) return "error";
  if (/\b(WARN|WARNING|DEPRECAT|RETRY|TIMEOUT|SLOW)\b/.test(u)) return "warn";
  if (/\b(DEBUG|TRACE)\b/.test(u)) return "debug";
  return defaultLevel;
}
const LEVEL_ORDER = { debug: 0, info: 1, warn: 2, error: 3 };

// Some lines already arrive as JSON (e.g. structured loggers). Try to parse so
// we preserve fields rather than re-wrapping them.
function recordFromLine(service, raw, source) {
  const trimmed = raw.replace(/\r$/, "");
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    try {
      const parsed = JSON.parse(trimmed);
      return {
        ts: parsed.ts || parsed.timestamp || new Date().toISOString(),
        service,
        level: parsed.level || classify(trimmed),
        msg: parsed.msg || parsed.message || trimmed,
        source,
        raw: parsed,
      };
    } catch { /* fall through to plain wrap */ }
  }
  return {
    ts: new Date().toISOString(),
    service,
    level: classify(trimmed, source === "stderr" ? "warn" : "info"),
    msg: trimmed,
    source,
  };
}

function fmtConsole(rec) {
  const svc = (SERVICES[rec.service]?.color)
    ? ansi(SERVICES[rec.service].color, rec.service.padEnd(6))
    : rec.service.padEnd(6);
  const t = rec.ts.slice(11, 19); // HH:MM:SS UTC
  const lvl = rec.level === "error" ? red("ERR")
            : rec.level === "warn" ? yellow("WRN")
            : rec.level === "debug" ? dim("DBG")
            : cyan("INF");
  return `${dim(t)} [${svc}] ${lvl} ${rec.msg}`;
}

// ---------- SUBCMD: spawn ----------
function pickServices() {
  if (ARGS.services.length === 0) return Object.keys(SERVICES);
  return ARGS.services.flatMap((s) => (s === "all" ? Object.keys(SERVICES) : [s]));
}

function runSpawn() {
  ensureLogDir();
  const purged = purgeOlderThan(Number(ARGS.flags.days) || RETENTION_DAYS_DEFAULT);
  if (purged) console.error(dim(`tail.mjs: purged ${purged} log file(s) older than retention`));

  const names = pickServices();
  const writers = new Map();
  const children = new Map();

  const shutdown = (signal) => {
    console.error(dim(`\ntail.mjs: caught ${signal}, stopping ${children.size} child process(es)`));
    for (const [name, child] of children) {
      try { child.kill("SIGTERM"); } catch { /* */ }
    }
    for (const w of writers.values()) w.close();
    process.exit(0);
  };
  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));

  for (const name of names) {
    const svc = SERVICES[name];
    if (!svc) { console.error(red(`unknown service: ${name}`)); continue; }

    const writer = makeWriter(name);
    writers.set(name, writer);

    // Two service shapes: local subprocess (cmd/args, has cwd) vs docker
    // attach (dockerContainer, no cwd needed). docker attach is just
    // `docker logs --follow <name>` — gives us the same NDJSON pipeline for
    // platform containers without us having to know how compose started them.
    let child;
    if (isDockerService(svc)) {
      console.error(dim(`tail.mjs: attaching to docker ${svc.dockerContainer} as service '${name}'`));
      child = spawn("docker", ["logs", "--follow", "--tail", "0", svc.dockerContainer], {
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
        shell: false,
      });
    } else {
      if (!existsSync(svc.cwd)) {
        console.error(yellow(`tail.mjs: skipping ${name} — ${svc.cwd} not found (set ${name.toUpperCase()}_DIR)`));
        continue;
      }
      console.error(dim(`tail.mjs: spawning ${name} (port ${svc.port}) in ${svc.cwd}`));
      // shell:false (default) — argv array is passed directly to the OS; no shell
      // expansion. Commands are hardcoded constants (no user input), but we still
      // avoid spawning a shell to keep this safe-by-construction.
      child = spawn(svc.cmd, svc.args, {
        cwd: svc.cwd,
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
        shell: false,
      });
    }
    children.set(name, child);

    const handleStream = (stream, source) => {
      const rl = createInterface({ input: stream, crlfDelay: Infinity });
      rl.on("line", (line) => {
        if (!line.trim()) return;
        const rec = recordFromLine(name, line, source);
        writer.write(rec);
        process.stdout.write(fmtConsole(rec) + "\n");
      });
    };
    handleStream(child.stdout, "stdout");
    handleStream(child.stderr, "stderr");

    child.on("exit", (code, signal) => {
      const msg = `process exited code=${code} signal=${signal || ""}`;
      const rec = { ts: new Date().toISOString(), service: name, level: code === 0 ? "info" : "error", msg, source: "supervisor" };
      writer.write(rec);
      process.stdout.write(fmtConsole(rec) + "\n");
      children.delete(name);
      if (children.size === 0) shutdown("all-children-exited");
    });
  }
}

// ---------- SUBCMD: tail ----------
function runTail() {
  ensureLogDir();
  const names = pickServices();
  const follow = ARGS.flags.follow !== false; // default true

  // Print last 50 lines from today's file (if any) per service, then watch.
  for (const name of names) {
    const file = logPathFor(name);
    if (!existsSync(file)) {
      console.error(dim(`tail.mjs: no log yet for ${name} at ${file}`));
      continue;
    }
    tailFile(file, name, /* fromStart */ false, /* follow */ follow);
  }
}

function tailFile(file, service, fromStart, follow) {
  let offset = 0;
  if (!fromStart) {
    try { offset = statSync(file).size; } catch { offset = 0; }
    // back up ~16KB so the user sees recent context on attach
    offset = Math.max(0, offset - 16 * 1024);
  }
  const read = () => {
    let size;
    try { size = statSync(file).size; } catch { return; }
    if (size <= offset) return;
    const stream = createReadStream(file, { start: offset, end: size - 1, encoding: "utf8" });
    offset = size;
    const rl = createInterface({ input: stream, crlfDelay: Infinity });
    rl.on("line", (line) => {
      if (!line.trim()) return;
      let rec;
      try { rec = JSON.parse(line); } catch { rec = { ts: new Date().toISOString(), service, level: "info", msg: line }; }
      rec.service = rec.service || service;
      process.stdout.write(fmtConsole(rec) + "\n");
    });
  };
  read();
  if (!follow) return;
  watch(file, { persistent: true }, () => read());
}

// ---------- SUBCMD: query ----------
function parseSince(spec) {
  if (!spec) return 0;
  const m = String(spec).match(/^(\d+)\s*(s|m|h|d)$/i);
  if (!m) return 0;
  const n = Number(m[1]);
  const unit = m[2].toLowerCase();
  const ms = { s: 1000, m: 60000, h: 3600000, d: 86400000 }[unit];
  return Date.now() - n * ms;
}

async function runQuery() {
  ensureLogDir();
  const names = pickServices();
  const sinceMs = parseSince(ARGS.flags.since);
  const grepRe = ARGS.flags.grep ? new RegExp(String(ARGS.flags.grep), "i") : null;
  const minLevel = ARGS.flags.level ? LEVEL_ORDER[String(ARGS.flags.level)] ?? 0 : 0;
  const limit = ARGS.flags.limit !== undefined ? Number(ARGS.flags.limit) : 200;

  // Walk yesterday + today (covers --since 1d cleanly without scanning everything).
  const days = [todayStamp(new Date(Date.now() - 86400 * 1000)), todayStamp()];
  const files = [];
  for (const name of names) {
    for (const stamp of days) {
      const p = logPathFor(name, stamp);
      if (existsSync(p)) files.push({ name, p });
    }
  }
  files.sort((a, b) => a.p.localeCompare(b.p)); // chronological

  const out = [];
  for (const { name, p } of files) {
    await new Promise((resolve) => {
      const rl = createInterface({ input: createReadStream(p, { encoding: "utf8" }), crlfDelay: Infinity });
      rl.on("line", (line) => {
        if (!line.trim()) return;
        let rec;
        try { rec = JSON.parse(line); } catch { return; }
        rec.service = rec.service || name;
        if (sinceMs && new Date(rec.ts).getTime() < sinceMs) return;
        if (grepRe && !grepRe.test(rec.msg || "")) return;
        const lvl = LEVEL_ORDER[rec.level] ?? 1;
        if (lvl < minLevel) return;
        out.push(rec);
      });
      rl.on("close", resolve);
    });
  }
  const sliced = limit > 0 ? out.slice(-limit) : out;
  for (const rec of sliced) process.stdout.write(fmtConsole(rec) + "\n");
  console.error(dim(`\n${sliced.length}/${out.length} record(s) shown`
    + (limit > 0 && out.length > sliced.length ? ` — raise --limit to see more` : "")));
}

// ---------- SUBCMD: clean ----------
function runClean() {
  ensureLogDir();
  const days = Number(ARGS.flags.days) || RETENTION_DAYS_DEFAULT;
  const removed = purgeOlderThan(days);
  console.error(`tail.mjs: purged ${removed} log file(s) older than ${days} day(s)`);
}

// ---------- help ----------
function printHelp() {
  const txt = `
AgentArmy dev-log multiplexer (tools/tail.mjs)

  node tools/tail.mjs                          default: tail --all --follow
  node tools/tail.mjs spawn [--service S]      supervise dev servers, capture stdout
  node tools/tail.mjs tail  [--service S]      follow today's NDJSON files
  node tools/tail.mjs query [opts]             grep on-disk NDJSON
  node tools/tail.mjs clean [--days N]         purge logs older than N days (default ${RETENTION_DAYS_DEFAULT})

Services: front (3000), middle (8100), back (8000) — sibling repos auto-detected.
Override paths with FRONTEND_DIR / MIDDLE_DIR / BACKEND_DIR env vars.

Query options:
  --service front|middle|back|all    (repeatable; default: all)
  --grep PATTERN                     case-insensitive regex over msg
  --since 5m|2h|1d                   relative window
  --level info|warn|error            min level
  --limit N                          tail-most-recent N (default 200, 0 = unlimited)

Logs live in tools/logs/ as {service}.log.YYYY-MM-DD (NDJSON, daily rotation).
Every invocation purges files older than the retention (default ${RETENTION_DAYS_DEFAULT} days).
`;
  process.stdout.write(txt.trimEnd() + "\n");
}

// ---------- dispatch ----------
async function main() {
  if (ARGS.flags.help || ARGS._[0] === "help") { printHelp(); return; }
  // Always tick the broom on every invocation (cheap).
  ensureLogDir();
  purgeOlderThan(Number(ARGS.flags.days) || RETENTION_DAYS_DEFAULT);

  switch (SUBCMD) {
    case "spawn": runSpawn(); break;
    case "tail":  runTail();  break;
    case "query": await runQuery(); break;
    case "clean": runClean(); break;
    default:
      // bare invocation => tail
      runTail();
  }
}

main().catch((err) => {
  console.error(red(`tail.mjs: ${err?.stack || err}`));
  process.exit(1);
});
