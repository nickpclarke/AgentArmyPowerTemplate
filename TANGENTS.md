# TANGENTS.md — the thread ledger

A friction-free ledger of the operator's open threads: interests, side-quests, ideas,
and tangents that surface mid-session. Mandated by [Article IV of the
CONSTITUTION](CONSTITUTION.md#article-iv--the-tangent-ledger-capture-the-threads).

**This is not the board.** The GitHub Projects board / issues are for *committed,
scoped work*. This ledger is for *live curiosity* — things worth not forgetting, before
they're ready to be real work. A thread **graduates** to a board issue when it becomes
concrete; until then it lives here, with no ceremony.

**How agents use it:** when a new thread surfaces, append a row. Don't ask permission to
log — just log it. Each session you may surface quiet *Active* threads via the selector,
never as a nag.

---

## 🔥 Active — threads in motion

| Opened | Thread | Next nibble | Notes |
|---|---|---|---|
| 2026-05-30 | **The Choice Principle + Tangent Ledger** (this constitutional moment) | Land PR; balanced strictness set | Constitution + ledger landed this session |
| 2026-05-30 | **F# ontology compiler core** — category theory framing | Functors=projections, catamorphisms=generators, gUFO⟷BFO=nat. transformation | ADR-032/033; keep CT top-of-mind |
| 2026-05-30 | **Local model serving on the dev box** | Local embedder for ArcadeDB RAG (best fit); iGPU via OpenVINO | Hub issue #184; Core Ultra 7, NPU/iGPU, no dGPU |
| 2026-05-30 | **BYO-credentials → thin bootstrap container** | Evolve broker into bootstrap; watch Infisical agent-vault | ARC-ADR-037 built; design note in Labs |
| 2026-05-30 | **Serve every capability via MCP** (cloud + local) | Declarative registry + reconcile loop (not hand-cranked plumbing) | Fast queue-able add-and-use cadence |

## 🌱 Parked — someday / not now

| Opened | Thread | Why parked |
|---|---|---|
| 2026-05-30 | **Operator-tunnel durability** (single session-bound connector) | Known gap #324; works today, revisit when it bites |
| 2026-05-30 | **Paid ngrok reserved subdomain** | cloudflared wins for now; KV `ngrok` token kept if we retry |

## ✅ Landed — graduated or done

| Opened | Closed | Thread | Outcome |
|---|---|---|---|
| 2026-05-30 | 2026-05-30 | Establish the fleet constitution | `CONSTITUTION.md` + `TANGENTS.md` created, anchored in CLAUDE.md/AGENTS.md |

---

_Conventions: keep rows one-line. Dates are `YYYY-MM-DD`. Move threads between sections
freely — graduation to a board issue means a row moves to **Landed** with the issue link
as its outcome._
