# ARC-ADR-001 — Adopt GitHub Issues as HITL Decision Artifacts with Unified Assignee-Agnostic Wait-for-Close Model

| Field      | Value                                      |
|------------|--------------------------------------------|
| ID         | ARC-ADR-001                                |
| Status     | Accepted                                   |
| Date       | 2026-05-23                                 |
| Deciders   | Architecture Review                        |
| Supersedes | —                                          |
| Superseded by | —                                       |
| Tags       | hitl, governance, github-projects, agents  |

---

## Context and Problem Statement

AgentArmy runs multiple parallel agent sessions across Claude Code, GitHub Copilot, and third-party AI apps (Claude GitHub App, Gemini GitHub App). At any point, a running agent may reach a judgment call that exceeds its delegated authority: an architectural divergence between competing design directions, an ambiguous business rule, a decision to accept or reject a vendor, or a destructive action that requires explicit human sign-off.

No first-class mechanism currently exists to surface such a decision point while keeping all other concurrent work unblocked. The gaps are:

1. The `codebase-orchestrator` has a local approval-loop pattern (analyze → propose → wait → execute) but it operates within a single Claude Code session, is scoped to code diffs, and produces no artifact visible on the GitHub Projects board. When the session ends, the decision context is lost.
2. The `blocked-by` label convention exists in the repo but has no automation behind it — no workflow fires, no Status field is updated on the board, and no notification reaches the assignee.
3. There is no standard for *who* can be assigned to resolve a decision point. Humans, GitHub Copilot, the Claude GitHub App, and the Gemini GitHub App each interact with GitHub differently. Without a unified model, each decision type would require bespoke handling per actor class.

The decision infrastructure must satisfy these four constraints simultaneously:
- Agents can pause on a specific decision without halting an entire PI's worth of parallel work.
- Decision artifacts are visible at the GitHub Projects board level, where humans already manage priority and status.
- Artifacts are persistent, auditable, searchable, and linkable to parent issues.
- The model is extensible to any GitHub actor as decision resolver — without adding new infrastructure per actor type.

---

## Decision Drivers

| # | Driver |
|---|--------|
| D1 | Agents must be able to pause on a single decision point without blocking all parallel work in the PI. |
| D2 | Humans engage with the project board (GitHub Projects v2), not via Slack pings or email. Decision artifacts must live there. |
| D3 | Decision artifacts must be persistent, auditable, searchable, and linkable to parent features and stories. |
| D4 | The model must be extensible to any GitHub actor as decision assignee: a named human, a team, GitHub Copilot, the Claude GitHub App, or the Gemini GitHub App — without per-actor special handling. |
| D5 | Zero new infrastructure tools — reuse what already exists in the repository. |
| D6 | The blocked story must recover automatically when the decision is resolved; manual board cleanup is unacceptable at scale. |

---

## Considered Options

1. **GitHub Issues as decision artifacts** (chosen) — introduce a `Decision` Type, a `hitl-decision` label, a `hitl-coordinator` agent, and a `hitl-decision.yml` GitHub Actions workflow; all assignee types use the same wait-for-close model.
2. **Slack or Teams messages** — post decision context to a channel and wait for an emoji reaction or threaded reply to indicate resolution.
3. **Custom webhook + external approval UI** — build a dedicated approval service outside GitHub that agents call via HTTP; humans approve through a custom web interface.
4. **Comment-only blocking on parent issues** — the agent posts a structured comment on the parent issue flagging the block; no separate decision artifact is created.
5. **Extend `codebase-orchestrator`** — expand its existing approval-loop pattern to cover non-code decisions by keeping the agent session alive longer.

---

## Decision Outcome

**Option 1 — GitHub Issues as decision artifacts** is adopted.

