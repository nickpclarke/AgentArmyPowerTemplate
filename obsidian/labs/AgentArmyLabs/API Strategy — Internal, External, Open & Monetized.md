---
tags: [vision, strategy, api, monetization, security, moc]
track: platform
status: draft
date: 2026-05-25
---
# API Strategy — Internal, External, Inner-Sourced, Open & Monetized

**🎛 [[Obsidian Board]] · 🧭 [[Platform Atlas]] · 🔌 [[Layer — API]]**

> [!abstract] Thesis
> AgentArmy's APIs serve **four audiences**, not one — internal plumbing, inner-sourced fleet collaboration, open-source community, and external paying consumers. The same **contract-first / mock-first** discipline runs through all four, but the *governance, visibility, and economics* differ per tier. The differentiated bet is **agent-native, pay-per-call** access: capabilities exposed as **MCP servers behind an HTTP-402 metered gateway** — *agents that pay agents*. **Monetization is the organizing constraint** (it dictates the gateway, the metering, the tiers), and **security is the enabling gate** (you cannot expose compute to the world without auth + rate-limit + cost caps).

---

## 1. The four audiences (the framing)

| Tier | Who consumes | Visibility | Primary concern | Postman home |
|---|---|---|---|---|
| **Internal (plumbing)** | the fleet's own layers (UI ↔ middle ↔ backend) | **private** | correctness, drift, parallel dev | private workspace |
| **Inner-source** | our own agents/teams across spokes | private, shared | reuse, discoverability, no duplication | private workspace |
| **Open source** | the world (read/run/fork the *commodity*) | **public** | adoption, trust, contribution | public repo + docs |
| **External commercial** | other people's apps **and agents** | **public, gated** | **revenue**, abuse/cost control | **public AgentArmyX** (product catalog) |

