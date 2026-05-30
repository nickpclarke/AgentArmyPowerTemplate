# Platform Layers

The untool.ai platform is built as a set of **layers**, each developed in its own
repository. Those repos are simultaneously (a) spokes generated from the **AgentArmy**
template factory and (b) the building system for the **untool.ai** platform — so their
own docs describe the *platform*, not the template scaffolding.

The pages under this section are **synced from each layer repo's `docs/`** into this site
at build time (see `.github/workflows/deploy-docs.yml`). Each layer remains the single
source of truth for its own documentation; this site aggregates them so the whole platform
reads as one.

| Layer | Repo | Role |
|---|---|---|
| **Frontend Core** | `frontend-core` | UI / BFF — the operator + product surface (Next.js, CopilotKit, fleet console) |
| **Middle Core** | `middle-core` | Agent runtime — model authority, knowledge loop, ontology & data objects |
| **Backend Core** | `backend-core` | Knowledge platform — ArcadeDB, credentials broker, LLM gateway, contracts |

> The AgentArmy (hub) docs describe these layers at the **template** level (how a spoke is
> generated, routed, and synced). The per-layer pages here are the **platform** story.
