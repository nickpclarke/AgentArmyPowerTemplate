// lib.mjs — shared primitives for the AgentArmy health monitor.
//
// This is the reusable spine of the pattern: a Reading (one measured signal),
// a grade() that maps a value to ok/warn/critical against thresholds, and the
// command helpers probes use to gather data. Everything degrades gracefully —
// nothing here throws on a missing tool or unreachable daemon (mirrors the
// status.mjs contract).

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const HERE = dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = join(HERE, '..', '..');

// Severity ordering — higher is worse. Mirrors the doctor's STATUS_RANK.
export const RANK = { ok: 0, skip: 0, warn: 1, critical: 2 };
export const worst = (statuses) =>
  statuses.reduce((acc, s) => (RANK[s] > RANK[acc] ? s : acc), 'ok');

// ---- platform detection ----------------------------------------------------
export const IS_WINDOWS = process.platform === 'win32';
export const IS_WSL =
  process.platform === 'linux' &&
  (Boolean(process.env.WSL_DISTRO_NAME) ||
    (existsSync('/proc/version') && /microsoft/i.test(safeRead('/proc/version'))));
// We can reach the Windows side (powershell.exe + docker.exe) from native
// Windows and from inside WSL via interop.
export const CAN_WINDOWS = IS_WINDOWS || IS_WSL;

function safeRead(p) {
  try { return readFileSync(p, 'utf8'); } catch { return ''; }
}

// ---- grading ---------------------------------------------------------------
// direction 'low'  → a SMALL value is bad (e.g. free GB).
// direction 'high' → a LARGE value is bad (e.g. used %, reclaimable GB).
export function grade(value, thresholds, direction = 'high') {
  if (!thresholds || value == null || Number.isNaN(value)) return 'ok';
  const { warn, critical } = thresholds;
  if (direction === 'low') {
    if (value <= critical) return 'critical';
    if (value <= warn) return 'warn';
    return 'ok';
  }
  if (value >= critical) return 'critical';
  if (value >= warn) return 'warn';
  return 'ok';
}

// ---- Reading factory -------------------------------------------------------
// A Reading is the unit every probe emits and every alerter/remediation reads.
export function reading({ id, component, label, value = null, unit = '', status, message, evidence = {}, remediations = [] }) {
  return { id, component, label, value, unit, status, message, evidence, remediations };
}

// ---- command helpers -------------------------------------------------------
// execFile (array args, NO shell) — no command injection, per the repo's
// security convention. Never throws; returns { ok, out }.
export function run(cmd, args, { timeoutMs = 6000, input } = {}) {
  try {
    const out = execFileSync(cmd, args, {
      encoding: 'utf8',
      timeout: timeoutMs,
      input,
      stdio: ['pipe', 'pipe', 'ignore'],
      windowsHide: true,
      maxBuffer: 16 * 1024 * 1024,
    });
    return { ok: true, out: (out || '').trim() };
  } catch (e) {
    return { ok: false, out: (e.stdout || '').toString().trim(), code: e.status };
  }
}

export const docker = (args, timeoutMs = 6000) => run('docker', args, { timeoutMs });

// Run the Windows data collector by piping the .ps1 to powershell over stdin
// (`-Command -`). Avoids Windows↔WSL path translation entirely, so the same
// call works natively and through interop. Returns parsed JSON or null.
export function collectWindows(timeoutMs = 12000) {
  if (!CAN_WINDOWS) return null;
  const script = safeRead(join(HERE, 'probe-windows.ps1'));
  if (!script) return null;
  for (const ps of ['powershell.exe', 'pwsh', 'powershell']) {
    const res = run(ps, ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', '-'],
      { timeoutMs, input: script });
    if (res.ok && res.out) {
      // PSReadLine can prepend ANSI/terminal-init noise on stdin pipes, so don't
      // assume the whole stream is pure JSON — extract the object and parse it.
      const m = res.out.match(/\{[\s\S]*\}/);
      if (m) { try { return JSON.parse(m[0]); } catch { /* try next shell */ } }
    }
  }
  return null;
}

// ---- size parsing ----------------------------------------------------------
// Convert docker's human sizes ("2.046GB", "956.6MB", "0B") to GB.
const UNIT_GB = { B: 1e-9, KB: 1e-6, kB: 1e-6, MB: 1e-3, GB: 1, TB: 1e3, PB: 1e6 };
export function sizeToGB(str) {
  if (!str) return 0;
  const m = String(str).trim().match(/^([\d.]+)\s*([A-Za-z]+)?$/);
  if (!m) return 0;
  const n = parseFloat(m[1]);
  const unit = (m[2] || 'B').replace('i', ''); // GiB→GB, treat as decimal (close enough)
  return n * (UNIT_GB[unit] ?? UNIT_GB[unit.toUpperCase()] ?? 1e-9);
}

// Redact a webhook URL for logging — ntfy/Slack URLs are capability tokens.
export const redactUrl = (u) => (u ? String(u).replace(/(\/\/[^/]+\/).*/, '$1[redacted]') : u);