When an agent encounters a decision point that exceeds its authority, it creates a GitHub Issue of Type `Decision` with label `hitl-decision`. The issue body contains a `## Blocks` section listing the parent issue numbers whose progress depends on the decision. The `hitl-decision.yml` workflow fires on issue creation, sets the board Status to `Awaiting Decision`, and adds the `awaiting-human` label plus a blocking comment to each story listed in `## Blocks`. Any GitHub actor — human or AI app — is assigned to the decision issue using the standard GitHub assignee field. The resolution protocol for every actor is identical: close the issue (with a comment explaining the decision made). The `hitl-decision.yml` workflow then removes `awaiting-human` from all blocked stories and sets their Status back to `Todo`, unblocking the parallelwork.

### Confirmation criteria

The decision is considered validated when all of the following are demonstrable:

- A Decision issue created by `hitl-coordinator` receives the `hitl-decision` label and board Status `Awaiting Decision` without manual intervention.
- Each story listed in `## Blocks` receives the `awaiting-human` label and a structured blocking comment linking to the decision issue.
- Closing the decision issue (by any actor) triggers automatic removal of `awaiting-human` and Status reset to `Todo` on all blocked stories.
- The `/decisions` board command lists all open decision artifacts, grouped by assignee type (human / copilot / claude-app / gemini-app).
- All actor types (human, Copilot, Claude GitHub App, Gemini GitHub App) follow the identical close-to-unblock flow with no actor-specific code paths in the workflow.

---

## Pros and Cons of the Options

### Option 1 — GitHub Issues as decision artifacts (chosen)

GitHub Issues are already the shared coordination plane for both the Claude Code army and the Copilot army. Adding a `Decision` Type and `hitl-decision` label costs nothing in terms of tooling. The GitHub Projects board already supports custom Status options, and the `auto-status.yml` workflow pattern demonstrates that Status transitions triggered by issue/PR events are fully automatable with the existing `PROJECT_TOKEN`.

**Pros:**
- Zero new tools — GitHub Issues, Labels, Projects, and Actions are already in place.
- Decision artifacts are board-visible, label-filterable, Status-lifecycle-tracked, and GitHub-notification-aware.
- Any GitHub actor can be assigned using the native assignee field — no per-actor special handling required.
- Sub-issue linkage via `## Blocks` places decision artifacts in the correct Epic/Feature/Story hierarchy.
- Persistent and auditable: decision rationale in the closing comment survives team turnover and is searchable by future agents and humans.
- Consistent with ARMY_PRINCIPLES.md Principle 7 (Observable Decision-Making): decision artifacts are structured, queryable records.

**Cons:**
- Adds a new `Decision` Type and `Awaiting Decision` Status option to the project board, which constitutes minor governance overhead (field value registration, documentation update).
- The `hitl-decision.yml` workflow must reliably parse the `## Blocks` section of the issue body. This section format becomes a structural contract — any agent that creates a decision issue must conform to it, and any future change to the format is a breaking change requiring a coordinated update.

---

### Option 2 — Slack or Teams messages

Decision context posted to a channel, resolution via emoji reaction or threaded reply.

**Pros:**
- Low implementation effort: agents can post via webhook with no new GitHub configuration.
- Humans who already monitor Slack/Teams receive a familiar notification.

**Cons:**
- Violates D2: humans engage at the board level, not in chat. A Slack message is a second coordination plane requiring humans to context-switch.
- Violates D3: Slack messages are not persistent, not version-controlled, not linkable to parent issues, and not searchable by future agents or humans.
- Violates D4: AI app actors (Copilot, Claude GitHub App, Gemini GitHub App) have no standardized way to read Slack threads or respond to emoji reactions.
- No automatic unblocking: the workflow would need to poll Slack for a resolution signal, which requires additional infrastructure.
- Slack message history expires on free tiers; decision rationale is lost.

---

### Option 3 — Custom webhook + external approval UI

A separate approval service receives agent-posted decisions via HTTP; humans approve through a dedicated web interface.

**Pros:**
- Maximum flexibility: the approval UI can be designed for rich decision context (diagrams, diffs, options side-by-side).
- Fully decoupled from GitHub, enabling use across multiple repository hosts.

