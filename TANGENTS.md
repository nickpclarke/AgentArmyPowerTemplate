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
| 2026-05-31 | **Consensus as a first-party graph-enhanced partner** — direct MCP exposure (PR #424) is right for *cloud* too: cloud agents can't reach the governed `/a2a/v1` (localhost-only behind the tunnel), so first-party direct is the more reliable path, not a compromise. Bigger idea: enrich Consensus's peer-reviewed evidence with our Object Model graph (provenance/entities/relationships) — a compounding loop | When PR #424 lands + token in KV: prototype graph-enrichment of a Consensus result; later, the governed MCP→REST shim for billing safety | Both-layers: direct (reachability) + governed (overage brake) are complementary. Governed shim not yet ticketed |
| 2026-05-31 | **Cross-harness governance distribution** — `docs/untool-platform.md` (foundry-vs-product brief) + CONSTITUTION.md aren't anchored into every agent's entrypoint: copilot-instructions.md has 0 refs, no GEMINI.md, no .cursor/rules. Operator drives Codex/Claude/Antigravity/Copilot/Cursor — each loads a different file | Point each harness entrypoint at untool-platform.md + CONSTITUTION (sync-script + CI no-drift gate, like the agent-roster pattern) | VERIFIED real gap. (Earlier same-session claim of "CONSTITUTION/copilot dup-line corruption" was FABRICATED by me — scans came back clean; no such corruption exists.) |
| 2026-05-31 | **Object Model shape inventory + UDA interop** — object-orient every data shape; gaps G1–G7 dispatched | G4/G7 in Codex PRs; G5 open; G1/G2/G3/G6 awaiting pickup | [docs/object-model-shape-inventory.md](docs/object-model-shape-inventory.md); PR #402 |
| 2026-05-31 | **Codex is implementing the forge generator** — G4→PR forge#29, G7→PR forge#30 (stacked), Experience kernel→PR #28/#31, certified-package lane→#32 | Land #29 then #30; pick up G5 (#26) next | Codex self-coordinates; no dup issue needed |
| 2026-05-31 | **#32 deferred follow-ups filed** — publishing #33, signing/SBOM #34, registry/channel #36, rich-IR coverage #37 (closed dup #35) | Sequence after #32 dry-run lands | forge repo |
| 2026-05-31 | **G5 vector projection (#26)** — Codex shipped it as PR forge#33 (`codex/vector-uda-projection-g5`, stacked on #30); explicit IR vector facet + `uda` target + BE-4 dim checks + goldens | Lands after the #29→#30→#33 stack merges | my "unclaimed" note raced the PR by ~1 min — corrected on #26 |
| 2026-05-31 | **#401 Fleet Commons Tier (Antigravity epic)** — peer epic at topology altitude; G1–G7 now its sub-issues | (resolved: umbrella'd + index posted) | complementary, not duplicate |
| 2026-05-31 | **#401 hand-picks ADR-038** — already taken (unified-process-and-time); must be `ARC-ADR-DRAFT-fleet-commons-tier` per repo rule | Flag on #401 / fix when the ADR is authored | CLAUDE.md ADR-numbering rule |
| 2026-05-31 | **contracts.md UDA forge-target** likely stale — lists C# `.g.cs`; UDA is rust-api-v2 → should be Rust `.g.rs` + Python `.g.py` (per #401 + our G4) | Verify the matrix row + correct | same truth our G4 rests on |
| 2026-05-31 | **IR access-pattern + persistence hints** (G1/G2) — UDA planner can't route without them | Phase-0 ADR via api-designer | keystone; unblocks forge + UDA. Issues #399/#400 |
| 2026-05-31 | **Commons sieve-report proof contract** — portable snap/quarantine evidence envelope now has a producer/consumer chain | Land commons-core#2 → forge#41 → backend-core#164 | contract artifact only; do not settle Commons-vs-Function runtime tier here |
| 2026-05-31 | **dlt as a first-party ontology source** — wire warehouse marts back into the sifter (BE-9) | After dbt marts exist (G6/BE #162) | closes data→ontology loop |
| 2026-05-31 | **agentarmy-forge missing `Enabler` label** — G4/G5/G7 filed with `agent-army-task` only | Create `Enabler` label in forge repo for SAFE parity | minor governance gap |
| 2026-05-30 | **The Choice Principle + Tangent Ledger** (this constitutional moment) | Land PR; balanced strictness set | Constitution + ledger landed this session |
| 2026-05-30 | **F# ontology compiler core** — category theory framing | Functors=projections, catamorphisms=generators, gUFO⟷BFO=nat. transformation | ADR-032/033; keep CT top-of-mind |
| 2026-05-30 | **Local model serving on the dev box** | Local embedder for ArcadeDB RAG (best fit); iGPU via OpenVINO | Hub issue #184; Core Ultra 7, NPU/iGPU, no dGPU |
| 2026-05-30 | **BYO-credentials → thin bootstrap container** | Evolve broker into bootstrap; watch Infisical agent-vault | ARC-ADR-037 built; design note in Labs |
| 2026-05-30 | **Serve every capability via MCP** (cloud + local) | Declarative registry + reconcile loop (not hand-cranked plumbing) | Fast queue-able add-and-use cadence |
| 2026-05-30 | **ArcadeDB platform IaC convergence** — live `arcadedb` app was Gordon/hand-deployed, drifted from template | Deploy `deploy/arcadedb-aca-platform.bicep` (or upgrade live secret to KV-ref) to fully converge | Plaintext `JAVA_OPTS` rotated to `secretRef`; `min=0→min=1` fixed live (single-writer lock) |
| 2026-05-30 | **Rotate leaked storage key** `starcadeeio2fcxu` (Azure Files behind arcadedb) | Regenerate key2 → ensure no consumer → regenerate key1; ACA env-storage `arcadedb-files` uses accountKey | Key echoed to transcript by the `az --query "[?…]"` cmd-echo bug — treat as exposed |
| 2026-05-30 | **ArcadeDB least-privilege** — backend-core + selfmodel-loader authenticate as `root` | Move backend-core → `platform_reader`, selfmodel-loader → scoped writer | Violates `docs/arcadedb-secret-hardening.md` ("no service uses root"); see follow-up issue |
| 2026-05-30 | **Hub `ARCADEDB_PASSWORD` Actions secret** purpose unclear | Confirm meaning + rotate if it's the root pw | Not referenced by committed hub workflows; may feed the selfmodel-loader job deploy |
| 2026-05-30 | **`arcadedb-live.yml` targets the legacy ACI box** (`aa-arcadedb-dev…azurecontainer.io`) | Repoint to the ACA internal endpoint or retire | Out of scope for the rotation; different server from the ACA `arcadedb` |

## 🌱 Parked — someday / not now

| Opened | Thread | Why parked |
|---|---|---|
| 2026-05-30 | **Operator-tunnel durability** (single session-bound connector) | Known gap #324; works today, revisit when it bites |
| 2026-05-30 | **Paid ngrok reserved subdomain** | cloudflared wins for now; KV `ngrok` token kept if we retry |
| 2026-05-31 | **Dapr secrets-store sidecar for prompt-router + broker** (proposed by a spoke agent re backend-core `config.py`) | Deferred: [ARC-ADR-037](docs/decisions/ARC-ADR-037-byo-credentials-secrets-broker.md) already chose KV + backend-agnostic broker ("no container, no new dep"); upgrade path is per-tenant vaults→OpenBao, not Dapr. Revisit only as "Dapr as a `store.py` backend *under* the broker" via ARC-ADR-DRAFT — never a parallel secret path bypassing broker audit |

## ✅ Landed — graduated or done

| Opened | Closed | Thread | Outcome |
|---|---|---|---|
| 2026-05-30 | 2026-05-30 | Establish the fleet constitution | `CONSTITUTION.md` + `TANGENTS.md` created, anchored in CLAUDE.md/AGENTS.md |

---

_Conventions: keep rows one-line. Dates are `YYYY-MM-DD`. Move threads between sections
freely — graduation to a board issue means a row moves to **Landed** with the issue link
as its outcome._
