---
tags: [security, infra, mcp, tunnel]
created: 2026-05-27
status: living
related:
  - "[[Cloud Agents → Local Docker — Control Plane Plan]]"
  - "[[Session 2026-05-27 — Dev Tunnel, Log Multiplexer, Catalog Gap]]"
---

# Security Model — Exposed Control Plane

We now expose two things publicly via `mcp.untool.ai` + `untool.ai`:

1. **The frontend** (Next.js dev server on `:3000`)
2. **The MCP control plane** (Node server on `:8765`) — capable of `docker compose build`, `docker compose restart`, `docker logs` against the operator's own PC

That second one is the interesting one. This note is the threat model + the mitigations we've shipped + the gaps that remain.

## What attackers can reach

| Surface | Path | Protection |
|---|---|---|
| `https://untool.ai/`, `https://dev.untool.ai/` | Cloudflare tunnel → Next.js on `:3000` | Session-cookie auth in app (BFF / ARC-ADR-002 JWT injector) |
| `https://mcp.untool.ai/healthz` | CF tunnel → MCP `:8765` | Public liveness — no fleet info exposed. Rate-limited per IP. |
| `https://mcp.untool.ai/.well-known/oauth-protected-resource` | CF tunnel → MCP | Public discovery doc (RFC 9728). No secrets. |
| `https://mcp.untool.ai/mcp` POST | CF tunnel → MCP | Dual auth: CF Access OIDC JWT OR static bearer. Rate-limited per principal. |

## Threat model

**Who:** opportunistic scanners hitting `mcp.untool.ai` via Shodan / CT-log monitoring; a leaked bearer in a screenshot / Discord paste / pcap; a compromised cloud-agent secret store.

**Not who:** state actors. The PC isn't worth that, and we'd lose anyway if we were.

**What they want:**
1. Read auth tokens from the box (Cerebras API key, GitHub tokens, etc.)
2. Run arbitrary code on the box (mine crypto, pivot to LAN)
3. Tamper with audit trail to cover tracks

## Mitigations shipped today

### 1. Allowlisted service names + no shell-exec tool
- `config.mjs` defines `ALLOWED_SERVICES` — only `arcadedb`, `postgres`, `nats`, `event-bridge` reachable via MCP tools.
- No `fleet.exec` / `fleet.shell` tool. Capability gaps become issues, not escape hatches.
- Implication: a leaked token can only restart/build/logs those four services. Can't `docker run ubuntu` and pivot.

### 2. Dual auth, principle of least surprise
- **CF Access OIDC JWT** — preferred. Browser OAuth flow, per-user email, signature-verified, audience-bound to `https://mcp.untool.ai/mcp`. Email allowlist enforced (only `nick@livecreative.com` today).
- **Static bearer** — fallback for local-laptop + curl tests. Constant-time compare, no length leak. Token in KV, never logged.
- Audit log records WHICH auth path was used (`principal: cfaccess:<email>` vs `bearer:static`).

### 3. Per-principal + per-IP rate limiting (in-memory leaky bucket)
- Authed callers: 30-burst, 60/min sustained (`ratelimit.mjs`).
- Anonymous probes: 20-burst, 30/min sustained.
- **Failed auth: 5-burst, 5/min by IP** — this is the brute-force cap. A leaked token can be guessed at most 5 times per minute before getting 429'd.
- Buckets are in-process — distributed attacks across many source IPs would still get through. Mitigation: Cloudflare WAF managed rules can be layered.

### 4. Tamper-evident audit log (hash chain)
- Every tool call appended to `tools/logs/mcp-audit.log.YYYY-MM-DD` as NDJSON with `prev_hash` (sha256 of previous record) and `hash` (sha256 of this record minus its own hash field).
- Any edit, deletion, or reorder breaks the chain. Detected by `node tools/mcp-local-fleet/verify-audit.mjs`.
- Demonstrated 2026-05-27: mutating one byte in any record causes verify to fail at that record.
- **Limit:** the chain is local. An attacker with root on the box can rewrite the chain from a chosen point forward. For real immutability we'd ship audit lines off-host (a queued send to a separate cloud bucket, or a signed beacon to a witness service). Acceptable for current threat model.

### 5. Separate security event sink
- Auth failures, rate-limit trips, body-cap violations → `tools/logs/mcp-security.log.YYYY-MM-DD` (distinct from tool-call audit).
- Each record has `ip`, `kind`, `ua` (truncated), `rate_limited` boolean.
- Enables fast "show me everything weird in the last hour" queries without wading through normal traffic.

