---
tags: [anti-pattern, mcp, fleet, spoke-sync, tiering, validation]
created: 2026-06-01
status: reference
related:
  - "[[Untool Fleet Suite — Operating Manual]]"
  - "[[Cloud Agents → Local Docker — Control Plane Plan]]"
  - "[[Architecture Atlas — Conceptual to Contract]]"
---

# Single-Repo Vantage — Why Spokes Consume the Hub, Not Rebuild It

> [!warning] The load-bearing rule
> **A spoke consumes the hub's `local-fleet` MCP server; it never re-implements
> the coordination / VFS / conformance plane locally.** Those tools live once, in
> the hub (`tools/mcp-local-fleet/`), and reach every spoke through the synced
> `.mcp.json`. If a spoke "has no fleet tools," it is **un-dressed**, not
> missing a feature — run the dressing sync, don't rebuild.

## What happened

On 2026-06-01 an external advisor (attached to a **single spoke**, `commons-core`)
produced a four-part blueprint telling us to *build*: a fleet coordination plane
(`fleet_agent_join` / `handoff` / `memo_*`), a Holographic Virtual Filesystem
(`vfs_file_write` / `vfs_commit`), conformance tools, and a separate Python/poetry
MCP server. From inside one not-yet-dressed Python repo the fleet looks greenfield.
It is not. Acting on the blueprint verbatim would be a **regression** and would
**fragment** the single-server architecture.

This note records the verdict so the misdiagnosis isn't repeated by the next agent
that opens a lone spoke.

## Verdict by area

| Blueprint area | Reality in the fleet |
|---|---|
| **1. Coordination plane** | **Already built** in the hub: `tools/mcp-local-fleet/tools.mjs` (Node), backed by **NATS CloudEvents + a file/JSON ledger with compare-and-swap** — not SQLite. Hardened in #434 (durable identity across compaction) and #430 (reliable NATS publish + lost-update-safe writes). ⚠️ Currently on integration branch `claude/modest-roentgen-6fd4e1`, **not yet merged to `main`** — built and running, in-flight to trunk. |
| **2. HVFS** | **Already an accepted decision — ARC-ADR-047** (lakeFS + SQLite staging + NATS live-sync, mirrors git verbs, `ut vfs lock` via ArcadeDB+TTL). The blueprint's `vfs_commit` is also **buggy**: it computes paths relative to the staging dir then writes relative to the process CWD (not the repo), and `rmtree`s the buffer with no rollback. It reinvents the **git worktrees** the fleet already uses for isolation. |
| **3. Conformance tools** | `compliance/check_tier_separation.py` **does not exist** (no `compliance/` dir — it's a hypothetical in ARC-ADR-029). RFC 7807 is already a real contract (`contracts/problem-details.openapi.yaml`), so `validate_error_envelope` is redundant. The **one genuine gap** (an executable tier-separation checker, ARC-ADR-023 future work) we closed — see below. |
| **4. Deploy guide** | Wrong stack. The fleet runs **one Node HTTP/JSON-RPC server on `:8765`**, wired via `.mcp.json` + Bearer/CF-Access. A second poetry stdio server fragments it. Adding a tool = one handler + one object in the `TOOLS` array. |

## Root cause — the topology the advisor couldn't see

`Hub ──serves──▶ local-fleet MCP server (one, on :8765)`, and the synced
`.mcp.json` points **every** repo at it. Spokes are **clients**, not
implementers. `commons-core` simply wasn't in the `spokes` list in
[`scripts/spoke_sync.config.json`](../../../scripts/spoke_sync.config.json) yet
(PR #432 adds it). "Missing tools" was an artifact of an un-synced spoke. The fix
is **wiring** (dress the spoke), not **building**.

See [[Untool Fleet Suite — Operating Manual]] for the server, the tool roster, and
the two auth modes (bearer on loopback, CF-Access service tokens for cloud).

## The one real gap we closed

ARC-ADR-023 §Implementation flagged "the fleet-heartbeat should warn on cross-tier
bundling" as future work. We built it correctly in the hub's existing stack:

- **`tools/checks/tier-separation.mjs`** — a pure, unit-tested checker: does an
  Application/Function spoke bundle Platform-tier infra (ArcadeDB, Postgres, NATS,
  Fuseki, …) into a `docker-compose` / `Dockerfile` instead of consuming it via
  env (`ARCADEDB_URL`, `NATS_URL`, …)? It only inspects `image:` / `FROM` values,
  so a correct `*_URL` env reference is never a false positive.
- **`fleet_check_tiers`** — a read-only MCP tool exposing it (one handler + one
  `TOOLS` entry), so any coder can self-check in its inner loop.
- **fleet-heartbeat §2c+** — emits a `cross-tier-bundling` WARN fleet-wide.

That's the shape every capability should take: **build once in the hub, serve
over MCP, and let the spokes consume it.**
