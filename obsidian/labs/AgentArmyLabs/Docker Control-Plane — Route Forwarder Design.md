---
tags: [design, platform, mcp, infra, incident]
track: platform
date: 2026-05-28
---
# 🔌 Docker Control-Plane — Route Forwarder Design

**🧭 [[Cloud Agents → Local Docker — Control Plane Plan]] · 🛡 [[Security Model — Exposed Control Plane]]**

> [!warning] Why this exists — the 2026-05-28 untool.ai outage
> The cloudflared named tunnel `cloudflare-tunnel-untool-ai` **coupled three public hostnames in one ingress**: `untool.ai → :3000`, `dev.untool.ai → :3000`, **`mcp.untool.ai → :8765`**. Running its connector on the **operator dev box** (to expose the docker-control MCP) made that box the origin for `untool.ai` too — pointed at a dead local `:3000` → **site-wide 502** (frontend-core #91). The frontend ACA app (`frontend-core`, `rg-arcade-platform`) was **healthy the whole time** (200 direct). The coupling — one tunnel serving both the product frontend and the operator control plane — is the bug.

## Decision

**Decouple by concern.** A product hostname must never share a tunnel with an operator service.
- **`untool.ai` / `dev.untool.ai`** (product frontend) → the **ACA app**, independent of any operator tunnel (CNAME direct, or a frontend-only tunnel).
- **`mcp.untool.ai`** (docker-control MCP) → its **own dedicated forwarder** to `localhost:8765`, owned by the operator, that *cannot* affect product hostnames.

## The route forwarder (recommended: dedicated MCP tunnel)

A **separate** cloudflared named tunnel that serves **only** the control plane:
- New tunnel `agentarmy-mcp` (token in KV, e.g. `cloudflare-tunnel-mcp`). Ingress = **only** `mcp.untool.ai → http://localhost:8765` + a `404` catch-all. No frontend hostnames, ever.
- **CF Access** service tokens gate it exactly as today (defense-in-depth: the MCP server also verifies the CF Access JWT; bearer accepted on loopback only).
- The operator runs `cloudflared tunnel run` for *this* tunnel. Because its ingress contains no product hostname, an operator running/stopping it can never take `untool.ai` down.

**Why a dedicated tunnel, not shared ingress:** one tunnel per concern means an operator action (run/stop/restart on a laptop) has a blast radius of *operator services only*. The outage proved the shared-ingress blast radius reaches production.

## Optional: a local reverse-proxy in front of the MCP

If you want a stable edge target decoupled from the MCP process lifecycle (restarts, port changes) — or to expose several local docker-control services through one route — run a tiny local reverse proxy (Caddy / nginx / socat / a node proxy) on a fixed port that forwards → `127.0.0.1:8765`, and point cloudflared at the proxy instead of the MCP directly. Not required for v1 (cloudflared → `:8765` is fine); it's the growth path when "docker controls" become more than one service.

## Interim (today)

The existing operator tunnel keeps `mcp.untool.ai → :8765` **live** — leave it running. The moment `untool.ai` is repointed to the ACA app **and removed from `cloudflare-tunnel-untool-ai`'s public hostnames**, the coupling is gone even before the dedicated tunnel exists.

## Migration steps

1. **(operator / Cloudflare)** Point `untool.ai` + `dev.untool.ai` → the ACA app (`frontend-core.kindcoast-b0a6ea84.eastus.azurecontainerapps.io`); **remove** them from `cloudflare-tunnel-untool-ai`'s public hostnames. → restores the site (frontend-core #91).
2. Create the `agentarmy-mcp` tunnel (ingress: `mcp.untool.ai → :8765` only); store its token in KV; update the operator runbook (`tools/mcp-local-fleet/AUTOMATION.md`) to run *that* tunnel.
3. Retire `untool.ai` from the operator tunnel entirely — the operator tunnel serves `mcp.untool.ai` and nothing product-facing.
4. *(optional)* Add the local reverse-proxy forwarder when >1 local docker-control service needs exposing.

> [!tip] Standing guardrail
> **Never put a product hostname (`untool.ai`, `dev.untool.ai`, app routes) in an operator/MCP tunnel's ingress.** Operator tunnels expose operator services only. This is the one rule that would have prevented the outage.

---

Related: [[Cloud Agents → Local Docker — Control Plane Plan]] · [[Security Model — Exposed Control Plane]] · [[Architecture Atlas — Conceptual to Contract]]
