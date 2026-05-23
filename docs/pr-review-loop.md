# Autonomous PR Review Loop

AgentArmy's pull requests are reviewed automatically by three remote bots — **Gemini Code Assist**, the **GitHub Copilot reviewer**, and **Codex**. The autonomous review loop lets Claude close the loop on that feedback: it reads the bots' comments, fixes the code, pushes, the bots re-review, and it repeats until the PR is clean — escalating to a human only when it stalls.

It is **opt-in per PR** (you add a label) and **bounded** (a round cap), so it never runs away.

---

## How to start it

Add the **`review-loop`** label to an open PR:

```bash
gh pr edit <PR> --add-label review-loop
```

That's it. From then on, every time a review bot posts feedback, the loop runs.

To stop it at any time, remove the label:

```bash
gh pr edit <PR> --remove-label review-loop
```

---

## The flow

```
You add the `review-loop` label
  ↓
A review bot (Gemini / Copilot / Codex) submits review comments
  ↓
review-loop.yml (the "brain") runs:
  • already asked Claude for this commit? → wait
  • bots re-reviewed with nothing actionable? → ✅ converged (label review-loop:done)
  • round cap reached? → 🙋 escalate to a HITL Decision artifact (label review-loop:escalated)
  • otherwise → post ONE aggregated @claude comment listing the feedback
  ↓
claude.yml (the "hands") runs:
  • Claude addresses each item, commits, and pushes (with the PAT)
  ↓
the push re-triggers Gemini / Copilot → they re-review
  ↓
back to the top
```

Two workflows split the work so each stays simple:

| Workflow | Role |
|---|---|
| **`review-loop.yml`** | The **brain** — decides whether to iterate, counts rounds, checks convergence, escalates. Never edits code. |
| **`claude.yml`** | The **hands** — the `@claude` responder. Reads the aggregated feedback, edits, commits, pushes, replies to threads. Also handles manual `@claude` mentions. |

---

## Rounds, convergence, and escalation

**Round tracking.** Each time the loop asks Claude to fix something, it posts a hidden marker (`<!-- review-loop round=N -->`) in its comment. The round number is just how many of those markers exist.

**Convergence (the happy path).** There is no single "approved by all bots" signal from GitHub, so the loop keys off what's still *unaddressed*. An inline bot comment counts as actionable until its line changes — once Claude's fix moves that code, GitHub marks the comment **outdated**, and the loop treats it as resolved. The loop converges when **no configured bot has any unaddressed (non-outdated) inline comment, and no bot's latest review is `CHANGES_REQUESTED`** — and at least one bot has re-reviewed the latest commit. It then posts a ✅ summary and swaps `review-loop` → `review-loop:done`.

> An unaddressed comment from **any** configured bot keeps the loop running — convergence is **not** declared just because one bot is happy while another still has open comments. It does not hard-block on *every* bot re-running each push (a bot may skip a round); the round cap is the backstop. And `review-loop:done` means "no outstanding bot feedback," **not** "merge it" — the final merge stays a human (or auto-merge) decision. Top-level review summaries are treated as descriptive, not actionable.

**Escalation (the safety net).** If the loop reaches the round cap (default **3**) while the bots still have actionable comments, it does **not** keep going. It opens a **Decision artifact** — a Human-in-the-Loop issue (`hitl-decision` label, Status `Awaiting Decision`) whose `## Blocks` section lists the PR — and swaps `review-loop` → `review-loop:escalated`. From there the normal [HITL flow](hitl.md) takes over: a human comments their choice and closes the issue, which unblocks the PR.

Escalation also fires implicitly when Claude can't satisfy the bots: if a round produces no fix, the bots keep their comments, and the cap is eventually hit.

---

## Labels

| Label | Color | Meaning |
|---|---|---|
| `review-loop` | blue | Opt-in: run the loop on this PR |
| `review-loop:done` | green | Converged — no actionable bot comments remain |
| `review-loop:escalated` | red | Hit the round cap — a Decision artifact was opened |

The workflow creates these labels automatically on first run.

---

## Configuration

| Setting | Where | Default |
|---|---|---|
| Round cap | repo **variable** `REVIEW_LOOP_MAX_ROUNDS` | `3` |
| Reviewed bot accounts | `BOT_LOGINS` env in `review-loop.yml` | gemini-code-assist[bot], copilot-pull-request-reviewer[bot], chatgpt-codex-connector[bot] |

To change the cap:

```bash
gh variable set REVIEW_LOOP_MAX_ROUNDS --body "5"
```

---

## Cost and safety guards

- **Opt-in only** — nothing happens until you add the `review-loop` label.
- **Round cap** — bounded iterations, then escalation. Never an infinite loop.
- **Debounced** — the loop posts at most **one** `@claude` request per commit; extra bot reviews of the same commit don't trigger duplicate fixes.
- **Bot-scoped** — only the three review-bot accounts count as feedback. Claude's own commits and comments can't re-arm the loop.
- **Event-driven** — the loop reacts to review events; it never polls or sleeps.

---

## Prerequisites (one-time)

The loop needs the Claude responder wired up. See the [Setup Guide](setup.md) for full steps:

1. **Install the Claude GitHub App** on the repo (provides the `@claude` trigger).
2. **Add the `CLAUDE_CODE_OAUTH_TOKEN` secret** — generate it locally with `claude setup-token`, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN`.
3. **`PROJECT_TOKEN`** (the classic PAT — personal access token — already used by the board workflows) must exist. Claude pushes with it so that its fix-commits re-trigger the review bots; a push made with the default `GITHUB_TOKEN` would **not** re-trigger them, and the loop would never close.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Nothing happens after adding the label | Bots haven't reviewed yet | The loop runs on the **next** bot review — wait, or re-request a bot review |
| `@claude` comment posts but nothing fixes | `claude.yml` not installed or `CLAUDE_CODE_OAUTH_TOKEN` missing | Check the Claude App + secret (see Prerequisites) |
| Claude fixes but bots never re-review | Claude pushed with `GITHUB_TOKEN`, not the PAT | Confirm `claude.yml` passes `github_token: ${{ secrets.PROJECT_TOKEN }}` |
| Loop escalates immediately | Round cap too low, or feedback is genuinely subjective | Raise `REVIEW_LOOP_MAX_ROUNDS`, or resolve via the Decision artifact |
| Loop seems stuck on round N | A bot re-reviews slowly | It's event-driven; the next review advances it |

---

## Related

- [Human-in-the-Loop](hitl.md) — the escalation target when the loop stalls
- [GitHub Copilot Army](copilot.md) — how the review bots fit the two-army model
- [GitHub Projects v2](github-projects.md) — board fields and the `Awaiting Decision` status
- [Setup Guide](setup.md) — installing the Claude App and tokens
