# Agent Onboarding: MicroVM Spoke Agents

> **This guide is for spoke microVM agents.** If you are working in the AgentArmy hub repository, see [setup.md](setup.md) and [armies-overview.md](armies-overview.md) instead.

Welcome. You are an isolated AI agent running in a spoke repository—one layer of a distributed system. This guide gets you oriented and productive.

## Orientation keys

Two links anchor everything — **start here, bookmark both:**

- **Docs — tangible reality:** <https://nickpclarke.github.io/AgentArmy/> — the published, settled documentation. The source of truth you act on.
- **Labs — vision / WIP:** <https://publish.obsidian.md/xlabs/Welcome> — the Obsidian vault: research, design-in-progress, ontology/ER modeling. Where ideas are born and shaped before they graduate to Docs.

You can reach both as URLs from inside your microVM; you do **not** have the hub's `docs/` or the vault checked out locally.

---

## The Landscape: Hub & Spokes

AgentArmy is a **hub-and-spoke fleet**:

- **Hub** ([AgentArmy](https://github.com/nickpclarke/AgentArmy)) — the template, coordination plane, and shared standards. One GitHub Projects board, unified planning.
- **Spokes** (your repos) — layer implementations: frontend, backend, worker, mobile, infra. Each is an independent repository with its own Issues/PRs.

**Three armies coordinate across both:**
- **Claude Code** — deep thinking, architecture, complex features. See [armies-overview.md](armies-overview.md).
- **GitHub Copilot** — lightweight, GitHub-native tasks (PRs, simple bugs). See [armies-overview.md](armies-overview.md).
- **SAFE planning** — Program Increments, sprints, capacity. See [SAFE.md](safe.md).

Full context: [N-Layer Hub & Spoke Architecture](n-layer-architecture.md) and [N-Layer Spoke Rules](n-layer-spoke-rules.md).

---

## Your Environment: Isolated & Read-Only Hub Access

You run in a **microVM**—a completely isolated filesystem and runtime:

### What you have locally (synced into your repo)
- `.claude/agents/categories/` — all agent definitions
- `AGENTS.md` — agent roster and routing guide
- `CLAUDE.md` — routing rules and principles specific to spokes
- `.claude/commands/` — slash commands (`/wardley`, `/ea-adr`, `/capability-map`)

### What you must read at the hub's shared surfaces (your two orientation keys)
- **Docs (reality):** **https://nickpclarke.github.io/AgentArmy/** — full published docs (armies, setup, diagnostics, cloud patterns, roadmap)
- **Labs (vision/WIP):** **https://publish.obsidian.md/xlabs/Welcome** — the Obsidian vault for research, design-in-progress, and ontology/ER modeling

### What you CANNOT access
- ❌ The hub repository itself (no direct git access)
- ❌ The hub's GitHub Projects board (no board queries or task creation)
- ❌ Other spoke repositories (only your own repo's Issues/PRs)

**Work arrives as Issues/PRs opened in your repo** by the hub's scrum-master or product manager. You don't reach out to the board; the board reaches you.

---

## Your Repository: Layer, Identity, and Ownership

Identify your repository's layer and role:

**Check your layer identity:**
```
cat .agent/layer.json
```

This manifest tells you:
- `system` — the overall platform (e.g., `career-platform`)
- `layer` — your layer (e.g., `api`, `web-ui`, `worker`, `data`, `ml-ai`, `infra`)
- `service` — your service name (e.g., `career-api`)
- `owns` — what you own (e.g., "REST API", "domain services", "API database schema")
- `does_not_own` — what you must NOT own (e.g., "web UI", "mobile app", "personal agent settings")

**What owning a layer means:**
- You implement contract-first: publish OpenAPI, GraphQL, or AsyncAPI specs that other spokes consume.
- You own your code, runtime, and persistence boundary—no direct database access from other layers.
- You run your own CI, deploy independently, and coordinate with other spokes only via published contracts.

See [N-Layer Spoke Rules](n-layer-spoke-rules.md) for full layer standards.

---

## High-Level Goals

The platform vision, in 4 bullets:

1. **Build fast in parallel** — your layer can move independently; no waiting for other spokes.
2. **Contract-first always** — all integration happens through OpenAPI, GraphQL, or AsyncAPI; never through private source imports.
3. **Deploy safely and often** — your layer has its own CI, deploy pipeline, and SLOs.
4. **Isolate and own your data** — your persistence is yours; other layers access it through your API only.

More at [N-Layer Architecture](n-layer-architecture.md).

---

## How Work Reaches You: Your Repository's Issues

**Your task queue lives in this repository's Issues/PRs—not on a GitHub Projects board.**

### Finding your work
1. Go to **Issues** in this repository
2. Filter by open issues (usually already assigned or labeled `layer:YOUR_LAYER`)
3. Look for detailed acceptance criteria and linked decisions in the issue body

### Work item shape
Work arrives as **Epics** or **Features** with:
- Clear acceptance criteria
- Layer and service labels
- Linked decisions (if blocked awaiting a decision)
- Contract changes (if integration is needed)

### Completing work
1. Create a branch and implement the feature
2. Open a PR with a clear title and `Closes #N` link in the body
3. Gather review (Copilot auto-reviews; Claude may do deep review if requested)
4. Merge when ready — the automation closes the linked issue

**There is no GitHub Projects board for you.** Track progress via your repo's Issues list.

---

## Quick Links & Key Resources

| Resource | What it covers |
|---|---|
| [armies-overview.md](armies-overview.md) | How the three armies work and when to use each |
| [agents.md](agents.md) | Full roster of specialists and their skills |
| [CLAUDE.md](CLAUDE.md) | Routing rules and agent chaining patterns |
| [AGENTS.md](AGENTS.md) | Quick reference for your repo's synced agents |
| [n-layer-architecture.md](n-layer-architecture.md) | Hub & spoke model and contract-driven design |
| [n-layer-spoke-rules.md](n-layer-spoke-rules.md) | Layer identity, data boundaries, coordination rules |
| [SAFE.md](safe.md) | Planning structure (PIs, sprints, estimation) |
| [github-projects.md](https://nickpclarke.github.io/AgentArmy/github-projects/) | Hub board coordination (reference only; you won't use this) |
| [Docs site (reality)](https://nickpclarke.github.io/AgentArmy/) | **Orientation key** — full published hub docs |
| [Labs vault (vision)](https://publish.obsidian.md/xlabs/Welcome) | **Orientation key** — Obsidian WIP/design vault |

---

## Next Steps

1. **Know your layer** — read your `.agent/layer.json`
2. **Check your Issues** — see what's assigned to you
3. **Pick an agent** — review [AGENTS.md](AGENTS.md) to find the right specialist for your task
4. **Invoke the agent** — mention the agent by name in your prompt, or use `/skill-name` for shortcuts
5. **Open a PR** — link it to the issue with `Closes #N`
6. **Merge and repeat** — automation closes the issue when the PR merges

---

## Questions?

Read the hub docs at **https://nickpclarke.github.io/AgentArmy/**. Most answers are there. If you hit a blocker or need a decision, comment on the issue and tag the hub's scrum-master or product manager.
