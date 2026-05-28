#!/usr/bin/env node
// monitor.mjs — AgentArmy health monitor: probe → grade → alert → remediate.
//
// Watches the things that have actually halted this dev box before (the Windows
// drive filling up because the Docker/WSL ext4.vhdx grows without bound), warns
// before it's fatal, and on a CRITICAL disk situation auto-reclaims safe Docker
// space (build cache + dangling images + stopped containers — never volumes).
//
// Runs three ways (see docs/health-monitoring.md):
//   • a Windows Scheduled Task every ~15 min (continuous protection)   ← primary
//   • the Claude Code SessionStart hook (status surface, no remediation)
//   • ad-hoc / on a /loop
//
// Usage:
//   node tools/health/monitor.mjs                # one pass, render readings
//   node tools/health/monitor.mjs --json         # machine-readable
//   node tools/health/monitor.mjs --quiet        # only emit on an alert (scheduled task)
//   node tools/health/monitor.mjs --session      # quiet + never remediate (mid-session safe)
//   node tools/health/monitor.mjs --remediate    # force the safe prune now, regardless of state
//   node tools/health/monitor.mjs --no-remediate # disable auto-prune for this run
//   node tools/health/monitor.mjs --watch [sec]  # loop (default 300s)
//   node tools/health/monitor.mjs --config <p>   # use an alternate config file

import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { collectWindows, CAN_WINDOWS, HERE, RANK, reading, worst } from './lib.mjs';
import { probes } from './probes.mjs';
import { dispatch, HOST, ICON } from './alerters.mjs';
import { runAuto, manualRunbook } from './remediate.mjs';

const ARGV = process.argv.slice(2);
const has = (f) => ARGV.includes(f);
const SESSION = has('--session');
const QUIET = has('--quiet') || SESSION;
const JSON_OUT = has('--json');
const FORCE_REMEDIATE = has('--remediate');
const NO_REMEDIATE = has('--no-remediate') || SESSION;
const STATE_FILE = join(HERE, '.state.json');

const DEFAULT_CONFIG = {
  drives: ['C'],
  thresholds: {
    hostDiskFreeGB: { warn: 25, critical: 10 },   // free space — low is bad
    hostDiskUsedPct: { warn: 85, critical: 93 },   // % used — high is bad
    dockerTotalGB: { warn: 40, critical: 60 },
    dockerReclaimableGB: { warn: 15, critical: 30 },
    wslVhdxGB: { warn: 60, critical: 100 },
  },
  alerters: {
    ndjson: { enabled: true },
    webhook: { enabled: false, format: 'ntfy', url: 'https://ntfy.sh/CHANGE-ME-agentarmy-health' },
  },
  remediation: {
    autoPruneOnCritical: true,
    cooldownMinutes: 60,
    allow: ['docker-prune-safe'],
  },
  alertCooldownMinutes: 30,
  timeoutMs: 8000,
};

function loadConfig() {
  const idx = ARGV.indexOf('--config');
  const path = idx >= 0 ? ARGV[idx + 1] : join(HERE, 'config.json');
  if (!path || !existsSync(path)) return DEFAULT_CONFIG;
  try {
    const user = JSON.parse(readFileSync(path, 'utf8'));
    return {
      ...DEFAULT_CONFIG, ...user,
      thresholds: { ...DEFAULT_CONFIG.thresholds, ...(user.thresholds || {}) },
      alerters: {
        ndjson: { ...DEFAULT_CONFIG.alerters.ndjson, ...(user.alerters?.ndjson || {}) },
        webhook: { ...DEFAULT_CONFIG.alerters.webhook, ...(user.alerters?.webhook || {}) },
      },
      remediation: { ...DEFAULT_CONFIG.remediation, ...(user.remediation || {}) },
    };
  } catch (e) {
    process.stderr.write(`health: bad config ${path}: ${e.message}\n`);
    return DEFAULT_CONFIG;
  }
}

const readState = () => {
  try { return JSON.parse(readFileSync(STATE_FILE, 'utf8')); } catch { return { alerts: {}, lastPrune: null }; }
};
const writeState = (s) => { try { writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); } catch { /* best effort */ } };

// Rate-limit: alert a reading if it's new, escalated since last time, or its
// cooldown has elapsed — so a steady warn doesn't spam every cycle.
function shouldAlert(r, state, cooldownMin) {
  const prev = state.alerts[r.id];
  if (!prev) return true;
  if (RANK[r.status] > RANK[prev.status]) return true;
  return (Date.now() - new Date(prev.ts).getTime()) / 60000 >= cooldownMin;
}

