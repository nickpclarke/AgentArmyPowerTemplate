# Arcade Cockpit

Arcade Cockpit is a local, optional dashboard for exploring and instrumenting an ArcadeDB container. It was built for the current AgentArmy ArcadeDB proof work without coupling this branch to the unfinished `claude/recursing-liskov-36b46a` platform code.

## What It Does

- Connects to ArcadeDB through a local Node proxy.
- Keeps the root password out of browser JavaScript.
- Shows database readiness, command latency, record counts, and recent query telemetry.
- Builds a playful graph map from known proof types: `StoredObject`, `Chunk`, and `IngestJob`.
- Lets you inspect graph nodes and run read-only SQL from the browser.

## Run

Start ArcadeDB first. The Claude worktree currently exposes it on `http://localhost:2480`.

```powershell
cd C:\Dev\AgentArmy\extensions\arcadedb-cockpit
node server.js
```

Then open:

```text
http://127.0.0.1:8787
```

Optional local overrides:

```powershell
copy .env.example .env
notepad .env
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8787` | Cockpit server port |
| `ARCADEDB_URL` | `http://localhost:2480` | ArcadeDB HTTP API |
| `ARCADEDB_USER` | `root` | ArcadeDB user |
| `ARCADEDB_PASSWORD` | `PlayWithData2026!` | Local test password |
| `ARCADEDB_DATABASE` | `knowledge` | Default database |
| `ARCADEDB_ALLOW_MUTATION` | `false` | Allows non-SELECT SQL only when set to `true` |

## Validation

```powershell
npm run check
```

The cockpit is designed to render even when ArcadeDB is offline. In that case it shows offline gauges and keeps the UI usable.
