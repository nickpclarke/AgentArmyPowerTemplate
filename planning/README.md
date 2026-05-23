# Template Platform Planning

Strategic planning artifacts for AgentArmy template system evolution.

**This is NOT user documentation.** See `/docs/` for user guides and getting started.

## What's Here

This folder contains **working hypotheses, release train plans, and synthesis work** for how the AgentArmy template platform itself evolves — separate from documentation for users who adopt the template.

## Folders

- **`release-trains/`** — Release train planning (RT1–RT4, 6-month roadmap)
- **`backlog/`** — GitHub Issues management & board population checklist
- **`synthesis/`** — Working synthesis of patterns, integrations, designs (evolving)
- **`roadmap/`** — Strategic direction (6-month platform vision, milestones)
- **`governance/`** — Planning process, naming conventions, artifact lifecycle

## Key Principle

**Work items live on the [GitHub Projects board](https://github.com/users/nickpclarke/projects/1), not in this folder.** Status, SAFE fields (Type, PI, Size, Estimate, Priority, dates), and Epic→Feature hierarchy are stored and tracked on the board. Files here must not duplicate that — they hold the *durable strategy* (themes, dependencies, rationale) and point to the board for live state.

Documents here are **working hypotheses and planning artifacts**. They may evolve, be revised, or move to `/docs/` once stable and user-relevant.

## Quick Navigation

- **The live work backlog?** → [GitHub Projects board](https://github.com/users/nickpclarke/projects/1)
- **Board fields, SAFE mapping & views?** → [`/docs/github-projects.md`](../docs/github-projects.md)
- **Starting a release train?** → `release-trains/release-train-index.md`
- **Populating the board (forks)?** → `backlog/board-population-checklist.md`
- **Creating new planning documents?** → `governance/FILE_ORGANIZATION.md`
- **Strategic 6-month vision?** → `roadmap/PLATFORM_ROADMAP.md`
- **ArcKit patterns integration?** → `synthesis/ARCKIT_SYNTHESIS.md`

## Artifact Lifecycle

| Phase | Location | Status | Audience | Lifespan |
|---|---|---|---|---|
| Discovery | `synthesis/` | Drafting | Planning team | Days–weeks |
| Specification | `release-trains/`, `roadmap/` | Decided | Entire team | Months |
| Public | `/docs/` | Stable | New users, community | Ongoing |
| Archive | `archive/` | Reference | Historical context | Permanent |

See `governance/FILE_ORGANIZATION.md` for detailed guidance on where to put new documents.

---

**Last Updated:** 2026-05-23

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
