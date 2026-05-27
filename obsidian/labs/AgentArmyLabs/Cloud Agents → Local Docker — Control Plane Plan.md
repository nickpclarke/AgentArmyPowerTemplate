---
tags: [plan, infra, mcp, tunnel, observability]
created: 2026-05-27
status: proposed
related:
  - "[[Factory-Loop-Test-Infrastructure]]"
  - "[[API Strategy — Internal, External, Open & Monetized]]"
  - "[[Mobile Strategy — Browser-First & PWA]]"
---

# Cloud Agents → Local Docker — Control Plane Plan

> **Historical context (2026-05-27):** this note used the tool-prefix `local_fleet.<action>` before the design landed. The shipped tools live under the `fleet_<action>` prefix (snake_case) and the system is branded **untool fleet suite**. The architecture in this note is still the basis of what's deployed; only the names changed. See `tools/mcp-local-fleet/README.md` for current authoritative tool list.

## North-star

> A cloud agent (Claude.ai routine, GitHub Actions runner, a remote OpenAI/Claude API caller, another human's laptop) can **build, test, deploy, observe, and iterate on agents that live in our local Docker** — using the same tunnel surface we just stood up for the frontend.

This makes the dev box behave like a tiny per-developer Container Apps environment that cloud agents can drive. It also makes "the entire fleet" reachable from any compute that can speak HTTPS.

## Why now

This session established three primitives that, *together*, make this possible:

1. **`tools/tunnel.mjs`** — vendor-agnostic public HTTPS for `localhost:*`. Today: cloudflared → `*.trycloudflare.com`. Tomorrow: a stable subdomain on a Cloudflare-managed zone, or paid ngrok.
2. **`tools/tail.mjs`** — daily-rotated NDJSON logs for any spawned dev service, with a `query` subcommand any agent (cloud or local) can grep over time.
3. **The lesson from `INCOMPLETE_STREAM`** — agentic loops are too noisy to debug without aggregated logs. We can't ship a cloud-agent flow without one.

Adding a fourth primitive (the **local fleet control plane**) connects them.

## Trust boundary — non-negotiable

The Docker socket on a developer laptop is **root on host**. Exposing it raw over a tunnel — even an authenticated one — is a non-starter.

The pattern is **never expose Docker; expose a *capability* server that wraps it.** That capability server only knows how to do safe, named, idempotent things. It rejects everything else.

```
cloud agent
   │  HTTPS + bearer / OIDC + audit-id
   ▼
[cloudflared edge] ── TLS termination ──▶ tunnel
   │
   ▼
[ tools/mcp-local-fleet ]  ──── only authenticated, only listed tools
   │
   ├── docker compose build <known-service>
   ├── docker compose up <known-service>
   ├── docker compose logs <known-service> (delegates to tail.mjs query)
   ├── git pull && restart
   ├── pytest / playwright run
   └── audit-log every call
       │
       ▼
[ host docker / git / pytest ]
```

The control plane is a small, auditable service. Docker socket access is confined to a single Unix-domain (or named-pipe on Windows) handler inside that service. No tool exposed to cloud agents accepts a free-form shell command.

## Capability matrix (first-cut)

| Capability | Tool name | Risk | Phase |
|---|---|---|---|
| Tail/query app logs | `local_fleet.logs(service, since, grep, level)` | Low (read-only, structured) | 1 |
| List running services | `local_fleet.ps()` | Low | 1 |
| Inspect one service | `local_fleet.inspect(service)` (returns image, env keys w/o values, ports) | Low | 1 |
| Restart a known service | `local_fleet.restart(service)` | Med | 2 |
| Start/stop a known service | `local_fleet.up(service) / .down(service)` | Med | 2 |
| Rebuild a known service from current code | `local_fleet.build(service)` | High (executes Dockerfile = arbitrary code by definition) | 3 |
| Pull a branch and redeploy | `local_fleet.deploy(repo, branch, service)` | High | 4 |
| Run tests | `local_fleet.test(scope)` (scope ∈ {unit, integration, e2e}) | Med (CPU spend, can leak data via test output) | 4 |
| Get current tunnel URL | `local_fleet.tunnel_url()` | Low | 1 |

**"Known service"** means a name in a static allowlist (e.g. `frontend`, `middle`, `back`, `arcadedb`, `event-bridge`) — *not* any arbitrary container name. Cloud agents can't ask us to start `crypto-miner-v2`.

## Architecture options considered

**A. Direct Docker socket over tunnel** — rejected. Docker socket = root on host. No level of bearer auth makes this acceptable.

**B. SSH over tunnel + shell access** — rejected. Equivalent to (A) with extra steps. A cloud agent with shell on the host is indistinguishable from a compromise.

**C. Single HTTPS API (FastAPI/Hono/Node) wrapping `docker compose` / `git`** — viable. Conventional, easy to audit, plays well with any HTTP-speaking caller. Downside: each cloud agent needs a custom client; not auto-discoverable.

**D. MCP server (Model Context Protocol) over the tunnel** ★ — preferred. Identical capability surface to (C), but:
- Auto-discoverable: any MCP-aware client (Claude.ai routines, Claude Code, Cursor, etc.) can list and call tools without bespoke integration code
- Schema is the documentation; tools advertise their parameters
- Standardised audit/observability hooks per the MCP spec
- We're already an MCP-heavy fleet (see `.mcp.json`)

**E. Webhook + job queue** — viable for async-only flows (build a thing, get notified later). Worth adding alongside D for long-running ops, not instead of.

**Recommendation: D primary, E for long-running jobs.**

## Authn / Authz

- Single bearer token per **cloud-agent identity**, stored in Key Vault (`local-fleet-mcp-<identity>`), e.g. `local-fleet-mcp-claude-ai-routine`, `local-fleet-mcp-github-actions`.
- Capability sets per identity (so a routine that only needs logs doesn't also get `deploy`).
- Every call gets a server-generated `audit-id`, logged to `tools/logs/mcp.log.YYYY-MM-DD` (the same retention scheme as the rest of the fleet — purgeable by `tools/tail.mjs clean`).
- No bearer token in logs ever (same hygiene as the ngrok-token-in-temp-file lesson from this session).

## Phasing — what to build, in what order

| Phase | Capabilities | New deps | Effort | Risk |
|---|---|---|---|---|
| **1 — Observe** | `tunnel_url`, `ps`, `inspect`, `logs` | MCP server scaffold; reuse tail.mjs query | ½ day | low — read-only |
| **2 — Lifecycle** | `up`, `down`, `restart` | docker compose wrapper, allowlist | ½ day | med — service downtime, contained to known names |
| **3 — Build** | `build` | Dockerfile execution, build cache mgmt | 1 day | high — first capability that runs arbitrary code (your own Dockerfile, but still) |
| **4 — Deploy + Test** | `deploy`, `test` | git wrapper, pytest/playwright runners, output streaming | 1–2 days | high — full development loop |

**Each phase ships independently behind the same MCP server**, so a cloud-agent identity scoped to Phase 1 can't accidentally invoke Phase 3 tools.

## What "done" looks like

A claude.ai routine can run, unattended:

1. "Build the latest middle-core from `claude/e2e-backend-integration-czAm5`."
2. "Restart it."
3. "Tail the logs for 30 seconds and report any errors."
4. "If there's an error, file a hub issue with the trace."
5. "Otherwise, run `pytest tests/test_agent.py` and post results."

…using only MCP tools, with full audit trail, no shell access, no Docker socket exposure, and the dev box stays healthy.

## Open questions for the next conversation

- **Stable tunnel URL** — phase 0 should be adding a Cloudflare-managed zone (cheap domain + free Cloudflare plan) so the MCP server has a stable HTTPS hostname. Otherwise every dev restart breaks the cloud agents.
- **Per-identity vs single token?** — single is faster to ship; per-identity is the right long-term default. Probably ship single, then split before exposing to anyone outside your control.
- **Audit retention** — same 3-day TTL as other logs, or longer (30d) for security review?
- **Idempotency keys** — should `build` accept an idempotency key so duplicate calls don't burn cycles?
- **Concurrency** — single in-flight `build`, queue the rest?
- **Egress firewall** — does the MCP server need to *limit* what the spawned containers can reach (e.g. block egress to your home LAN)?

## Related work elsewhere in the repo

- [[Factory-Loop-Test-Infrastructure]] — the test-infra side of the same vision; "factory loop" implies a producer side that the control plane is the runtime of.
- [[API Strategy — Internal, External, Open & Monetized]] — monetisation tier note: this control plane is *internal-only forever*. The customer-facing path is api-gateway-engineer + Azure APIM, separate concern.
- `tools/tunnel.mjs`, `tools/tail.mjs` — the two primitives this builds on.
- `reference_tunnel_vendor.md` (memory) — why cloudflared and not ngrok-free.
- ARC-ADR-002 — the JWT injection pattern that's the model for the bearer-token flow here.

## Pre-decisions worth surfacing

1. **No Docker socket exposure, ever.** The MCP server is the *only* code that touches `/var/run/docker.sock`. This is the single most important rule.
2. **Allowlisted service names only.** Cloud agents cannot name new containers.
3. **No shell-exec tool.** If a cloud agent asks for capability X that we haven't implemented as a typed tool, the answer is "file a hub issue to add it" — never "here's a `run_shell` escape hatch."
4. **Audit log is append-only and required.** A capability that can mutate state without an audit entry is a bug.
