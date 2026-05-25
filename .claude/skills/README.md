# Skills

## First-party skills

Authored for AgentArmy (not vendored). Model-invoked — Claude auto-triggers them by context:

| Skill | Description |
|-------|-------------|
| `ufo-ontology` | Model with UFO / OntoUML / gUFO — stereotypes (kind/role/phase/relator…), rigidity & sortality, relator reification, anti-patterns, gUFO OWL, UFO→BFO mapping. The primary authoring discipline. Loaded by `ontologist-ufo`. |
| `bfo-ontology` | Ground in Basic Formal Ontology (BFO 2020, ISO/IEC 21838-2) — continuant/occurrent hierarchy, time-indexed relations, OBO Foundry/CCO/IAO/RO, Common-Logic-vs-OWL, BFO/CCO interop projection, UFO↔BFO mapping. Loaded by `ontologist-bfo`. |

The two share a UFO↔BFO synthesis (mapping table + divergence list) supporting the "offer both / dual projection" design in the Labs vault. See `.claude/agents/categories/12-knowledge-ontology/`.

## Vendored Skills

## obsidian-skills

The following skills are vendored from [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)
(MIT License, Copyright (c) 2026 Steph Ango (@kepano); see [LICENSE](LICENSE)) and follow the
[Agent Skills specification](https://agentskills.io/specification):

| Skill | Description |
|-------|-------------|
| `obsidian-markdown` | Create/edit Obsidian Flavored Markdown (`.md`) — wikilinks, embeds, callouts, properties |
| `obsidian-bases` | Create/edit Obsidian Bases (`.base`) — views, filters, formulas, summaries |
| `json-canvas` | Create/edit JSON Canvas files (`.canvas`) — nodes, edges, groups, connections |
| `obsidian-cli` | Interact with Obsidian vaults via the Obsidian CLI; plugin/theme dev |
| `defuddle` | Extract clean markdown from web pages via the Defuddle CLI (`npm install -g defuddle`) |

To update, re-copy from the upstream repo's `skills/` directory.
