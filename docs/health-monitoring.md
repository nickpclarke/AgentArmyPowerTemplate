# Health Monitoring & Alerting (WSL / Docker storage + uptime)

A lightweight, dependency-free monitor that watches the things that have
actually halted this dev box — the Windows drive filling up because the
WSL/Docker `ext4.vhdx` grows without bound — warns **before** it's fatal, pushes
the alert to your phone, and on a critical disk situation auto-reclaims *safe*
Docker space.

It is also a **reusable health pattern**: probe → grade → alert → remediate.
Adding a new signal (a service endpoint, a queue depth, a cert expiry) is one
function. See [the pattern](#the-reusable-pattern) below.

> Background: this exists because of the 2026-05-26 disk-cascade incident — the
> Docker VHDX filled the box and jobs failed in cryptic ways. The
> `fleet-heartbeat.mjs --disk` flag was the first backstop; this monitor is the
> always-on, phone-alerting, auto-remediating version.

## Quick start

```bash
# 1. See current health (any OS — degrades gracefully off Windows)
node tools/health/monitor.mjs
npm run health

# 2. Turn on phone alerts (ntfy = simplest webhook-to-phone, free, no account)
cp tools/health/config.example.json tools/health/config.json
#   → install the "ntfy" app on your phone, subscribe to a private topic,
#     then set webhook.url to https://ntfy.sh/<your-private-topic>
#   (or export AGENTARMY_HEALTH_WEBHOOK_URL=... to keep it out of the file)

# 3. Run it continuously on the Windows host (every 15 min, even with no Claude open)
powershell -ExecutionPolicy Bypass -File tools\health\install-windows-task.ps1
```

`config.json` and `.state.json` are gitignored (per-machine). The webhook URL is
a capability token — prefer the `$AGENTARMY_HEALTH_WEBHOOK_URL` env var.

## What it checks

| Probe | Signal | Why it matters |
|---|---|---|
| `host-disk` | Free GB + used % on `C:` (Windows) or the repo mount (Linux) | This is what literally stops the PC. |
| `docker` | Engine reachable; total + reclaimable GB (`docker system df`) | The biggest space consumer; reclaimable = free win. |
| `containers` | Per-container health + restart count | Catches crash/restart loops and `unhealthy` states. |
| `wsl` | `ext4.vhdx` size per distro (incl. `docker-desktop-data`) | The file that silently grows on `C:` and never auto-shrinks. |

Each reading is graded `ok` / `warn` / `critical` against thresholds in
`config.json`. Tune them — defaults assume a ~250–500 GB drive.

## Alerts

Alerts fan out to every enabled sink, **rate-limited** so a steady warn doesn't
spam you (`alertCooldownMinutes`, default 30; an *escalation* always fires):

- **ntfy / webhook** — POST to a URL. `format`: `ntfy` (phone push, default),
  `slack`, `discord`, or `json`. Critical → max ntfy priority.
- **Twilio SMS** — `alerters.twilio` (`{ enabled, accountSid, from, to }`).
  Auth token via `$AGENTARMY_TWILIO_AUTH_TOKEN` (sourced from KV secret `Twilio`)
  or `authToken` in the gitignored `config.json`. **`criticalOnly: true` by
  default** — SMS is metered, so warns stay on the free channels and only
  critical alerts text you. Sends via the Twilio Messages REST API (Basic auth).
- **NDJSON log** — `tools/logs/health.log.YYYY-MM-DD`, queryable with the
  existing multiplexer: `node tools/tail.mjs query --grep health`.
- **console** — the monitor's own output (status view; one-liner in `--quiet`).

### ntfy phone path (MVP)

1. Install **ntfy** (iOS/Android/web).
2. Subscribe to a hard-to-guess topic, e.g. `agentarmy-nick-7f3a`.
3. Set `webhook.url` to `https://ntfy.sh/agentarmy-nick-7f3a` (or the env var).
4. Test: `npm run health` while a threshold is tripped, or
   `curl -d "test" https://ntfy.sh/agentarmy-nick-7f3a`.

Anyone who knows the topic can post to it — keep it private, or self-host ntfy.

## Remediation

When a **critical** disk reading trips and `remediation.autoPruneOnCritical` is
on, the monitor runs **only safe reclaims** and reports what it freed:

```
docker container prune -f   # stopped containers
docker image prune -f       # dangling (untagged) images only — never -a
docker builder prune -f     # build cache
```

**Guardrails (do not relax):** never named volumes, never `-a` (tagged images),
never `compose down`. A `cooldownMinutes` (default 60) prevents prune-thrash, and
every auto-run is pushed to your alert channels.

The one fix that actually shrinks the `.vhdx` file on `C:` (pruning frees space
*inside* the vhdx, but the file never auto-shrinks) is **manual** — the monitor
surfaces the runbook (`wsl --shutdown` + `--set-sparse` / `diskpart compact`)
but never runs it, because it requires stopping Docker. Force a safe prune
anytime with `node tools/health/monitor.mjs --remediate`.

## Where it runs

- **Windows Scheduled Task** (primary, continuous) — `install-windows-task.ps1`
  registers `AgentArmy-HealthMonitor` to run `--quiet` every 15 min at logon.
  Remove with `... -Uninstall`.
- **SessionStart hook** — runs `--session` (quiet **and** never remediates, so it
  can't delete build cache mid-session) to surface a heads-up when you open Claude.
- **Ad-hoc / `/loop`** — `npm run health`, or `--watch [sec]` to poll in a terminal.

## The reusable pattern

```
probe(ctx) → Reading[]   →   grade(value, thresholds)   →   dispatch(alert)   →   runAuto(critical)
 probes.mjs                   lib.mjs                        alerters.mjs          remediate.mjs
```

- **Add a probe:** write `(ctx) => Reading[]` and append it to `probes` in
  `tools/health/probes.mjs`. Use `grade(value, ctx.config.thresholds.X, 'low'|'high')`.
  Attach `remediations: ['action-id']` to wire a fix.
- **Add an alert channel:** add a sink `{ id, enabled, send }` to `SINKS` in
  `alerters.mjs`.
- **Add a remediation:** add an entry to `CATALOG` in `remediate.mjs`. Set
  `auto: true` only for genuinely safe, idempotent reclaims.

See `tools/health/README.md` for the module-level reference.
