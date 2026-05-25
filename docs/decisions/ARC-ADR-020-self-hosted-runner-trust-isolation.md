# ARC-ADR-020 — Self-Hosted CI Runner Trust & Isolation Policy

| Field | Value |
|---|---|
| ID | ARC-ADR-020 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — hub owner decides) |
| Supersedes | — |
| Superseded by | — |
| Tags | ci, security, self-hosted-runners, actions, isolation, supply-chain, aca, docker-local |

---

## Context and Problem Statement

To escape the GitHub-hosted Actions minutes cap, the fleet migrated **all PR-gating CI** across the hub + 3 spokes onto **self-hosted runners** (ACA/KEDA `aca-linux` + local `docker-local`), triggered on `pull_request`. Those jobs **execute repository code** (`npm ci`, `cargo build`, `pip install`, `npm run build-storybook`, etc.).

A Codex review (on frontend-core storybook.yml, 2026-05-25) flagged the general risk, correctly: **self-hosted runner + untrusted `pull_request` code = arbitrary code execution on the runner**, which can read whatever credentials and network the runner can reach. This is a well-known GitHub anti-pattern, and here it is **fleet-wide** (every self-hosted `pull_request` job, not one workflow).

**Verified current exposure (2026-05-25):** all four repos are **PRIVATE**, have **zero outside collaborators**, **0 forks**, and fork-PR workflow access is `none`. So untrusted parties **cannot open PRs** → cannot run code on the runners. **The risk is not exploitable today.**

But the safety lives entirely in **repo settings, not the workflow YAML** — so it can regress silently. The moment any repo goes **public**, or gains an **untrusted collaborator**, every self-hosted PR job becomes a remote-code-execution vector. The blast radius is real: the ACA runners currently hold **ACR-admin credentials + Key Vault access**.

The decision: **what is the trust/isolation policy that keeps self-hosted CI safe and keeps it from silently regressing?**

## Decision Drivers

| # | Driver |
|---|---|
| D1 | Keep CI **free** (self-hosted, off the metered minutes cap) — the reason for the migration. |
| D2 | **No untrusted code on self-hosted runners**, ever — untrusted PR code must not execute where it can reach fleet credentials/network. |
| D3 | The safety must be **enforceable / hard to regress**, not a tribal-knowledge "keep it private" hope. |
| D4 | **Least privilege** the runner identity — a compromised job should reach as little as possible (ACR-admin + KV is too much standing power). |
| D5 | Don't break the current fast, free PR feedback for **trusted** contributors. |

## Considered Options

1. **Private-only invariant + fork-origin guard + fork-PR approval** *(recommended)*. Keep all repos private with trusted-only write (the current posture, made explicit as an invariant). Add defense-in-depth so a settings regression can't silently arm the vector: (a) a **fork-origin guard** on every self-hosted job — `if: github.event.pull_request.head.repo.full_name == github.repository` (a no-op today; permanently prevents fork-origin PRs from running on self-hosted), (b) GitHub **"require approval for fork PRs"**, and (c) **least-privilege** the runner identity (drop standing ACR-admin/KV where possible; scope per-repo).
2. **Split routing — trusted → self-hosted, fork/untrusted → GitHub-hosted.** Gate by PR origin: same-repo branches run self-hosted (free); fork PRs run on `ubuntu-latest`. Safe for public-repo futures, but fork CI then **consumes the minutes cap** (the thing we're avoiding), and adds per-workflow conditional complexity.
3. **Status quo — rely on the private posture alone.** Works today; no guardrails. A single visibility flip = instant fleet-wide RCE with no tripwire. Cheapest now, highest latent risk (fails D3).

## Decision Outcome

**To be decided** by the hub owner (Proposed stub — options + recommendation, not a unilateral call).

### Recommendation note (not a decision)

**The owner has confirmed the threat model excludes forks and untrusted collaborators** (2026-05-25: *"we're not building forks"*) — all work is branches within private repos by the owner + trusted agent apps. That puts the fork-RCE vector **out of scope**, so Option 1's fork-origin guard + fork-PR approval machinery is **not adopted**: it would guard a path that does not exist in this model, at a maintenance cost for zero real coverage.

**Adopted posture (lightweight):**
1. **Document the invariant** — self-hosted CI is safe *because* these repos stay **private, trusted-only write, no forks**. That is the security boundary; record it so it isn't silently lost.
2. **Tripwire on the invariant, not the PR** — if any repo is ever made **public** (or gains an untrusted collaborator), self-hosted CI must be revisited *before* that change lands, at which point Option 1 (fork-origin `if:` guard) or Option 2 (route fork PRs to GitHub-hosted) applies. Until then, **no per-job guards**.
3. **Optional defense-in-depth** — least-privilege the runner identity (drop standing ACR-admin/KV where a build doesn't need it). This caps blast radius from a *supply-chain* compromise (a malicious dependency in even a trusted PR) — the one residual risk that survives a no-forks model. Adopt if cheap; not urgent.

Options 2 and 3 stay documented for a possible public-repo future, but under the current no-forks model the fork machinery isn't warranted.

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| all | hub + frontend-core + backend-core + middle-core | fork-origin `if:` guard on every self-hosted `pull_request` job; fork-PR approval setting |
| (infra) | hub templates (`aca-github-runner`, `local-docker-runner`) | least-privilege the runner identity; document the trust invariant in the template README |

## Pros and Cons of the Options

### Option 1 — Private invariant + fork-origin guard + approval (recommended)
**Pros:** keeps CI free (D1); makes safety enforceable not implicit (D3); the `if:` guard is a zero-cost permanent tripwire; least-privilege shrinks blast radius (D4). **Cons:** a guard line to maintain on each self-hosted job; fork PRs (if ever enabled) get no CI until explicitly routed.

### Option 2 — Split routing (fork → GitHub-hosted)
**Pros:** safe even for public repos; trusted PRs stay free. **Cons:** fork CI consumes the minutes cap (re-introduces the cost problem); more conditional complexity per workflow.

### Option 3 — Status quo (private-only, no guardrails)
**Pros:** nothing to do now. **Cons:** safety is invisible and one settings flip from fleet-wide RCE; fails D3.

## Related Decisions

- **ARC-ADR-011** — runtime secret resolution: the runner identity's creds (least-privilege per D4) resolve via that scheme.
- **ARC-ADR-015** (backlog) — deployment & promotion: where/how the runners are deployed and their identity scoped.
- **ARC-ADR-017** (backlog) — connector egress/SSRF: sibling "untrusted input reaching privileged execution" concern, on the data-plane rather than CI.
- Origin: Codex PR review on frontend-core storybook.yml (2026-05-25); the self-hosted runner migration (hub #180/#183 + spoke equivalents).

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | security review (Codex finding) | Initial Proposed draft — options + recommendation; HITL decision pending |