async function runOnce(config) {
  const ctx = {
    config,
    timeoutMs: config.timeoutMs || 8000,
    win: CAN_WINDOWS ? collectWindows(config.timeoutMs ? config.timeoutMs + 4000 : 12000) : null,
  };

  const readings = [];
  for (const probe of probes) {
    try { readings.push(...await probe(ctx)); }
    catch (e) { readings.push(reading({ id: probe.name, component: probe.name, status: 'warn', message: `probe error: ${e.message}` })); }
  }

  const overall = worst(readings.map((r) => r.status));
  const elevated = readings.filter((r) => r.status === 'warn' || r.status === 'critical');
  const critical = readings.filter((r) => r.status === 'critical');

  // ---- remediation -----------------------------------------------------------
  const state = readState();
  let remediation = [];
  const cooldownOk = !state.lastPrune ||
    (Date.now() - new Date(state.lastPrune).getTime()) / 60000 >= config.remediation.cooldownMinutes;
  const wantRemediate = !NO_REMEDIATE &&
    (FORCE_REMEDIATE || (config.remediation.autoPruneOnCritical && critical.length));
  if (wantRemediate && (FORCE_REMEDIATE || cooldownOk)) {
    remediation = runAuto(critical, config.remediation, Math.max(config.timeoutMs, 60000));
    if (remediation.length) state.lastPrune = new Date().toISOString();
  }

  // ---- alerting (rate-limited) ----------------------------------------------
  const ts = new Date().toISOString();
  const toAlert = elevated.filter((r) => shouldAlert(r, state, config.alertCooldownMinutes));
  const alerted = toAlert.length > 0 || remediation.length > 0;
  if (alerted) {
    const alert = {
      status: overall === 'ok' ? 'warn' : overall,
      ts, host: HOST,
      readings: toAlert.length ? toAlert : elevated,
      remediation,
    };
    await dispatch(alert, config.alerters);
  }
  // Refresh state: keep current elevated readings; stamp now for ones we alerted.
  const next = {};
  for (const r of elevated) {
    const prev = state.alerts[r.id];
    next[r.id] = { status: r.status, ts: toAlert.includes(r) ? ts : prev?.ts || ts };
  }
  state.alerts = next;
  writeState(state);

  return { overall, readings, elevated, critical, remediation, ctx, ts, alerted };
}

function render(result) {
  const { overall, readings, remediation, ctx } = result;
  if (JSON_OUT) {
    process.stdout.write(JSON.stringify({
      status: overall, host: HOST, ts: result.ts,
      windowsDataAvailable: Boolean(ctx.win), readings, remediation,
      manual: manualRunbook(result.critical),
    }, null, 2) + '\n');
    return;
  }
  const sorted = [...readings].sort((a, b) => RANK[b.status] - RANK[a.status]);
  if (QUIET) {
    // Scheduled-task / session mode: only speak up on a new/escalated alert
    // (rate-limited) or when a remediation actually ran.
    if (result.alerted) {
      const head = `${ICON[overall]} AgentArmy health ${overall.toUpperCase()} @ ${HOST}`;
      const body = result.elevated.map((r) => `  ${ICON[r.status]} ${r.message}`).join('\n');
      const rem = remediation.length
        ? '\n  ♻️  auto-remediated: ' + remediation.map((x) => `${x.id} (reclaimed ${x.reclaimed})`).join(', ')
        : '';
      process.stdout.write(`${head}\n${body}${rem}\n`);
    }
    return;
  }
  // Full status view.
  const lines = [`${ICON[overall]} AgentArmy health — ${overall.toUpperCase()} @ ${HOST}  ${result.ts.slice(0, 19).replace('T', ' ')}`];
  if (!ctx.win && CAN_WINDOWS) lines.push('  (windows collector returned no data — drives/vhdx skipped)');
  for (const r of sorted) lines.push(`  ${ICON[r.status]} ${r.message}`);
  if (remediation.length) {
    lines.push('  ♻️  auto-remediated:');
    for (const x of remediation) lines.push(`     - ${x.title} → reclaimed ${x.reclaimed} (${x.detail})`);
  }
  const manual = manualRunbook(result.critical);
  if (manual.length) {
    lines.push('  🔧 manual fixes available:');
    for (const m of manual) lines.push(`     - ${m.title}  [${m.id}]`);
  }
  process.stdout.write(lines.join('\n') + '\n');
}

function helpText() {
  return `AgentArmy health monitor — WSL/Docker storage + container health, alerts, auto-remediation.

Usage: node tools/health/monitor.mjs [options]
  --json          machine-readable output
  --quiet         emit only on an alert (for the Scheduled Task)
  --session       quiet + never remediate (safe at SessionStart)
  --remediate     force the safe Docker prune now
  --no-remediate  disable auto-prune for this run
  --watch [sec]   loop every N seconds (default 300)
  --config <path> alternate config file (default tools/health/config.json)
  --help

Config: copy tools/health/config.example.json → config.json and tune thresholds /
enable the webhook. Webhook URL can also come from $AGENTARMY_HEALTH_WEBHOOK_URL.`;
}

async function main() {
  if (has('--help') || has('-h')) { process.stdout.write(helpText() + '\n'); return; }
  const config = loadConfig();

  if (has('--watch')) {
    const idx = ARGV.indexOf('--watch');
    const sec = Number(ARGV[idx + 1]) > 0 ? Number(ARGV[idx + 1]) : 300;
    process.stdout.write(`health monitor watching every ${sec}s (Ctrl-C to stop)\n`);
    // eslint-disable-next-line no-constant-condition
    for (;;) {
      render(await runOnce(config));
      await new Promise((r) => setTimeout(r, sec * 1000));
    }
  }
  render(await runOnce(config));
}

main().catch((e) => { process.stderr.write(`health monitor error: ${e?.message || e}\n`); process.exit(0); });