### 6. Defense-in-depth response headers
Every response carries:
- `Strict-Transport-Security: max-age=63072000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
- `Cache-Control: no-store`

Most are theatrical for a JSON-RPC API, but they're free and they harden the response if something starts serving HTML.

### 7. Body cap (256 KB) + abort logging
- Anything larger gets `413 Payload Too Large` and is logged as `body_too_large` in the security sink with the byte count.

### 8. Bound to 127.0.0.1
- MCP server binds to `127.0.0.1:8765`. Public exposure is an explicit `tools/tunnel.mjs start --name mcp` second step. No accidental external reach.

### 9. Token rotation tooling
- `node tools/mcp-local-fleet/rotate-token.mjs` — generates fresh 48-char base64url token, writes to KV (versions retained for rollback), updates local settings, prints once.
- Restart of MCP server invalidates the old in-memory token immediately.

### 10. Real client IP capture
- `cf-connecting-ip` header parsed (cloudflared proxies locally, so default `remoteAddress` is always 127.0.0.1).
- Audit log + security log now show the true source IP for tunneled requests.

### 11. Fleet heartbeat probes the public endpoints
- `node tools/fleet-heartbeat.mjs --slo` now probes `https://mcp.untool.ai/healthz` and `https://untool.ai/`. Non-200 emits a `slo-probe-failed` warning. Single signal proves: cloudflared connector alive + tunnel routing OK + MCP server process up.

## Gaps still open

### CF Access enforcement on the public hostname
Currently CF Access acts as the OIDC IdP for our SaaS app, but doesn't gate the public URL. A direct request to `https://mcp.untool.ai/mcp` with a valid static bearer still works (intentionally — local laptop + curl need this path). The hardening upgrade: add a CF Access **Application** at `mcp.untool.ai/mcp*` requiring CF Access service tokens for non-OIDC clients. Migrating curl tests + local Claude Code to service tokens is a separate task.

### Bot Fight Mode false-positives
CF Bot Fight blocked `User-Agent: agentarmy-probe` earlier today. Cloud-agent clients with non-browser UAs may trip the same rule. **Action for operator:** in CF dashboard, add a custom rule exempting `mcp.untool.ai` from Bot Fight Mode, or whitelist the specific UAs the cloud agents send.

### Audit log shipping off-host
Currently local-only. If attacker compromises the box, they can rewrite the chain from any point forward. **Mitigation idea:** every N records, hash + POST to a witness service (could be just a private GitHub issue we append to via `gh api`). Then offline replay can detect "the chain re-forked at record X and we have evidence what record X used to be."

### Per-tool rate limiting
Currently all tools share one bucket per principal. A more nuanced model would have `fleet_build` (high-cost) cost 5 tokens, `fleet_ps` (cheap) cost 1. Not urgent.

### Build content is whatever's in the repo
`fleet_build` runs `docker compose build` against current local source. If an attacker gains git push to a watched branch, they can land a malicious Dockerfile and have it built on the operator's PC. **Mitigation:** require explicit human approval on every `fleet_build` invocation OR pin builds to specific git refs verified against a known-good checksum. Not implemented today.

### Tunnel token in chat history
The `cloudflare-tunnel-untool-ai` KV secret is the auth credential that lets `cloudflared` connect a connector to our tunnel. If leaked, an attacker can stand up a *competing* connector, accept traffic, and MITM it. Rotate it via CF dashboard ("Refresh token" on the tunnel) after every session that involved pasting tokens into LLM contexts.

## Operator checklist (when you're back)

- [ ] In CF dashboard: add **Bot Fight Mode** exception for `mcp.untool.ai/*` (currently blocking some legitimate cloud-agent UAs)
- [ ] In CF dashboard: rotate the **tunnel token** (`cloudflare-tunnel-untool-ai` KV secret leaked into chat earlier today; same procedure, ~30 sec)
- [ ] If you want belt-and-suspenders: rotate the **MCP bearer token** too — `node tools/mcp-local-fleet/rotate-token.mjs` then restart the server
- [ ] Set `CF_ACCESS_AUDIENCE=https://mcp.untool.ai/mcp` env on the MCP server once you confirm CF Access's `aud` claim matches that (currently empty → `aud` verification skipped)
- [ ] Run `node tools/mcp-local-fleet/verify-audit.mjs --all` on a schedule (or wire into the heartbeat) to detect log tampering
