# Labs & the Idea Pipeline

AgentArmy designs flow through **three surfaces**, from raw idea to published doc. Each has a distinct job; commitment and visibility rise top → bottom.

| Stage | Surface | Holds | Where |
|---|---|---|---|
| 1 · Skunkworks & Labs (WIP) | **Obsidian vault (in-repo)** | research, ideation, shared design-in-progress, ontology / entity-relationship modeling | `obsidian/labs/AgentArmyLabs/` (committed) · humans also at https://publish.obsidian.md/xlabs |
| 2 · Work | **Project board** | committed tasks, status, who's-doing-what | [Project #1](https://github.com/users/nickpclarke/projects/1) |
| 3 · Docs | **this site** | completed, stable documentation | you're here |

## Why the vault is in the repo

The WIP design surface lives **in the repository** at `obsidian/labs/AgentArmyLabs/`, not the GitHub Wiki. A wiki is a *separate* git repo that cloud coding agents (Codex, Copilot) never receive in their microVM sandbox — so it cannot be a shared agent surface. The vault is part of the normal checkout, so **every agent (Claude, Codex, Copilot) can read and edit it**, and it is version-controlled and reviewable like any other code.

Only the note content is tracked. Per-user app state (`.obsidian/`) and the deleted-notes folder (`.trash/`) are gitignored.

## How a design matures

- **Skunkworks & Labs — Obsidian vault.** Ideas are born and shared here; the graph view is the thinking tool, ideal for ontology and entity-relationship work. Agents write to it using the Obsidian skills (markdown, wikilinks, bases, canvas) and collaborate via PRs to `obsidian/labs/`. Humans use the Obsidian app and the published mirror at **https://publish.obsidian.md/xlabs**.
- **Work — Board.** Once committed as a task on [Project #1](https://github.com/users/nickpclarke/projects/1), with intent and status.
- **Docs — this site.** Once a design is stable, a summary graduates here (MkDocs).

## Ontology has a destination

Entities and relations are modeled in the **Obsidian vault** (the graph) → and graduate into **ArcadeDB** vertex/edge schema and the **OpenAPI contract** (the universal data adapter's common data model). The vault is where the graph is *designed* and *agreed*; ArcadeDB is where it *runs*; `docs/` is where the stable summary is *published*.

> **Retired:** the GitHub Wiki is no longer the Labs surface — microVM agents can't reach it. Its pages were migrated into the in-repo vault (see [Ontology Pipeline](https://github.com/nickpclarke/AgentArmy/blob/main/obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md)).
