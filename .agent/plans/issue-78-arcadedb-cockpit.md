# ExecPlan: ArcadeDB Cockpit Extension

Issue: https://github.com/OWNER/AgentArmyPowerTemplatePowerTemplate/issues/78

## Goal

Build a self-contained local cockpit for the ArcadeDB container used by the `claude/recursing-liskov-36b46a` worktree. The cockpit should make the database feel explorable: graph navigation, schema/sample inspection, query execution, and lightweight instrumentation in one browser surface.

## Context

AgentArmyPowerTemplate is a template repository, so this work belongs in an optional extension rather than application source. The Claude worktree currently uses ArcadeDB at `http://localhost:2480`, database `knowledge`, and default test credentials managed by local environment variables.

## Non-goals

- Do not couple this extension to the unfinished platform branch.
- Do not commit personal credentials or provider keys.
- Do not mutate the database by default from the query console.
- Do not replace ArcadeDB Studio; this is a fast local navigation and instrumentation cockpit.

## Source-of-Truth Files

- `AGENTS.md`
- `planning/backlog/BACKLOG_ISSUES_INDEX.md`
- `docs/github-projects.md`
- `.claude/worktrees/recursing-liskov-36b46a/platform/docker-compose.yml`
- `.claude/worktrees/recursing-liskov-36b46a/platform/backend-core/app/arcade.py`
- `.claude/worktrees/recursing-liskov-36b46a/platform/backend-core/app/store.py`

## Subagents To Use

No delegated subagents in this implementation pass. The user asked for a separate branch and build; local context is enough for a bounded optional extension.

## Work Breakdown

1. Create `codex/arcadedb-cockpit` branch.
2. Create GitHub issue #78 for board traceability.
3. Add `extensions/arcadedb-cockpit/` with:
   - Node HTTP server and ArcadeDB proxy.
   - Static cockpit UI.
   - README and `.env.example`.
4. Keep connection defaults compatible with the local ArcadeDB container.
5. Add validation scripts that do not require installing dependencies.

## File Ownership

- Owner: `extensions/arcadedb-cockpit/**`
- Owner: `.agent/plans/issue-78-arcadedb-cockpit.md`

Do not edit the Claude worktree files.

## Tests and Validation

- `node --check extensions/arcadedb-cockpit/server.js`
- `node --check extensions/arcadedb-cockpit/public/app.js`
- Start the server locally when practical and verify `/api/config`.
- Browser verification is best-effort if ArcadeDB is running locally.

## Risks

- ArcadeDB schema introspection can vary by version; the extension should degrade to known demo types (`Chunk`, `StoredObject`, `IngestJob`) if metadata queries fail.
- Local ArcadeDB may not be running during validation; the UI must show an offline state instead of crashing.
- Query console must default to read-only SQL unless explicitly enabled by environment variable.

## Decision Log

- Use a dependency-free Node server to avoid introducing package install friction.
- Put the cockpit in `extensions/arcadedb-cockpit/` so it is clearly optional template tooling.
- Use server-side Basic auth to keep ArcadeDB credentials out of browser JavaScript.
