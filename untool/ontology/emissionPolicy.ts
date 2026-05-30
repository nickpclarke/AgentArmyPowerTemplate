// untool/ontology/emissionPolicy.ts
//
// EMISSION POLICY — the heart of untool's privacy + trust character.
//
// When a tool runs, it emits results. The emission policy decides:
//   - what's in the payload (full output? redacted? summary?)
//   - what scope it lives in (swarm-private? user-private? public?)
//   - what trust grade attaches to it
//   - what fingerprint chain it inherits
//
// This is the place where untool's opinions about provenance and privacy
// crystallize. A liberal policy makes downstream reasoning richer but leaks more.
// A conservative policy is private and trust-preserving but starves downstream
// agents of context.
//
// Related: ARC-ADR-044 (architecture), ARC-ADR-037 (credentials-broker, where
// per-user identity resolves), ARC-ADR-038 (RDF↔LPG projection, where emissions
// land in the graph), ARC-ADR-042 (temporal pulse, the `at` field below).
//
// See also:
//   obsidian/labs/AgentArmyLabs/Untool-Ontology-Orchestrated-Swarm-Intelligence.md

// ─────────────────────────────────────────────────────────────────────────────
// Types (sketch — final shapes live in the ontology, generated from OWL)
// ─────────────────────────────────────────────────────────────────────────────

export type Cid = string  // content-addressed identifier (IPLD-style)
export type Fingerprint = string  // signed hash chain segment
export type TrustGrade = 'platform' | 'official' | 'community' | 'unverified'
export type Ecosystem = 'fleet' | 'anthropic-skills' | 'mcp-official' | 'community' | 'custom'

export interface Scope {
  visibility: 'public' | 'swarm-private' | 'user-private'
  swarm?: string  // when swarm-private
  user?: string   // when user-private
}

export interface ToolHolon {
  id: string
  ecosystem: Ecosystem
  trustGrade: TrustGrade
  isMutating: boolean
  emitsContaining?: ('pii' | 'secrets' | 'financial' | 'health')[]
}

export interface User { id: string }
export interface Swarm { id: string; participants: string[] }

export interface SwarmContext {
  user: User
  swarm: Swarm
  goal: { sensitivity: 'low' | 'medium' | 'high' }
}

export interface Emission {
  payload: Cid
  emitter: string
  trustGrade: TrustGrade
  scope: Scope
  fingerprint: Fingerprint
  timestamp: number
}

// ─────────────────────────────────────────────────────────────────────────────
// The policy contract
// ─────────────────────────────────────────────────────────────────────────────

export interface EmissionPolicy {
  /**
   * Classify the raw tool output into a stored payload + a list of fields
   * that were redacted from it. Returns the CID of the stored payload.
   */
  classifyPayload(
    raw: unknown,
    tool: ToolHolon,
    ctx: SwarmContext
  ): { payload: Cid; redactions: string[] }

  /**
   * Assign the scope this emission lives in. Determines who can see it
   * via graph-traversal access checks at query time.
   */
  assignScope(tool: ToolHolon, ctx: SwarmContext): Scope

  /**
   * Compute the trust grade for this emission, given the tool's own grade
   * and the trust of any upstream emissions that fed into the call.
   */
  computeTrust(
    tool: ToolHolon,
    upstream: Emission[],
    ecosystem: Ecosystem
  ): TrustGrade

  /**
   * Compute the fingerprint chain for this emission.
   * Chains the parents' fingerprints with this call's content.
   */
  chainFingerprint(parents: Emission[], thisCallContent: Cid): Fingerprint
}

// ─────────────────────────────────────────────────────────────────────────────
// ★ LEARNING-MODE TODO ★
//
// Write your defaults here. This 5–10 line function defines untool's
// privacy + trust character more than any other code in the codebase.
//
// Key questions to answer with your defaults:
//
//   Q1. PAYLOAD REDACTION — conservative or permissive?
//       Conservative: redact PII / secrets / financial / health unless
//                     the tool's emissionPolicy explicitly allows.
//                     Safer; downstream context is leaner.
//       Permissive:   store full payload; downstream agents decide what to use.
//                     Richer reasoning; bigger leak surface.
//
//   Q2. SCOPE DEFAULT — swarm-private or user-private?
//       Swarm-private allows all participants (other agents + humans in the
//       swarm) to read; user-private restricts to the originating user only.
//       Group flows want swarm-private; sensitive solo flows want user-private.
//
//   Q3. TRUST INHERITANCE — minimum, average, or weighted?
//       Minimum: an emission is at most as trusted as its least-trusted input.
//                Strongest guarantee; quarantines low-trust inputs aggressively.
//       Average: trust degrades gradually. Easier to work with; weaker guarantee.
//       Weighted: tool's own grade dominates; inputs nudge. Most realistic.
//
//   Q4. CROSS-USER LEAKAGE — hard invariant or soft policy?
//       Hard: a graph constraint that physically prevents user-A emissions from
//             being visible in user-B queries, enforced in ArcadeDB query layer.
//             Strongest. Engineering cost.
//       Soft: policy with logged violations. Faster to ship. Audit-recoverable
//             but not preventive.
//
// ─────────────────────────────────────────────────────────────────────────────

