# Human-in-the-Loop (HITL) Decision Pattern

AgentArmy runs parallel agent sessions across Claude Code, GitHub Copilot, and AI apps. When any agent hits a creative fork, an architectural divergence, or a judgment call that exceeds its authority, it surfaces the decision to the right person (or AI app) as a **Decision Artifact** on the GitHub Projects board — without blocking everything else.

This page explains how to navigate, engage with, and resolve Decision Artifacts.

---

## What is a Decision Artifact?

A **Decision Artifact** is a GitHub Issue with:

- **Type:** `Decision`
- **Label:** `hitl-decision` (vivid orange — easy to spot on the board)
- **Status:** `Awaiting Decision`
- **Assignee:** the human, team, or AI app responsible for the call

The issue body follows a structured template that gives you everything you need to decide:

| Section | What it contains |
|---|---|
| **Decision Summary** | 1–2 sentence plain-English statement of what needs to be decided |
| **Context** | What the agent knows — facts, constraints, prior attempts, relevant code paths |
| **Options** | 2–4 alternatives with explicit pros and cons |
| **Agent Recommendation** | The agent's preferred option (or "no preference") with reasoning |
| **Impact of Each Option** | What changes downstream based on the choice |
| **Blocks** | Links to the issues that cannot proceed until this decision is made |
| **Decision Needed By** | Target date or sprint milestone |
| **How to Decide** | Instructions for closing the issue |

---

## Finding Decisions That Need You

### On the board

Filter the GitHub Projects board by:
- **Status = `Awaiting Decision`** — shows all open decision artifacts
- **Label = `hitl-decision`** — same, across all statuses
- **Assignee = you** — decisions specifically routed to you

### Via slash command

In any issue comment, type:

```
/decisions
```

The bot replies with a table of all open decision artifacts, grouped by assignee type, showing how long each has been open and what it blocks.

### Via GitHub notifications

GitHub notifies you automatically when a Decision Artifact is assigned to you. To ensure you see them promptly:

1. Go to **GitHub → Settings → Notifications**
2. Under "Participating and @mentions," enable **Email** or **Web** notifications
3. Alternatively, subscribe to the `hitl-decision` label: on any issue with that label, click **Subscribe**

---

## How to Make a Decision

1. **Read the issue.** The Context and Options sections are written to be self-contained — you should not need to dig through code to decide.

2. **Comment with your choice.** Use any format — a single word, a sentence, or a paragraph with conditions:
   ```
   Go with Option B. The extra complexity is worth it given we're expecting >10k users by PI-3.
   Condition: revisit at PI-3 retrospective if adoption is lower than forecast.
   ```

3. **Close the issue.** This triggers the automation:
   - `hitl-decision` label is swapped for `decision-made`
   - Your comment is posted as context on every blocked issue
   - Blocked issues transition from `Awaiting Decision` → `Todo`
   - `awaiting-human` label is removed from each blocked issue
   - Work can resume — apply `copilot-task` or `agent-army-task` to restart routing if needed

That's it. You don't need to manually update any other issue or field.

---

## Assignee Types

Decision Artifacts can be assigned to any GitHub actor. The `assignee:TYPE` label tells you who's responsible at a glance:

| Label | Color | Who decides |
|---|---|---|
| `assignee:human` | Soft purple | A specific human — you or a named stakeholder |
| `assignee:copilot` | Copilot blue | GitHub Copilot (for board/code queries) |
| `assignee:claude-app` | Claude amber | Claude GitHub App (for bounded analysis) |
| `assignee:gemini-app` | Gemini blue | Gemini GitHub App (for bounded analysis) |

All assignee types use the **same workflow** — comment + close. There is no special API wiring. If an AI app is assigned, it will engage in its own time via the GitHub interface, exactly like a human reviewer would.

---

## Blocked Issues

While a Decision Artifact is open, every issue listed in its `## Blocks` section:

- Gets the `awaiting-human` label (amber — visible on the board)
- Gets a blocking comment linking to the Decision Artifact
- May have its Status set to `Awaiting Decision` on the board

Once you close the Decision Artifact, the automation clears all of this automatically.

---

## Decision Types

The `hitl-coordinator` agent classifies decisions into these types. Understanding the type helps you engage at the right level:

| Type | What it means for you |
|---|---|
| **Architecture Divergence** | A proposed design deviates from the established system — you're signing off on a structural change |
| **Creative Direction** | A visual, narrative, or UX choice with no objectively correct answer — your aesthetic/product judgment is the input |
| **Risk Acceptance** | Proceeding requires accepting a risk the agent can't own — you're explicitly acknowledging the trade-off |
| **Scope Change** | Implementation would grow beyond the original issue — you're deciding whether to expand or stay scoped |
| **Priority Conflict** | Two high-priority items compete — you're setting the tie-break |
| **Security Gate** | A change needs explicit authorization — you're the authorizing stakeholder |
| **Budget/Capacity** | There are cost or staffing implications — you're approving or redirecting |
| **Bounded Research** | A well-scoped question an AI app can answer — typically assigned to claude-app or gemini-app |

---

## For Agents: When to Escalate

An agent should invoke `hitl-coordinator` when it encounters a situation where:

- Multiple valid design paths exist and the choice reflects values or strategy (not just engineering)
- The proposed implementation would deviate from the established system architecture
- A risk exists that the agent is not authorized to accept on behalf of the project
- The scope of an issue would expand beyond what was originally described
- Two high-priority items are in conflict and cannot both proceed

An agent should **not** escalate for:

- Choices between two technically equivalent implementations (make the reasonable call)
- Minor style or naming decisions within an established codebase convention
- Errors that can be automatically recovered by `error-coordinator`

See the `hitl-coordinator` agent for the full decision type taxonomy and issue creation template.

---

## Architecture Reference

The design rationale for this pattern — including alternatives considered and consequences — is documented in [ARC-ADR-001: HITL Decision-Point Pattern](decisions/ARC-ADR-001-hitl-decision-point-pattern.md).