**Cons:**
- Violates D5 directly: this is new infrastructure requiring development, hosting, authentication, and maintenance.
- Violates D2: introduces a third coordination plane (board + GitHub + approval UI) that humans must monitor.
- High implementation cost relative to the problem: the existing GitHub Issues system already provides all required capabilities.
- Security surface increases: the external service must be authenticated, authorized, and kept available — adding operational risk with no commensurate benefit for this use case.
- AI app actors have no standardized integration path to an external approval UI.

---

### Option 4 — Comment-only blocking on parent issues

The agent posts a structured comment on the parent story or feature issue flagging the block; no separate decision artifact is created.

**Pros:**
- Minimal ceremony: no new issue type, no new label, no new workflow.
- Decision context is co-located with the blocked work item.

**Cons:**
- Violates D2: a comment buried in a story issue is not visible at the board level. A human scanning the board cannot distinguish a story that is blocked on a decision from one that is actively in progress.
- Violates D3: comments are not independently searchable, cannot be filtered, and are not assignable to a resolver.
- Violates D6: there is no automation hook on a comment that can trigger a Status transition. A human must manually update the board after resolving the decision.
- Violates D4: AI app actors cannot be assigned to a comment; they would need to monitor the comment thread, which is not a supported interaction model for GitHub Apps.
- Comment threads become noisy as multiple agents post blocks on the same story; there is no lifecycle (open/close) to indicate whether a block has been resolved.

---

### Option 5 — Extend `codebase-orchestrator`

Expand the `codebase-orchestrator` approval-loop pattern to cover non-code decisions by keeping the agent session alive and waiting for a human reply within the same Claude Code session.

**Pros:**
- No new GitHub artifacts: the decision lives within the active session.
- The `codebase-orchestrator` approval-loop is already implemented and understood.

**Cons:**
- Violates D2: the decision point is invisible on the GitHub Projects board. A human must be actively watching the Claude Code terminal to see the approval prompt.
- Violates D3: when the Claude Code session ends (timeout, connection drop, user closes terminal), the decision context is lost. There is no persistent record.
- Violates D4: the approval-loop is scoped to the human running the session. Copilot, Claude GitHub App, and Gemini GitHub App cannot participate in a Claude Code session approval-loop.
- Violates D1: the current `codebase-orchestrator` blocks the entire session while waiting for approval, meaning no other work in that session can proceed. This is acceptable for code diffs within a single refactor but unacceptable for blocking an agent that has other parallel work to continue.
- Not extensible: each new decision category (vendor selection, architectural direction, data retention policy) would require bespoke extensions to `codebase-orchestrator`, coupling governance concerns into a code-focused agent.

---

## Positive Consequences

- Decision points are surfaced at the board level without any new tooling — the existing `PROJECT_TOKEN`, GitHub Actions infrastructure, and Projects v2 board are fully reused.
- Any GitHub actor can be assigned as a decision resolver. The workflow is actor-agnostic: it triggers on issue close, regardless of who or what closed it. ARC-ADR-002 (deferred) may introduce API-based auto-response for AI app actors, but the wait-for-close model remains the baseline for all actors.
- Blocked stories are automatically unblocked on decision close, eliminating the manual board cleanup that would otherwise accumulate as technical governance debt.
- Decision artifacts are persistent, version-controlled, and linkable, satisfying ARMY_PRINCIPLES.md Principle 7 (Observable Decision-Making) and extending it from agent routing decisions to cross-cutting governance decisions.
- The `## Blocks` section format is a lightweight structural contract that is easy to validate in CI (a grep for the section header is sufficient to detect malformed decision issues before they reach the board).

---

## Negative Consequences

- The `Decision` Type and `Awaiting Decision` Status option must be registered in the GitHub Projects v2 board configuration before the first decision issue can be created. This is a one-time governance action but it must be documented in `docs/setup.md` so that Spoke repos that fork AgentArmy know to replicate the board schema.
- The `## Blocks` section in the decision issue body is a structural contract. If the format changes (e.g., from issue numbers to issue URLs, or from a flat list to a nested hierarchy), the `hitl-decision.yml` workflow parser must be updated simultaneously. A migration strategy must be defined before any format change is made.
- Each new decision issue adds an artifact to the board. If agents over-generate decision issues (e.g., raising a decision for trivial judgment calls within their authority), the board becomes noisy. The `hitl-coordinator` agent definition must include clear authority thresholds to prevent over-escalation.

