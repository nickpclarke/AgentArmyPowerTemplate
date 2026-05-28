// alerters.mjs — pluggable alert sinks. Each sink is { id, send(alert, cfg) }.
// An `alert` is { status, ts, readings, summary, host } where `readings` are the
// warn/critical Readings that tripped. Adding a channel = adding a sink here.

import { appendFileSync, existsSync, mkdirSync } from 'node:fs';
import { hostname } from 'node:os';
import { join } from 'node:path';
import { REPO_ROOT, redactUrl } from './lib.mjs';

const LOG_DIR = join(REPO_ROOT, 'tools', 'logs');
export const ICON = { ok: '✅', warn: '🟡', critical: '🔴', skip: '·' };

// ---- NDJSON log (one line per reading; tail.mjs-compatible) ----------------
const ndjsonSink = {
  id: 'ndjson',
  enabled: (cfg) => cfg?.enabled !== false,
  async send(alert) {
    if (!existsSync(LOG_DIR)) mkdirSync(LOG_DIR, { recursive: true });
    const stamp = alert.ts.slice(0, 10);
    const file = join(LOG_DIR, `health.log.${stamp}`);
    const level = (s) => (s === 'critical' ? 'error' : s === 'warn' ? 'warn' : 'info');
    const lines = alert.readings.map((r) => JSON.stringify({
      ts: alert.ts, service: 'health', level: level(r.status),
      component: r.component, status: r.status, value: r.value, unit: r.unit,
      msg: r.message,
    }));
    if (lines.length) appendFileSync(file, lines.join('\n') + '\n', 'utf8');
  },
};

// ---- webhook (ntfy phone path + slack/discord/json) ------------------------
const webhookSink = {
  id: 'webhook',
  enabled: (cfg) => Boolean(cfg?.enabled && (process.env.AGENTARMY_HEALTH_WEBHOOK_URL || cfg.url)),
  async send(alert, cfg) {
    const url = process.env.AGENTARMY_HEALTH_WEBHOOK_URL || cfg.url;
    if (!url || /CHANGE-ME/.test(url)) return;
    const format = cfg.format || 'ntfy';
    const title = `AgentArmy health: ${alert.status.toUpperCase()} @ ${alert.host}`;
    const body = alert.readings.map((r) => `${ICON[r.status]} ${r.message}`).join('\n');

    let opts;
    if (format === 'ntfy') {
      // ntfy.sh: plain-text body + metadata headers. Critical → max priority.
      opts = {
        method: 'POST',
        headers: {
          Title: title,
          Priority: alert.status === 'critical' ? '5' : '4',
          Tags: alert.status === 'critical' ? 'rotating_light,floppy_disk' : 'warning',
        },
        body,
      };
    } else if (format === 'slack') {
      opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: `*${title}*\n${body}` }) };
    } else if (format === 'discord') {
      opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: `**${title}**\n${body}` }) };
    } else {
      opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(alert) };
    }

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    try {
      const res = await fetch(url, { ...opts, signal: ctrl.signal });
      if (!res.ok) process.stderr.write(`health webhook ${redactUrl(url)} → HTTP ${res.status}\n`);
    } catch (e) {
      process.stderr.write(`health webhook ${redactUrl(url)} failed: ${e.message}\n`);
    } finally {
      clearTimeout(timer);
    }
  },
};

// ---- Twilio SMS ------------------------------------------------------------
// SMS is metered (costs per message), so default to CRITICAL-only — warns stay
// on the free channels (ntfy/NDJSON). Auth token comes from the env var
// (sourced from KV secret `Twilio`) or cfg.authToken (gitignored config.json);
// accountSid + from + to live in config. Sink stays disabled until all present.
const twilioSink = {
  id: 'twilio',
  enabled: (cfg) => Boolean(
    cfg?.enabled && cfg.accountSid && cfg.from && cfg.to &&
    (process.env.AGENTARMY_TWILIO_AUTH_TOKEN || cfg.authToken)
  ),
  async send(alert, cfg) {
    if (cfg.criticalOnly !== false && alert.status !== 'critical') return;
    const token = process.env.AGENTARMY_TWILIO_AUTH_TOKEN || cfg.authToken;
    const trip = alert.readings
      .filter((r) => r.status !== 'ok')
      .map((r) => r.message)
      .slice(0, 3)
      .join('; ');
    // SMS segments cost money — keep it terse + single-ish segment.
    const body = `AgentArmy ${alert.status.toUpperCase()} @ ${alert.host}: ${trip || alert.summary || ''}`.slice(0, 320);
    const auth = Buffer.from(`${cfg.accountSid}:${token}`).toString('base64');
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    try {
      const res = await fetch(
        `https://api.twilio.com/2010-04-01/Accounts/${cfg.accountSid}/Messages.json`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            Authorization: `Basic ${auth}`,
          },
          // channel 'whatsapp' prefixes the addresses (sandbox/sender); default 'sms'.
          body: new URLSearchParams({
            To: (cfg.channel === 'whatsapp' ? 'whatsapp:' : '') + cfg.to,
            From: (cfg.channel === 'whatsapp' ? 'whatsapp:' : '') + cfg.from,
            Body: body,
          }),
          signal: ctrl.signal,
        },
      );
      if (!res.ok) {
        const t = await res.text().catch(() => '');
        process.stderr.write(`health twilio → HTTP ${res.status} ${t.slice(0, 120)}\n`);
      }
    } catch (e) {
      process.stderr.write(`health twilio failed: ${e.message}\n`);
    } finally {
      clearTimeout(timer);
    }
  },
};

// NDJSON + webhook + Twilio are the persistent/push channels. Console output is
// the engine's own responsibility (it doubles as a status view), so it isn't a sink.
export const SINKS = [ndjsonSink, webhookSink, twilioSink];

// Fan an alert out to every enabled sink.
export async function dispatch(alert, alertersCfg = {}) {
  await Promise.all(SINKS.map(async (sink) => {
    const cfg = alertersCfg[sink.id] || {};
    if (!sink.enabled(cfg)) return;
    try { await sink.send(alert, cfg); }
    catch (e) { process.stderr.write(`alerter ${sink.id} failed: ${e.message}\n`); }
  }));
}

export const HOST = hostname();
