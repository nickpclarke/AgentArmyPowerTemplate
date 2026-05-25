---
name: "Epic Handoff"
about: "Hub PM/scrum-master uses this to hand an epic to a spoke repo. Opened IN the spoke, not the hub."
title: "[EPIC] "
labels: ["Epic", "agent-army-task"]
---

<!-- Hub: fill every section before opening this issue in the spoke repo. -->
<!-- Spoke agents: decompose this into Stories/Enablers as child issues, then close with PRs using `Closes #N`. -->

## Epic goal / why

<!-- One-paragraph statement of the outcome and the business/user value. Link the hub Epic issue for full context. -->

Hub epic: <!-- https://github.com/nickpclarke/AgentArmy/issues/N -->

## Target layer and repo

| Field | Value |
|---|---|
| Spoke repo | <!-- e.g. frontend-core, backend-core, middle-core --> |
| Layer role | <!-- e.g. REST API, graph model, UI shell --> |
| Owning team | <!-- Claude Code / Copilot / mixed --> |

## Scope

**In scope**

- <!-- feature or behaviour the spoke must deliver -->

**Out of scope**

- <!-- explicitly excluded; avoids scope creep -->

## Acceptance criteria

- [ ] <!-- observable, testable outcome -->
- [ ] <!-- observable, testable outcome -->
- [ ] <!-- observable, testable outcome -->

## Contracts and interfaces

<!-- List every OpenAPI spec, AsyncAPI schema, GraphQL type, or shared-type package this epic touches or produces. Spoke agents must not break existing contracts without a versioning plan. -->

| Artifact | Location | Change type |
|---|---|---|
| <!-- OpenAPI spec --> | <!-- path or URL --> | <!-- new / extend / no change --> |

## Dependencies

<!-- Cross-spoke or external blockers. Link the blocking issue. -->

| Dependency | Spoke / system | Blocking? | Issue |
|---|---|---|---|
| <!-- e.g. backend-core auth endpoint --> | <!-- backend-core --> | <!-- yes / no --> | <!-- #N --> |

## Reference links

- Hub docs site: <https://nickpclarke.github.io/AgentArmy/>
- Hub Obsidian vault: `obsidian/` in the hub repo (clone or browse on GitHub)
- Hub planning: `planning/release-trains/release-train-index.md`

## Suggested agent routing

<!-- Adjust to the spoke's actual stack. -->

| Work type | Suggested agent |
|---|---|
| Architecture / ADR | `architect-reviewer` |
| Implementation (complex / multi-file) | `agent-army-task` label → Claude Code specialist |
| Implementation (bounded / single-file) | `copilot-task` label → Copilot coding agent |
| Contract design | `api-designer` |
| Security review | `security-auditor` |

## Definition of Done

- [ ] All acceptance criteria above are checked
- [ ] Every child Story/Enabler issue is closed via a merged PR containing `Closes #N`
- [ ] Contracts (OpenAPI/schema) updated or confirmed unchanged
- [ ] Spoke milestone marked closed
- [ ] Hub notified (comment on hub Epic issue with link to spoke milestone)