---

## Implementation Notes

### New components introduced by this decision

| Component | Type | Purpose |
|-----------|------|---------|
| `Decision` | GitHub Projects v2 Type field value | Labels an issue as a decision artifact on the board |
| `hitl-decision` | GitHub label | Marks an issue as a HITL decision point; used for board filtering and workflow trigger |
| `awaiting-human` | GitHub label | Applied to blocked stories; signals that no agent should pick up the work |
| `Awaiting Decision` | GitHub Projects v2 Status field value | Board-level status for decision artifacts |
| `hitl-coordinator` | Claude Code agent | Creates decision issues, populates `## Blocks`, assigns resolvers |
| `hitl-decision.yml` | GitHub Actions workflow | Fires on decision issue creation and on close; manages label and Status transitions |
| `/decisions` | Board command (board-commands.yml extension) | Lists open decision artifacts grouped by assignee type |

### Decision issue body contract

Decision issues created by `hitl-coordinator` must conform to the following structure. Deviation from this structure will cause the `hitl-decision.yml` parser to fail silently (blocked stories will not receive `awaiting-human`).

```markdown
## Decision Required

[One paragraph describing the decision point, the options available, and the recommendation (if any) from the requesting agent.]

## Context

[Links to relevant issues, ADRs, design documents, or agent outputs that provide background for the decision.]

## Options

- **Option A:** [Description]
- **Option B:** [Description]

## Recommendation

[The requesting agent's preferred option, with rationale. Leave blank if the agent has no preference.]

## Blocks

- #[issue-number] — [brief description of what is blocked]
- #[issue-number] — [brief description of what is blocked]

## Requested Assignee

[GitHub username, team slug, or AI app name (copilot, claude-app, gemini-app)]
```

### Workflow trigger and transition logic

```
on: issues [opened, closed]

opened:
  if label == 'hitl-decision':
    set board Status = 'Awaiting Decision'
    for each issue in ## Blocks:
      add label 'awaiting-human'
      post blocking comment with link to decision issue

closed:
  if label == 'hitl-decision':
    remove label 'awaiting-human' from all issues previously listed in ## Blocks
    set board Status of blocked issues = 'Todo'
    post unblocking comment on each previously-blocked issue
```

---

## Related Decisions

- **Supersedes:** None. This is ARC-ADR-001, the first Architecture Decision Record in the AgentArmy decision log.
- **Relates to:** `codebase-orchestrator` approval-loop pattern (`.claude/agents/categories/09-meta-orchestration/codebase-orchestrator.md`) — the approval-loop pattern inspired the wait-for-close model but is intentionally kept separate. `codebase-orchestrator` continues to own code-diff approval within a live session; `hitl-coordinator` owns board-level decision artifacts.
- **Relates to:** ARMY_PRINCIPLES.md Principle 1 (Error Escalation to Coordinator) — decision points that arise from an irresolvable error should escalate to `error-coordinator` first; only if `error-coordinator` cannot resolve the issue should `hitl-coordinator` raise a decision artifact.
- **Relates to:** ARMY_PRINCIPLES.md Principle 7 (Observable Decision-Making) — decision artifacts are the governance-layer expression of this principle, extending observable decision-making from agent routing logs to cross-cutting architectural and business governance decisions.
- **Relates to:** Agent routing conventions in `CLAUDE.md` — the `hitl-coordinator` agent is added to the meta-orchestration routing table.
- **Follow-up — ARC-ADR-002 (deferred):** AI app actors (Claude GitHub App, Gemini GitHub App) may eventually auto-respond to decision issues via the GitHub API, bypassing the need for a human to manually close the issue. The wait-for-close model chosen here is deliberately actor-agnostic and remains valid whether the close action is performed by a human or an API call. ARC-ADR-002 will document the auto-response protocol if and when it is implemented.

---

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-05-23 | Architecture Review | Initial acceptance |