> [!tip] This resolves the "public vs private Postman" question
> It was never one workspace. **Internal plumbing stays private** (nobody outside cares; it's implementation). **External product APIs go to public [[AgentArmyX]]** — that workspace *is* the catalog the world subscribes to. The mocks being public HTTP endpoints is orthogonal to either.

---

## 2. Internal (plumbing) — the spine

The inter-layer contracts ([[Layer — API]], [[Universal Data Adapter]], MCR-F4 projection) are **implementation detail**. Doctrine already in force:

- **Contract-first + mock-first** — every contract is published *and mocked* up front so sandboxed spokes build in parallel before the real producer exists (see CLAUDE.md standing rule). Internal contracts live in a **private** Postman workspace.
- **Reachability caveat (open):** sandboxed/microVM coding agents may have **no egress** — they consume the *contract* via copy-in (vendored files), and the *mock URL* is hit by CI runners / the deployed app, which do have internet. ⚠️ **Verify per environment; don't assume.** (See [[Open Questions and Risks]].)

## 3. Inner-source ("crowdsourcing inner")

The fleet **is** an inner-source organization: many agents contributing across spokes against shared contracts. To make that compounding rather than chaotic:

- **Shared, discoverable contracts** — one registry (Postman + `docs/contracts.md`), generated clients, drift gates. No layer hand-rolls another's types.
- **Reusable building blocks** — agent definitions, skills, the runner templates, the model→projection factory. A contribution in one spoke is a *component* others reuse.
- **Low-friction contribution** — `copilot-task` / agent-army-task routing, PR review via `@`-mention bots, the HITL decision pattern for forks in judgment. Crowdsourcing *internally* = many cheap parallel agents against a stable contract spine ([[Model-Driven Platform]]).

## 4. Open source — the open-core boundary

The strategic question: **what do we give away to win adoption, and what do we keep to monetize?** Recommended **open-core** split:

- **Open (commodity / adoption flywheel):** the *template* (the AgentArmy hub itself), agent definitions, the self-hosted runner infra, the contract-first/mock-first tooling, the "one model, many projections" *ideas* ([[One Model, Many Projections]]). These build trust, community, and a hiring/credibility funnel.
- **Closed (the moat / monetized core):** the running **platform capabilities** — the live UDA over real connectors, the hosted reasoning/ontology engine, the agent runtime *as a service*, the knowledge graph, and anything that costs us compute/LLM/data spend to run.

> [!tip] Open the *recipe*, sell the *kitchen*
> Open-source the patterns and the scaffolding (commodity, copyable anyway); charge for the **operated, metered, supported** instance. The model/projection thesis is more valuable as a *standard others adopt* than as a secret.

## 5. External commercial — the product surface

The outward APIs (detail in [[Scenarios as Agent Tools]]):

| Surface | What | Protocol |
|---|---|---|
| **Capabilities-as-API** | UDA query, knowledge/graph reads, reasoning, ingest | REST / GraphQL |
| **Agents as MCP servers** | our agents/tools callable by *other people's AI* natively | **MCP** + tool/resource manifests |
| **Subscriptions** | events others react to (graph updates, run/decision completions) | AsyncAPI + webhooks / SSE |
| **Monetization layer** | metered, pay-per-call access | **HTTP 402 / x402**, API keys, Stripe |

## 6. Monetization (above all)

> [!important] The organizing constraint
> Monetization isn't a feature bolted on at the end — it dictates the **architecture**. Everything external flows through a **metered gateway**; the gateway is the product.

- **Model: open-core + usage-based.** Free/OSS scaffolding → paid operated capability. Charge on the units that cost us: **per agent-run, per UDA query, per reasoning job, per 1k tokens, per ingest GB** — plus subscription tiers for committed capacity.
- **Agent-native payments — the differentiator.** Expose capabilities as **MCP tools behind HTTP `402 Payment Required` / x402**, so an autonomous *external agent* can discover a tool, get a 402 with a price, pay, and call — **agents paying agents per call**. This is the novel surface for a *meta*-platform in the agentic economy; plain REST + API keys is table stakes.
- **Billing rails:** Stripe for human/dev customers (metered billing, invoices); x402 (stablecoin/crypto) for autonomous agent micropayments. Meter at the gateway; reconcile to billing.
- **Tiering:** free (mock/sandbox + tiny quota to drive adoption) → metered pay-as-you-go → committed subscription (FinOps-friendly caps).

## 7. Security — the enabling gate

> [!warning] You cannot expose compute to the world without controls
> An external caller hitting LLM / UDA / agent compute with no guardrails = **unbounded spend + abuse from a single actor**. The gateway (auth + rate-limit + **cost caps** + 402 metering) is the *prerequisite*, not an enhancement.

Per-tier security posture:

- **Internal/inner-source:** trust model is **private repos + trusted-only write + no forks** (owner-confirmed). Self-hosted CI is safe *because* of that invariant — don't over-engineer fork defenses that guard a non-existent path (see ARC-ADR-020). Revisit only if a repo goes public.
- **External (the hard part):**
  - **Edge:** API gateway — authN/Z, per-key + per-principal **rate limits**, **hard cost caps / budgets**, WAF/abuse detection, quotas.
  - **AuthZ:** extend per-connection RBAC (ARC-ADR-013) to external principals; least-privilege every exposed capability.
  - **Egress/SSRF:** the ingest/connector endpoints take user-supplied URIs — allowlist + private-IP blocking (ARC-ADR-017; already flagged on backend-core #66's URI-ingest).
  - **Secrets:** never in published artifacts; resolve via Key Vault/OIDC (ARC-ADR-011). Public Postman = **synthetic mock data only**.
  - **Supply-chain:** least-privilege runner identity (a bad dep in even a trusted PR is the residual risk once forks are out of scope).
  - **Tenancy/PII:** isolation boundary + audit trail before multi-tenant external load (backlog horizon).

## 8. How it maps to the fleet (architecture)

- **Two Postman tiers:** private (internal plumbing) + public **[[AgentArmyX]]** (external product catalog). Mocks let consumers (and external devs) build before GA.
- **API gateway** in front of all external surfaces — the meter, the authN/Z, the cost cap. *(New decision — no ADR yet.)*
- **MCP packaging** — wrap capabilities as MCP servers with manifests + 402.
- **Billing/metering** service — Stripe + x402, reconciled from gateway usage. *(New decision — no ADR yet.)*

## 9. Decisions this implies (ADR queue)

- ✅ exists: **ARC-ADR-013** per-connection RBAC · **ARC-ADR-017** connector egress/SSRF · **ARC-ADR-011** secret resolution · **ARC-ADR-020** self-hosted runner trust.
- 🆕 needed:
  - **API gateway & edge-policy** (rate-limit, cost caps, edge authN/Z, routing) — *graduate the backlog horizon entry*.
  - **402 / metering / billing model** (units, x402 vs Stripe, free/paid tiers).
  - **Open-core boundary** (what's OSS vs commercial) + license choice.
  - **External tenancy & abuse/cost-control** policy.

## 10. Phasing (crawl → walk → run)

1. **Crawl:** one capability (e.g. a UDA read or a single agent) exposed as **one MCP tool behind a metered 402 gateway**. Prove the *external-agent-pays-and-calls* loop end-to-end. Don't expose the whole surface.
2. **Walk:** add REST/GraphQL for human/dev consumers; Stripe metered billing; publish the product specs to public [[AgentArmyX]]; open-source the scaffolding tier.
3. **Run:** subscriptions/events (AsyncAPI), more capabilities, committed tiers, multi-tenant isolation, x402 agent micropayments at scale.

---

## 11. Market research & benchmarks (2026)

*Externally researched + cited (2026-05-25). Self-reported vendor metrics flagged.*

**Agent-native payments are real — ship Stripe-first, x402 in parallel (not x402-only).**
- **x402** (Coinbase, Apache-2.0, HTTP-402 + USDC) is past bleeding-edge: ~**165M cumulative txns / ~$600M annualized** (self-reported, Apr 2026), now under the **Linux Foundation**; **AWS Bedrock AgentCore Payments** (preview, Apr 2026) and **Stripe** both integrate it. ([Coinbase](https://www.coinbase.com/developer-platform/discover/launches/x402); [AWS](https://aws.amazon.com/blogs/machine-learning/agents-that-transact-introducing-amazon-bedrock-agentcore-payments-built-with-coinbase-and-stripe/))
- **Stripe MPP** (Machine Payments Protocol, launched Mar 2026; Anthropic/OpenAI/Shopify at launch) covers high-frequency fiat+stablecoin sessions. ([Stripe](https://stripe.com/blog/machine-payments-protocol)) Stripe's **x402** support is **US-only / preview** today. ([Stripe docs](https://docs.stripe.com/payments/machine/x402))
- Others: **Google AP2** (60+ partners incl. Mastercard/PayPal, → FIDO governance), **Skyfire** (KYA + payments), **L402** (Bitcoin-native, niche), **Nevermined** (wraps MCP with paywall; 1.38M txns).
- **Call:** Stripe usage-based metered billing = production revenue rail (global, enterprise, human buyers); **x402 additive** for agent-to-agent calls. The AWS AgentCore + Stripe + Coinbase stack is the reference hybrid. ([WorkOS comparison](https://workos.com/blog/x402-vs-stripe-mpp-how-to-choose-payment-infrastructure-for-ai-agents-and-mcp-tools-in-2026))

**Pricing/billing:** per-call / per-token + prepaid credits dominate (every major LLM API). Tooling: Stripe Billing, **Metronome** (Stripe-owned), **Orb**, **Lago** (OSS/self-host). The #1 churn driver is **"bill shock"** (78% of IT leaders hit unexpected AI bills, 2026) — real-time usage dashboards + soft/hard budget caps are table-stakes. ([Metronome](https://metronome.com/blog/ai-pricing-in-practice-2025-field-report-from-leading-saas-teams); [Lago](https://getlago.com/blog/the-full-playbook-how-to-design-usage-based-pricing-models))

**Open-core works — Apache-2.0/MIT scaffolding, never BSL/SSPL.**
- Validated: **dbt** ($100M ARR → Fivetran merge), **Temporal** (184% NRR), **Supabase** ($70M ARR, 250% YoY) — all open the tool, sell the operated/governed cloud. ([Sacra/dbt](https://sacra.com/c/dbt/); [Supabase](https://sacra.com/research/supabase-at-70m-arr-growing-250-yoy/))
- **Cautionary:** HashiCorp **BSL** → OpenTofu fork (didn't reverse post-IBM); Elastic **SSPL** → OpenSearch (didn't reverse even after Elastic re-added AGPL). Source-available licenses trigger enterprise legal blocks + durable hyperscaler forks. **Use Apache-2.0/MIT for scaffolding; proprietary only for operated services.** ([Spacelift](https://spacelift.io/blog/terraform-license-change); [FlowVerify](https://www.flowverify.co/blog/open-source-relicensing-2026-what-happened))

**MCP monetization is early — first-mover window.** ~11,000 MCP servers, 8M downloads, **<5% monetized**; MCP now under the Linux Foundation (AAIF). Marketplaces exist (Apify 80% rev-share, MCPize, Nevermined, Moesif metering) but no dominant operator-grade platform — the open-core "sell the operated capability" gap is exactly what's missing. ([DEV.to](https://dev.to/krisying/mcp-servers-are-the-new-saas-how-im-monetizing-ai-tool-integrations-in-2026-2e9e); [Nevermined](https://nevermined.ai/blog/mcp-monetization-ai-agents))

**Security — "Denial of Wallet" is the named threat.** Cost-asymmetry abuse from one caller (documented: a leaked Gemini key → **$82K in 48h**, 457× normal). Standard mitigation = the 3-layer gateway: per-caller **dollar** quotas, soft alerts + **hard caps**, request/abuse limits — plus **session-level pre-authorized budgets** for agent callers (the AgentCore pattern). ([Hands-on Architects](https://handsonarchitects.com/blog/2025/denial-of-wallet-cost-aware-rate-limiting-part-1/); [TrueFoundry](https://www.truefoundry.com/blog/rate-limiting-ai-agents-preventing-llm-api-exhaustion))

> [!tip] Net implication for the bet
> The infrastructure thesis holds: ship **Stripe-metered REST/MCP now + x402 for agent calls**, **Apache-2.0 scaffolding** with a proprietary operated core, and treat **bill-shock/Denial-of-Wallet controls as launch-blocking, not polish**. The MCP-monetization market is early enough that **distribution beats payment-protocol choice** in the first ~18 months.

---

> [!question] Open questions (post-research)
> - Which **first capability** is the monetization beachhead (UDA query? an agent? reasoning)? *(still open — product call)*
> - ~~x402 maturity~~ → **resolved:** Stripe-first, x402 parallel (above).
> - The **open-core line** — does the model/projection factory stay closed, or is it the standard we *want* widely adopted? *(Apache-2.0 for whatever's opened — never BSL/SSPL.)*
> - MicroVM agent **egress** — confirmed unknown; gates how "mock-as-producer-endpoint" actually works for sandboxed consumers.

Related: [[Model-Driven Platform]] · [[Universal Data Adapter]] · [[Scenarios as Agent Tools]] · [[Skills as a Projection]] · [[Governance in the Model]] · [[Open Questions and Risks]] · [[Layer — API]]
