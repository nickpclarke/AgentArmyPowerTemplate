# CLAUDE.md

AI assistant guidance for the AgentArmy template repository.

## What This Repo Is

AgentArmy is a starter template for AI-powered software development. It coordinates two autonomous AI armies and a shared planning surface:

- **Claude Code army** — local, deep, strategic: architecture, complex features, SAFE planning, security audits
- **GitHub Copilot army** — GitHub-native, fast, lightweight: PR review, simple task coding, board queries via `@board-manager`
- **GitHub Projects v2** — shared coordination plane both armies read and write
- **GitHub Actions** — routes issues to the right army, syncs board state, automates ceremonies
- **SAFE** — the planning model at team and program level

All significant work is tracked as GitHub issues on the project board. Agents operate as specialists — delegate to the right agent, in the right army, rather than doing everything generalist.

## Hub vs Spoke Mode (N-Layer)

AgentArmy is intended to be used as a **Hub template** that generates many **Spoke repos** (one per layer: UI, API, worker, mobile, infra, etc.).

- **If you are in the Hub repo** (the AgentArmy template itself): treat deliverables as template artifacts (workflows in `.github/workflows/`, agent definitions in `.claude/agents/`, docs in `docs/`, and root config). Do not assume an application exists.
- **If you are in a Spoke repo** (a layer repo created from this template): treat the repository as the *actual layer implementation*. Prefer contract-first changes (OpenAPI/GraphQL/AsyncAPI/shared types), use mocks/stubs for parallel work, and integrate “late” via environment variables instead of tight repo-to-repo coupling.

When in doubt, infer intent from the issue/task context (e.g., “update the template” vs “implement the API/UI/worker”), and ask for clarification if the repo’s role is ambiguous.

## Repository Layout

```
.claude/agents/categories/  → specialist agent definitions (12 categories)
.claude/commands/           → local slash commands (/wardley, /ea-adr, /capability-map)
.claude/skills/             → vendored Agent Skills (Obsidian: markdown/bases/canvas/cli/defuddle)
.github/workflows/          → GitHub Actions: auto-status, routing, agent-onboarding-validation
docs/                       → user-facing docs: agents.md, setup.md, github-projects.md, capabilities
extensions/board-manager/   → Azure-deployable Copilot Chat extension (@board-manager)
planning/
  ├── release-trains/       → RT1–RT4 strategic roadmap & issue planning
  ├── backlog/              → GitHub Issues index, board population checklist
  ├── synthesis/            → ArcKit integration, research artifacts
  ├── roadmap/              → Platform 6-month vision
  ├── governance/           → FILE_ORGANIZATION.md (folder strategy)
  └── meta/                 → Governance layer: principles, agent validation, learning loops
```

## Working in This Repo

### GitHub Projects is the task backbone

**Default — check Issues AND the PRs that reference them FIRST, always.** Before starting work, creating/closing/duplicating an issue, or opening a PR, do BOTH: (a) list open Issues (the board in the hub; `gh issue list` in a spoke) and pick up / align with an existing one; (b) **list open PRs that reference candidate issues** (`gh pr list --search "linked:issue/N"` or read PR bodies for `Closes #N`/`supersedes #M`) BEFORE marking duplicate / closing. A PR in flight against an issue is the strongest "not a duplicate" signal — two issues with one open PR each are two architectural *tracks*, not duplicates. Create a new issue only if no Issue and no in-flight PR covers the work.

Before starting significant work, check whether an issue exists on the board. If not, create one and add it to the project. Use `gh` CLI:

```bash
# Create an issue and add to project
gh issue create --title "..." --body "..." --label "Feature"
gh project item-add 1 --owner OWNER --url "https://github.com/OWNER/AgentArmy/issues/N"
```

Set the `Type` and `PI` fields on items so they're properly categorised.

### Poll for work with a recurring loop

For long-running, autonomous sessions, keep a heartbeat on the board with the `/loop` skill so new work and PR feedback are picked up without a human re-prompting:

```
/loop 5m check GitHub for new issues and PR activity, then pick up the next ready item
```

Each cycle should:

