# Glossary

## Armies & Agents

**Army** — A specialized group of AI agents that operate together. AgentArmy has three armies: Claude Code, GitHub Copilot, and dlt.

**Agent** — A single AI specialist with expertise in a specific domain (e.g., `react-specialist`, `dlt-engineer`). See [agents.md](agents.md) for the full roster.

**Agent Distinctiveness** — Property of agents that they are semantically non-overlapping (MECE). Each agent handles a specific, well-defined scope without duplication.

**MECE** — Mutually Exclusive, Collectively Exhaustive. Framework for organizing agents so routing is unambiguous and complete coverage is guaranteed.

**Specialist** — A Claude agent with deep expertise in a narrow domain (e.g., `postgres-pro`, `kubernetes-specialist`). Distinguished from generalist agents.

## GitHub Projects & Workflow

**GitHub Projects v2** — Beta GitHub feature providing a shared task board with custom fields. Single source of truth for all armies.

**Issue** — A unit of work tracked on GitHub Projects. Has Type, Size, Estimate, PI, Status, etc.

**PR (Pull Request)** — Code change proposed for merge. Must link back to issue with `Closes #N`.

**Type** — Custom field on issue: Epic, Feature, Story, Enabler, Bug, Spike, Decision. Defines hierarchy and kind of work.

**Size** — Custom field on issue: XS, S, M, L, XL. T-shirt estimate for routing and effort prediction.

**Estimate** — Custom field on issue: Story points (1,2,3,5,8,13). Fibonacci scale for velocity tracking.

**Priority** — Custom field on issue: P0 (must ship this sprint), P1 (should ship this PI), P2 (backlog).

**PI (Program Increment)** — ~10-week planning horizon with a goal, multiple sprints, and quarterly business review. Tracked as GitHub Milestone.

**Status** — Field tracking work state: Todo → Ready → In Progress → In Review → Done, with **Awaiting Decision** as a hold state when a HITL decision is required. The `auto-status` workflow sets In Progress on PR open and Done on PR merge (with `Closes #N`); Ready and In Review are set manually.

**Iteration** — 2-week sprint. Assigned to issues during sprint planning.

**Acceptance Criteria** — Definition of what "done" means for a Story. Written as checklist in issue body.

**Definition of Ready (DoR)** — Criteria issue must meet before work starts: Type, PI, Size, Estimate, acceptance criteria set.

**Definition of Done (DoD)** — Criteria before issue can move to Done: Code merged, tests passing, `Closes #N` in PR body.

## SAFe Framework

**SAFe** — Scaled Agile Framework. Hierarchical planning model: Portfolio → Program → Team, across multiple PIs.

**PI Planning** — Quarterly event where features are estimated, prioritized, and assigned to sprints. Output: PI Goal and committed stories.

**Velocity** — Average story points completed per sprint. Used to forecast PI capacity.

**Backlog Grooming** — Refinement session where upcoming stories get Size and Estimate.

**Sprint Goal** — Outcome a team commits to in a 2-week sprint. Measured by completed stories.

**Release Train** — All teams executing within a PI. Coordinated through Program Increment.

## Armies & Specialization

**Claude Code Army** — Deep, local, strategic. Handles architecture, large features, security audits. Response time: hours to days.

**GitHub Copilot Army** — Fast, GitHub-native, lightweight. Handles PR review, simple tasks (XS/S), board queries. Response time: minutes to hours.

**dlt-engineer** — Claude Code specialist agent for data pipelines. Handles ETL/ELT, incremental loading, schema evolution, source connector development, and destination wiring. Part of the Claude Code army.

**Copilot Coding Agent** — GitHub Copilot automation that takes `copilot-task` labeled issues and auto-implements them.

**Copilot Review** — GitHub Copilot that provides first-pass PR review on all PRs.

**Board Manager Extension** — Azure-deployable Copilot Chat extension for querying GitHub Projects board via `@board-manager`.

## Data & Pipelines

**dlt** — "data load tool." Lightweight Python framework for ETL/ELT: extraction, incremental loading, schema inference, destination wiring.

**ETL** — Extract, Transform, Load. Data pipeline pattern: pull from source, transform, push to destination.

**ELT** — Extract, Load, Transform. Modern variation: pull from source, push to data warehouse, transform in place.

**Incremental Loading** — Loading only new/changed data since last run. Opposed to full reload. More efficient, lower latency.

**Schema Evolution** — Handling changes to data structure over time. Adding columns, changing types, etc.

**Source Connector** — dlt abstraction for extracting from an external system (API, file, database).

**Destination** — Where data lands: DuckDB, BigQuery, Snowflake, Postgres, Parquet files, etc.

## Architecture & Enterprise

**Architecture Decision Record (ADR)** — Document explaining a significant architecture decision, its alternatives, and rationale. Written as MADR v4.0 format.

**Capability Map** — Business capability model. Hierarchical decomposition of "what the business does" into abstract capabilities.

**Wardley Map** — Strategic map showing: user needs, value chain, component evolution (genesis → custom → product → commodity), organizational doctrine.

**TOGAF** — The Open Group Architecture Framework. Enterprise architecture methodology with ADM (Architecture Development Method).

**Enterprise Architecture** — Holistic approach to designing organizations, information systems, and technology strategy across multiple PIs.

**Zero Trust Architecture** — Security model: never trust, always verify. Every access request is authenticated and authorized.

## Development & CI/CD

**Branch** — Named commit history. Feature branches isolate work; main is production-ready.

**Merge** — Integrating changes from one branch to another.

**Rebase** — Reorganizing commits on top of another branch. Cleaner history than merge.

**CI/CD** — Continuous Integration / Continuous Deployment. Automated pipeline: test on push, deploy on merge.

**Workflow** — GitHub Actions workflow. Automation triggered on events (push, PR, schedule).

**Auto-merge** — Automatically merge PR when all conditions met (tests passing, reviews approved, checks green).

**Pre-commit Hook** — Code that runs before commit. Used to lint, format, validate.

## Code & Technical

**Refactoring** — Restructuring code without changing behavior. Improves readability, testability, performance.

**Monolith** — Single large application. Opposed to microservices (decomposed into independent services).

**Microservices** — Architecture pattern: independent, loosely-coupled services with separate databases.

**Async/Await** — Programming pattern for handling asynchronous operations (network, I/O) without blocking.

**Type Safety** — Language feature ensuring type mismatches are caught at compile time, not runtime.

**Idiomatic** — Following language conventions and best practices. E.g., "idiomatic Python" means Pythonic code.

**Performance Bottleneck** — Code or infrastructure point that limits system throughput or latency.

**Observable** — System that emits metrics, logs, traces. Enables root cause analysis and alerting.

---

## Related Docs

- **[Armies Overview](armies-overview.md)** — Three armies model
- **[GitHub Projects](github-projects.md)** — Board field reference
- **[SAFe Framework](safe.md)** — PI planning details
- **[FAQ](faq.md)** — Answers to common questions