export const defaultEmissionPolicy: EmissionPolicy = {
  classifyPayload(_raw, _tool, _ctx) {
    // TODO: implement default redaction strategy.
    // Suggested starting point (conservative):
    //   - if tool.emitsContaining includes pii/secrets/financial/health,
    //     redact those fields unless ctx.goal.sensitivity === 'low'
    //   - store remaining payload via content-address (IPLD)
    //   - return both the CID and the list of redacted field paths
    throw new Error('TODO: define classifyPayload defaults')
  },

  assignScope(_tool, _ctx) {
    // TODO: implement default scope assignment.
    // Suggested starting point:
    //   - default to swarm-private
    //   - downgrade to user-private when tool is mutating + ecosystem !== 'fleet'
    //   - upgrade to public only when explicitly tagged (never automatically)
    throw new Error('TODO: define assignScope defaults')
  },

  computeTrust(_tool, _upstream, _ecosystem) {
    // TODO: implement default trust computation.
    // Suggested starting point (minimum-trust inheritance):
    //   - if any upstream is 'unverified', this emission is 'unverified'
    //   - else take min(tool.trustGrade, min(upstream.trustGrade))
    //   - ecosystem 'fleet' may upgrade by one tier
    throw new Error('TODO: define computeTrust defaults')
  },

  chainFingerprint(_parents, _thisCallContent) {
    // TODO: implement default fingerprint chaining.
    // Suggested starting point:
    //   - hash(parents.map(p => p.fingerprint).join('|') + ':' + thisCallContent)
    //   - sign with emitter's keypair (out-of-band — keys live in credentials-broker)
    //   - return the signed segment
    throw new Error('TODO: define chainFingerprint defaults')
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Notes for the spike + v1 build
// ─────────────────────────────────────────────────────────────────────────────
//
// 1. The spike (Untool-Team-Composer-Spike.md) does NOT exercise this policy —
//    it composes teams without emitting yet. This file exists so when emissions
//    DO turn on (v1 sprint: "emissions store + sign + DAG semantics"), the
//    defaults are already opinionated and reviewed.
//
// 2. The signing key lives in credentials-broker (ARC-ADR-037), looked up by
//    holon fingerprint. Do not hardcode keys here.
//
// 3. The CID strategy can start as SHA-256 over canonical JSON; upgrading to
//    IPLD links is a v2 task.
//
// 4. When a tool is *uncertain* about its output (model hallucination risk,
//    unverifiable source), it should down-mark its own trustGrade BEFORE this
//    policy runs. The policy then propagates; the tool's self-assessment is
//    the upstream signal.
//
// 5. Hallucination quarantine pattern: an emission with no upstream tool-call
//    trigger should default to trustGrade = 'unverified' regardless of emitter.
//    That's pure model claim; downstream consumers need to know.
//
// 6. CONVICTION vs TRUST (CSI / Rosenberg lineage — see
//    obsidian/labs/AgentArmyLabs/Conversational-Swarm-Intelligence-Mapping.md):
//    when conviction-weighted aggregation lands, the Emission interface will
//    gain a separate `conviction: Conviction` field. Trust = how much I believe
//    the source. Conviction = how strongly the source itself feels. A high-trust
//    agent saying "maybe X" deserves different weight than the same agent saying
//    "definitely X." The aggregation curve (linear / sigmoid / quadratic) lives
//    in a separate policy interface — ARC-ADR-044 Open Decision D.
//
// 7. SYNTHESIS emissions are first-class — when a `synthesis-role` agent emits,
//    its trigger chain references ALL upstream emissions it synthesized (not just
//    the most recent). The chainFingerprint default below must handle the many-
//    parent case correctly; it's not a one-parent chain.