1. **Issues** — list open issues (hub: the Projects board, `gh project item-list 1 --owner OWNER`; spoke: `gh issue list` filtered to your labels) and start the next *Ready* / unblocked item that isn't already assigned or *In Progress*.
2. **PR activity** — for your open PRs, check review comments and CI (`gh pr status`, `gh pr checks`) and address actionable feedback, or let the `review-loop` label drive the auto-fix flow.
3. **Stop when idle** — exit the loop once the queue is empty or when told to; don't spin on a clean board.

Tune the interval (`5m` / `10m` / `15m`) to trade responsiveness against token/API cost — `/loop` defaults to `10m` if you omit the duration. `/loop` is a Claude Code skill; other agents in the fleet don't have it.

### Contract-first & mock-first (always)

**Every contract goes up, and every contract gets a mock — proactively, up front, not on request.** This is a standing rule. The fleet integrates across sandboxed spokes only via contracts (OpenAPI/AsyncAPI/GraphQL/shared types), so a live mock per contract is what lets every layer build in parallel *before* the real producer exists.

- **Publish + mock in the paid Postman** — the **AgentArmy** workspace (`64b63429-ed44-4078-861a-c8867742eaf4`; PMAK in Key Vault `POSTMANTOKEN`, see [docs reference]). Whenever a contract/endpoint/spike defines or changes a contract: publish/refresh the spec **and** create/refresh its mock immediately, then hand the mock URL to consumer spokes as the "reachable producer endpoint."
- **Don't wait to be asked.** Standing up the spec + mock is part of producing the contract, not a follow-up.
- **Mock caveat:** Postman mocks return 200 regardless of auth/headers — fine for shape/dev and parallel unblocking, but JWT/authz assertions must verify against the **real** producer, not the mock (don't let mock-backed tests pass falsely).
- A pure **data-model** contract (e.g. middle-core MCR-F4 `data-platform-contract.g.json`) needs an HTTP read surface *designed* (OpenAPI, via `api-designer`) before it can be mocked — that design is the producer-mock enabler, not a blocker to skip.

### Contract inventory & dispatch — SOP (recurring, not ad-hoc)

Run this **as a loop**, not reactively. Each cycle (and whenever a contract is added/changed):

1. **Inventory** — enumerate contract artifacts across hub + all spokes (`contract*/`, `*.openapi.*`, `*.asyncapi.*`, generated `*.g.json`) and build the producer→consumer matrix.
2. **Check each contract is fully landed** — (a) source-of-truth in the producer repo, (b) **vendored into every consumer** repo, (c) **published + mocked** in Postman (per Contract-first & mock-first), (d) **consumed** (generated client wired, not raw fetch), (e) **registered in [docs/contracts.md](docs/contracts.md)**.
3. **Each gap → a dispatched issue** in the owning repo with a routing label (`copilot-task` mechanical / `agent-army-task` bigger) + `Enabler`. This is how you "get the team busy."
4. **Fan out via the orchestration layer, not by hand** — delegate the cross-repo dispatch to an orchestration/`general-purpose` agent (it checks each repo's labels + avoids duplicates), and let the two armies (Copilot via `copilot-coding-agent`, Claude via `@claude`) execute. Don't hand-crank issue creation in the main context.
5. **Keep [docs/contracts.md](docs/contracts.md) the single registry** — update it whenever a contract is added, vendored, or changes status.

### Fleet heartbeat (automated inventory + dispatch)

The SOP above is automated by **`tools/fleet-heartbeat.mjs`** — the fleet's "heart." It inventories contracts, detects drift (unvendored contracts, agent-pack sync, missing PR-event workflows), checks repo health, and optionally dispatches gaps as deduped issues. Three run modes — pick your autonomy level:

| Mode | What it does |
|---|---|
| `node tools/fleet-heartbeat.mjs` | **dry-run** (default) — inventory + report only; files nothing, spawns nothing |
| `node tools/fleet-heartbeat.mjs --apply` | files a deduped issue per hard gap as **`agent-army-task`** (waits for `/loop`/human; no worker spawns) |
| `node tools/fleet-heartbeat.mjs --apply --auto` | files gaps as **`copilot-task`** → Copilot coding agent **auto-spawns** to fix each |

It runs three ways: the **SessionStart hook** (dry-run, every local session), a **scheduled cloud routine** (daily cron, off the Actions cap), and ad-hoc via **`/loop`**. Only the heartbeat dispatches, so spawning is a finite tree (heart → issues → workers → PRs → review bots), never a recursive cascade. **Full reference, the scheduled-routine config, and the dry-run → `--apply` → `--auto` graduation path: [docs/fleet-heartbeat.md](docs/fleet-heartbeat.md).**

### Route work to the right army first, then the right agent

**Copilot army:** apply a label and let automation handle it — `copilot-task` (Size XS/S Bug/Story) creates a branch + PR; PRs get auto-review; board questions use `@board-manager` in Copilot Chat.

**Claude Code army:** delegate to the right specialist. The **full concern→agent table, cross-cutting clusters (contract / delivery-ops / knowledge / data-vault), and TOGAF EA specialist roster** live in [docs/agent-routing.md](docs/agent-routing.md) — load that doc when you need to pick an agent. The behavioral rules below are what live in this file.

**Cluster anchors** (use these when scoping a task, then pick the specific agent from agent-routing.md):

- **Contract cluster:** `api-designer` → `contract-test-engineer` → `schema-migration-engineer`.
- **Delivery/ops cluster:** `devops-engineer` → `deployment-engineer` → `release-manager` → `observability-engineer` → `sre-engineer` → `finops-engineer` → `api-gateway-engineer`.
- **Knowledge/ontology cluster** (formality gradient): `taxonomist` → `ontologist-generalist` → `ontologist-ufo` / `ontologist-bfo` → `knowledge-engineer`. See [.claude/agents/categories/12-knowledge-ontology/README.md](.claude/agents/categories/12-knowledge-ontology/README.md).
- **Data Vault cluster** (lifecycle): `data-vault-architect` → `data-vault-modeler` → `data-vault-engineer`. Anchor: [ARC-ADR-026](docs/decisions/ARC-ADR-026-data-vault-2-1-methodology.md). Strategy: [docs/data-vault/](docs/data-vault/).

**HITL escalation:** when an agent hits a creative fork or judgment call beyond its authority, route to `hitl-coordinator` (creates a Decision Artifact on the board). See HITL Decision Pattern below.

**Local docker fleet:** use the **untool fleet suite** (`mcp__local-fleet__fleet_*`). Read-only tools (`fleet_ps` / `fleet_inspect` / `fleet_logs`) are auto-approvable; write tools (`fleet_up` / `fleet_down` / `fleet_restart` / `fleet_build` / `fleet_deploy`) require per-call approval — they execute arbitrary code in the operator's docker host. See [tools/mcp-local-fleet/README.md](tools/mcp-local-fleet/README.md).

### Meta-Planning & Governance (ARMY_PRINCIPLES)

The agent army operates under **7 foundational principles** defined in `/planning/meta/principles/ARMY_PRINCIPLES.md`:

1. **Error Escalation** — Every agent escalates failures to `error-coordinator`
2. **Knowledge Feedback** — Agents feed insights to `knowledge-synthesizer`
3. **Skill Scaffolding** — Reusable, composable skills exposed by agents
4. **Hook Integration** — Agents listen to session lifecycle events
5. **Delegation Direction** — Down-hierarchy only, no UP-delegation, no circular references
6. **MECE** (Mutual Exclusive, Collectively Exhaustive) — Boundary rules disambiguate routing
7. **Observable Decisions** — Decision-making is logged and queryable

**New agents must pass `AGENT_ONBOARDING_RUBRIC.md` before merge**, which operationalizes these principles. See `/planning/meta/decisions/AGENT_ONBOARDING_RUBRIC.md` for validation checklist.

**Planning structure (3 layers):**

| Layer | Location | Purpose | Cadence |
|---|---|---|---|
| **Tasks** | GitHub Projects board | Issue tracking, sprints, burndown | Per-sprint |
| **Strategy** | `/docs/release-trains/` | Feature delivery roadmap (RT1–RT4) | Quarterly |
| **Governance** | `/planning/meta/` | Principles, agent validation, learning loops | Quarterly + continuous |

**For fork users (Spokes):** See `/planning/meta/spoke-templates/SPOKE_META_PLANNING_TEMPLATE.md` for how to inherit Hub principles while customizing for your layer.

### Language Specialists Routing Rules (Category 02)

Four tiers: **Languages/** (idioms, type system, runtime), **Frameworks/web/** (app with a web framework + ORM), **Frameworks/mobile/** (React Native / Flutter), **Platforms/** (version-pinned .NET, OS-bound PowerShell). Pick **Languages** for language semantics and **Frameworks** for app-with-framework work — chain both when needed (e.g. `python-pro` design → `fastapi-developer` implementation).

Full tier table, 15+ concrete examples, tie-breakers, and edge cases (JS/TS, .NET versions, mobile): [.claude/agents/categories/02-language-specialists/TAXONOMY.md](.claude/agents/categories/02-language-specialists/TAXONOMY.md). Full agent roster: [docs/agents.md](docs/agents.md). Copilot setup: [docs/copilot.md](docs/copilot.md).

### Design system (frontend-core is the source of truth)

All UI, visual, and **graph / data-viz** work pulls from the shipped frontend-core design
system — **never invent a palette or ad-hoc colors.** Source of truth:

- **`frontend-core/app/theme.css`** — canonical light/dark token set (WCAG-AA audited):
  `--color-bg / -surface / -text / -muted / -border / -primary / -accent / …`. Dark is the
  default; light/dark switch via the `[data-theme="dark"]` attribute.
- **`frontend-core/app/untool.css`** — the **data-viz bridge** (`--ut-ink`, `--ut-accent`,
  `--ut-ok`, `--ut-warn`, `--ut-data-up/-down`). Use these for charts and graph node coloring.
- **`frontend-core/contract/design-tokens.json`** — W3C DTCG tokens (brand primary `#0066ff`,
  purple `#7c3aed`); this is the **FE-1 design-tokens contract** ([docs/contracts.md](docs/contracts.md)),
  vendored to consumers. `frontend-core/app/tailwind.css` + `components.json` wire shadcn/ui (OKLch).
- Richer design material (handoffs, prototypes) lives under `frontend-core/design_handoff_*/`.

In spirit: Tailwind **slate** base (`#0f172a`/`#1e293b`/`#e2e8f0`), **blue/cyan** primary
(`#60a5fa`/`#38bdf8`), brand **purple**, semantic green/amber/red. Route visual work to
**`ui-designer`** (design direction) → **`frontend-developer`** (implementation). Worked example
that consumes these tokens: the self-model graph viewer (`ontology/platform-self-model/viz/`).

### Issue type conventions

Label every issue with its SAFE type:

| Label | Meaning | Typical hierarchy |
|---|---|---|
| `Epic` | Large body of work (>1 PI) | Top level — no parent |
| `Feature` | Deliverable capability within a PI | Child of Epic milestone |
| `Story` | User-facing value, completable in 1 sprint | Sub-issue of Feature |
| `Enabler` | Technical infrastructure or exploration | Same level as Story |
| `Bug` | Defect | Same level as Story |
| `Spike` | Time-boxed research | Same level as Story |
| `Decision` | HITL decision artifact — requires human or AI-app judgment | Created by `hitl-coordinator`; blocks linked issues |

### PR conventions

PR body must contain `Closes #N`, `Fixes #N`, or `Resolves #N` to trigger the `auto-status` workflow. This is what moves issues from *In Progress* to *Done* automatically.

**Autonomous review loop:** add the `review-loop` label to a PR to have Claude auto-address Gemini/Copilot/Codex review comments until the PR is clean (or it escalates to HITL at the round cap). See [docs/pr-review-loop.md](docs/pr-review-loop.md).

**Getting AI second opinions (cap-free — any agent/model can do this):** to get review on a PR, **`@`-mention an AI reviewer in a PR/issue comment** — no human and no GitHub Actions needed. Preferred reviewers:
- **`@copilot`** — ample capacity (Copilot Pro+); also auto-requested on PRs via `copilot-review.yml`. Runs on Copilot's infra, off the Actions minutes cap.
- **`@codex`** — reliable; `@codex review` to review, `@codex address that feedback` to have it push fixes. Off the Actions cap.
- **`@gemini-code-assist`** — daily-quota-limited and the quota **cannot be raised**, so don't depend on it; it reviews only when quota allows.
- **Avoid `@claude` for routine second opinions** — it runs via `claude.yml` on GitHub Actions and **burns the metered minutes cap**. Reserve it for when you want Claude to actually edit/commit.

> Open question: whether a `@copilot` mention can pin a specific model (Copilot model selection, e.g. Opus 4.6) for the review — Copilot's automated PR review may use a fixed model regardless. Test before relying on per-mention model pinning.

## ADR numbering — never hand-pick a number

ADRs live in `docs/decisions/ARC-ADR-NNN-<slug>.md`. **Do not choose `NNN` yourself.** Picking "highest existing number + 1" is a read-modify-write race that collides when sessions run in parallel — it bit ARC-ADR-038/040 twice. Instead:

- **Author** new ADRs as `docs/decisions/ARC-ADR-DRAFT-<slug>.md`, using the literal token `ARC-ADR-DRAFT` wherever the number would go (title heading + `ID` field). Inside the draft's own file the bare token is fine; to link the draft *from another file*, use its full `ARC-ADR-DRAFT-<slug>` stem (only full-stem refs are rewritten repo-wide — a bare token elsewhere is left dangling). Scaffold with `node tools/data-vault/adr-scaffold.mjs --topic "..." --category <cat>` or `/ea-adr` — both emit a draft.
- **Merge-time assigner** (`.github/workflows/adr-assign-numbers.yml`) allocates the next integer on push to `main`, renames the file, and rewrites the token + cross-references. Allocation is serialized (one run at a time), so it cannot collide.
- **PR guard** (`.github/workflows/adr-number-guard.yml`) fails any PR where two decision files share an `ARC-ADR-NNN` prefix — the backstop for accidental hand-numbering.

Full reference: [docs/decisions/README.md](docs/decisions/README.md).

## HITL Decision Pattern

When an agent hits a creative fork, architectural divergence, or judgment call exceeding its authority, it escalates to `hitl-coordinator` which creates a **Decision Artifact** issue on the board.

**Decision Artifact lifecycle:**
1. Agent calls `hitl-coordinator` → Decision issue created with `hitl-decision` label, `Decision` Type, Status = "Awaiting Decision"
2. Blocked issues get `awaiting-human` label and a comment linking the decision
3. Assignee (human or AI app) reviews, comments with choice, closes the issue
4. Automation unblocks linked issues, posts decision context, resets Status to "Todo"

**Board commands for decisions:**
- `/decisions` — list all open Decision Artifacts grouped by assignee type (human / copilot / claude-app / gemini-app)
- Filter board by Status = "Awaiting Decision" or Label = `hitl-decision` to find items needing attention

**Assignee labels** (for board filtering):
- `assignee:human` (soft purple) — specific human
- `assignee:copilot` (Copilot blue) — GitHub Copilot
- `assignee:claude-app` (Claude amber) — Claude GitHub App
- `assignee:gemini-app` (Gemini blue) — Gemini GitHub App

**When agents should escalate:** multiple valid design paths with strategic/values implications, architectural divergence, risk acceptance, scope changes, priority conflicts. See `hitl-coordinator` agent and [docs/hitl.md](docs/hitl.md) for the full pattern.

## GitHub Projects Field Reference

| Field | When to set |
|---|---|
| `Status` | Auto-managed by Actions; only override manually if needed. Flow: Todo → Ready → In Progress → In Review → Done, plus **Awaiting Decision** (HITL hold). `auto-status` sets In Progress on PR open and Done on merge; Ready and In Review are set manually. |
| `Type` | Set on creation |
| `PI` | Set to current Program Increment (e.g. `PI-1`) |
| `Priority` | P0 = must ship this sprint; P1 = should ship this PI; P2 = backlog |
| `Size` | T-shirt estimate: XS ≤ 0.5 day, S ≤ 1 day, M ≤ 3 days, L ≤ 1 week, XL > 1 week |
| `Estimate` | Story points (Fibonacci: 1, 2, 3, 5, 8, 13) |
| `Iteration` | Assign to the sprint when committed |
| `Start date` / `Target date` | Set during sprint planning |
| `Parent issue` | Link Stories to their parent Feature |

## Local debugging — log multiplexer + tunnel

End-to-end agentic loops are noisy across three processes. Use **`tools/tail.mjs`** as the single surface for live tail, on-disk NDJSON, and historical query. Logs land in `tools/logs/{service}.log.YYYY-MM-DD` (gitignored, NDJSON, daily rotation) and every invocation purges files older than 3 days.

```bash
node tools/tail.mjs spawn                 # supervise front+middle+back, capture stdout to NDJSON + terminal
node tools/tail.mjs tail                  # follow today's files (services started elsewhere)
node tools/tail.mjs query --since 5m --level error                # last 5 min, errors only
node tools/tail.mjs query --grep tavily --service middle          # search across logs
node tools/tail.mjs clean --days 1        # tighten retention
```

**Public URL (phone testing, webhooks)** — use **`tools/tunnel.mjs`**, a vendor-agnostic wrapper over cloudflared (default) / ngrok. State persists in `tools/.tunnel-state.json` so commands work across shells:

```bash
node tools/tunnel.mjs start               # cloudflared → trycloudflare.com URL
node tools/tunnel.mjs start --vendor ngrok # if you've added a paid reserved subdomain
node tools/tunnel.mjs url                 # just print the public URL
node tools/tunnel.mjs status              # vendor, pid, url, since
node tools/tunnel.mjs logs --lines 50     # tail today's tunnel log
node tools/tunnel.mjs stop                # kill agent, clear state
```

**Tunnel policy:** the tunnel exposes **frontend only** (`:3000`). Middle (`:8100`) and backend (`:8000`) stay on localhost behind the Next.js BFF at `/api/copilotkit` — that route owns session-cookie → JWT injection (ARC-ADR-002). Exposing middle/back directly would bypass JWT injection and orphan rate-limiting, auth tiers, and billing — the slot for that is `api-gateway-engineer` (Azure APIM) when external API monetisation arrives, not a raw tunnel.

**Vendor choice:** Cloudflare Tunnel (default) is free, stable, real CA-signed cert (Google Trust Services). Ngrok-free was tried and failed — its `*.ngrok-free.dev` edge had broken IPv6 TLS handshakes for our network path; phone tests got `ERR_SSL_PROTOCOL_ERROR`. Cloudflare's edge works on both IPv4 and IPv6. The ngrok authtoken is still in Key Vault (`akv01-agentarmy` secret `ngrok`) if you want to upgrade to a paid ngrok tier for a reserved subdomain.

## Cloud-agent control plane — `tools/mcp-local-fleet/`

A small MCP server that lets cloud agents (Claude.ai routines, GitHub Actions, remote API callers) **observe and drive the local Docker fleet** without exposing the Docker socket. Bound to `127.0.0.1:8765`; public access is via `mcp.untool.ai` behind **CF Access service tokens** (`CF-Access-Client-Id` + `CF-Access-Client-Secret` headers). Eight tools, snake_case: `fleet_ps` / `fleet_inspect` / `fleet_logs` (read-only, auto-approve) and `fleet_up` / `fleet_down` / `fleet_restart` / `fleet_build` / `fleet_deploy` (write, per-call approval).

**Key invariants** (enforced in code, do not relax):
- Loopback bind only; public exposure requires explicit tunnel.
- Allowlisted service names only — no arbitrary container spawn; no shell-exec tool.
- CF Access JWT verified server-side (defense-in-depth); legacy bearer accepted on loopback only.
- Every call audited to `tools/logs/mcp-audit.log.YYYY-MM-DD` with redacted args + edge principal.
- Tool names MUST match `[a-zA-Z0-9_-]` — Claude Code's MCP client silently drops dotted names (`claude mcp list` shows 0 tools).

**Full reference** — server architecture, deployment target labels, full tool table, consumer-setup recipes, per-consumer service-token provisioning, and the Labs design note: [tools/mcp-local-fleet/README.md](tools/mcp-local-fleet/README.md) and [tools/mcp-local-fleet/AUTOMATION.md](tools/mcp-local-fleet/AUTOMATION.md).

Platform containers are also visible to `tail.mjs` (`node tools/tail.mjs spawn --service arcadedb` → `docker logs --follow` into the same NDJSON pipeline).

## SAFE Workflow Summary

- **PI** = Program Increment (~10 weeks / 5 sprints), tracked as a GitHub Milestone.
- **Sprint** = 2-week iteration via the `Iteration` field.
- **Definition of Ready**: Type, PI, Size, Estimate set + acceptance criteria in the body.
- **Definition of Done**: PR merged with a `Closes #N` link so `auto-status` moves the issue.

## Available Skills (Claude Code)

Run these with `/skill-name` in the Claude Code prompt:

| Skill | What it does |
|---|---|
| `/commit` | Stage and commit with a well-formed message |
| `/commit-push-pr` | Commit, push, and open a PR in one step |
| `/review-pr` | Multi-agent PR review |
| `/security-review` | Security audit of current branch changes |
| `/revise-claude-md` | Update this file with session learnings |
| `/simplify` | Review and clean up changed code |
| `/wardley [domain]` | Full Wardley analysis pipeline — value chain, map (OWM), doctrine, climate, gameplay |
| `/ea-adr [decision topic]` | Architecture Decision Record in MADR v4.0 format |
| `/capability-map [domain]` | Business capability model + investment heat map |
| `/loop [interval] [prompt]` | Run a prompt/command on a recurring interval (e.g. `/loop 5m`) — poll the board for new issues + PR activity (see [Poll for work with a recurring loop](#poll-for-work-with-a-recurring-loop)) |

### Model-invoked Skills (`.claude/skills/`)

[Agent Skills](https://agentskills.io/specification) — Claude auto-triggers them by file type/context (no slash command needed).

**First-party (ontology knowledge bundles)** — loaded by the `12-knowledge-ontology` agents:

| Skill | Triggers on |
|---|---|
| `ufo-ontology` | UFO/OntoUML/gUFO modeling — stereotypes, rigidity/sortality, relator reification, anti-patterns, UFO→BFO mapping (primary authoring discipline) |
| `bfo-ontology` | BFO 2020 grounding — continuant/occurrent, time-indexed relations, OBO/CCO/IAO/RO, Common-Logic-vs-OWL, BFO/CCO interop projection |

**Vendored** from [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) (MIT, © Steph Ango / @kepano):

| Skill | Triggers on |
|---|---|
| `obsidian-markdown` | `.md` files with wikilinks, embeds, callouts, properties, tags |
| `obsidian-bases` | `.base` files — views, filters, formulas, summaries |
| `json-canvas` | `.canvas` files — nodes, edges, groups, connections |
| `obsidian-cli` | Vault operations / plugin & theme dev via the Obsidian CLI |
| `defuddle` | Extracting clean markdown from a web URL (needs `npm install -g defuddle`) |

## GitHub Actions in This Repo

| Workflow | Do not manually override |
|---|---|
| `auto-add-to-project` | Runs on every new issue/PR — don't manually add items |
| `auto-status` | Runs on PR open/merge — don't manually change Status unless correcting |
| `copilot-review` | Adds Copilot as reviewer and flags large PRs — don't remove `needs-deep-review` label |
| `copilot-coding-agent` | Routes labelled issues — trust the routing, don't reassign manually |
| `claude` | Responds to `@claude` mentions on issues/PRs — edits, commits, pushes |
| `review-loop` | Autonomous review-fix loop (opt-in via `review-loop` label) — don't remove the label mid-loop |

## Container Tiering ([ARC-ADR-023](docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

Every container in the fleet belongs to exactly one tier. Pick the right one before adding a Dockerfile or `image.json`:

| Tier | Lifecycle | Has state? | Examples |
|---|---|---|---|
| **Platform** | Slow (days–months); careful upgrades | Yes | ArcadeDB, Postgres, NATS, Fuseki — composed via `templates/local-stack/` |
| **Application** | Rolling deploys (hours–days) | No | One container per spoke: backend-core, middle-core, frontend-core |
| **Function** | Fast, independently rolled out | No | event-bridge; planned LLM gateway (ADR-021), local embedder (#184) |

**Rule of thumb:** two pieces belong in the same container iff they always deploy together AND one failing must take the other down anyway. Otherwise split.

**Don'ts:** don't pre-split a spoke into 12 micros; don't bundle a platform database into a spoke's `image.json` ("fusion images" are retired — that's what `local-stack` is for); don't put state into Application or Function tiers.

**Composition patterns** (not new tiers): sidecar for cross-cutting concerns (HMAC verify, OTel collector); init container for pre-start work (migrations, schema seeds); Docker-in-Docker **only** for CI runners.

## Copilot Handoff Conventions

- When closing a `copilot-task` issue via PR, ensure the PR body contains `Closes #N` so `auto-status` fires correctly
- If Copilot's PR needs a deep review, add `needs-deep-review` label and run `/review-pr`
- If Copilot's implementation is wrong or too shallow, remove `copilot-task`, add `agent-army-task`, and handle with Claude Code

## Gotchas

- **This is a template repo.** When forked into a real project, owner/project references in `.github/workflows/*.yml` are hardcoded (e.g. `nickpclarke`, project number `1`) and must be edited by hand — see [docs/setup.md](docs/setup.md).
- **`PROJECT_TOKEN`** must be a **classic** PAT with the `project` scope checked — the default `GITHUB_TOKEN` cannot write to Projects v2 boards. Used by every workflow that updates the board.
- **`GITHUB_TOKEN`** (built-in) drives the PR/issue automation (`label-pr-size`, `copilot-review`, `copilot-coding-agent`, `stale`, `board-commands`). It is **read-only by default on forks** — those workflows declare `permissions:` blocks and set `GH_REPO`, but the catch-all is **Settings → Actions → General → Workflow permissions → Read and write**. Symptoms when missing: `Resource not accessible by integration` (perms) or `fatal: not a git repository` (no `GH_REPO`/checkout). See [docs/setup.md](docs/setup.md).
- `.claude/settings.local.json` contains personal permissions — gitignore in forks.
- **`@claude` and the review loop** need the Claude GitHub App + `CLAUDE_CODE_OAUTH_TOKEN` secret (see [docs/setup.md](docs/setup.md)); Claude pushes with `PROJECT_TOKEN` so its commits re-trigger the review bots.
- `auto-status` only fires when a PR body contains `Closes #N` / `Fixes #N` / `Resolves #N`. Without it, the linked issue stays in *In Progress*.
- **GCP Cloud Run container pipeline** templates live in `templates/gcp-cloud-run/` (Terraform IaC + `gcloud` bootstrap, reusable GitHub Actions workflow `.github/workflows/gcp-cloud-run-deploy.yml`, and `cloudbuild.yaml`). Auth is keyless via Workload Identity Federation — a spoke needs the repo secrets `WORKLOAD_IDENTITY_PROVIDER` and `DEPLOY_SERVICE_ACCOUNT` (printed by `terraform output` or `bootstrap-wif.sh`), and the caller workflow must set `id-token: write` + `secrets: inherit`. Runtime secrets come from Google Secret Manager. See [docs/gcp-cloud-run-pipeline.md](docs/gcp-cloud-run-pipeline.md).
- **Editing `.claude/agents/categories/` requires regenerating derived stores before commit.** Three artifacts are auto-generated from the source agent files: `.codex/agents/*.toml` (Codex platform), `.agents/plugins/**` (Gemini Antigravity), and `docs/agents-glossary/index.md`. CI enforces no-drift via the `Validate Codex Agent Synchronization` and `Fail if generated glossary is out of date` checks. After editing any agent file, run `PYTHONIOENCODING=utf-8 python -X utf8 scripts/orchestrate_agent_sync.py` (Codex + Antigravity) and `PYTHONIOENCODING=utf-8 python -X utf8 scripts/generate_agent_docs.py` (glossary), then stage `.codex/agents/`, `.agents/plugins/`, and `docs/agents-glossary/` alongside your source edits. The `PYTHONIOENCODING=utf-8 -X utf8` prefix is required on Windows — the scripts print emoji that crash under cp1252.
