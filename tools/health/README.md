# tools/health — WSL/Docker storage + health monitor

Always-on monitor for the Windows dev box: watches WSL/Docker storage, container
health and uptime, alerts (incl. phone push via ntfy), and auto-reclaims safe
Docker space on a critical disk situation. Dependency-free Node + two PowerShell
helpers. **User-facing runbook & quick start: [docs/health-monitoring.md](../../docs/health-monitoring.md).**

## Modules

| File | Role |
|---|---|
| `monitor.mjs` | Engine + CLI. Loads config, runs probes, grades, rate-limits + dispatches alerts, runs guarded auto-remediation, renders. |
| `lib.mjs` | Shared spine: `Reading`, `grade()`, platform detection, `run()`/`docker()` exec helpers, the Windows collector bridge, `sizeToGB()`. |
| `probes.mjs` | The probes: `host-disk`, `docker`, `containers`, `wsl`. Each is `(ctx) => Reading[]`. |
| `alerters.mjs` | Sinks: NDJSON log + webhook (ntfy/slack/discord/json). `dispatch()` fans out to enabled sinks. |
| `remediate.mjs` | `CATALOG` of fixes + `runAuto()` (guardrailed) + `manualRunbook()`. |
| `probe-windows.ps1` | Windows data collector (drives + WSL vhdx sizes + states). Piped to powershell via stdin, so it works from Windows **and** WSL. |
| `install-windows-task.ps1` | Registers/removes the `AgentArmy-HealthMonitor` Scheduled Task. |
| `config.example.json` | Copy → `config.json` (gitignored) and tune. |

## CLI

```
node tools/health/monitor.mjs              # one pass, full status view
  --json            machine-readable
  --quiet           emit only on a new/escalated alert (Scheduled Task)
  --session         quiet + never remediate (safe at SessionStart)
  --remediate       force the safe Docker prune now
  --no-remediate    disable auto-prune for this run
  --watch [sec]     loop every N seconds (default 300)
  --config <path>   alternate config file
```

## Extending (the reusable pattern)

- **New probe** → write `(ctx) => Reading[]`, append to `probes`. `ctx` has
  `{ config, timeoutMs, win }` (`win` = parsed `probe-windows.ps1` JSON, or null
  off-Windows). Grade with `grade(value, ctx.config.thresholds.X, 'low'|'high')`
  and attach `remediations: ['action-id']` to wire a fix.
- **New alert channel** → add `{ id, enabled(cfg), send(alert, cfg) }` to `SINKS`.
- **New remediation** → add to `CATALOG`; `auto: true` only for safe, idempotent
  reclaims. Never auto-run anything that touches named volumes or tagged images.

## Notes

- Degrades gracefully: missing docker daemon / non-Windows → probes return
  `skip`, never throw (mirrors `tools/status.mjs`).
- Logs are NDJSON in `tools/logs/health.log.YYYY-MM-DD` (gitignored) and
  queryable via `node tools/tail.mjs query --grep health`.
- `config.json` + `.state.json` are gitignored (per-machine). Keep the webhook
  URL in `$AGENTARMY_HEALTH_WEBHOOK_URL`.
