---
tags: [moc, platform, arch-view, conceptual]
track: platform
date: 2026-05-28
---
# L0 — Untool.ai System Context

**🗺 [[Architecture Atlas — Conceptual to Contract]] · 🧭 [[Platform Atlas]] · ⬇ [[L1 — Capability & Domain Map]]**

> [!abstract] What this view answers
> *Who uses the platform, what they get, and how value (and money) crosses its boundary.* This is the highest-abstraction view in the atlas — one system, its actors, and its external dependencies. Everything below it (capabilities, layers, contracts) decomposes this single box.

## System context

```mermaid
flowchart TB
    %% ===== Center: the platform as one system =====
    subgraph PLATFORM["Untool.ai / AgentArmy — model-driven, ontology-first agentic delivery platform"]
        direction TB
        GATEWAY["Metered MCP / HTTP-402 gateway<br/>(product surface: auth + rate-limit + hard cost caps)"]
        CORE["Hub + spokes (FE / MC / BE / infra)<br/>contract-first, two-army control loop"]
        GATEWAY --> CORE
    end

    %% ===== Internal / inner-source actors =====
    OPER["Operators / EA (human)<br/>steer, govern, decide (HITL)"]
    ARMIES["Two AI armies<br/>Claude Code + GitHub Copilot"]
    FLEET["Internal fleet layers<br/>FE / MC / BE inner-source consumers"]

    %% ===== Open-source actor =====
    OSS["Open-source community<br/>fork the recipe (Apache-2.0 scaffolding)"]

    %% ===== External commercial actors =====
    DEVS["External human devs / customers<br/>REST + GraphQL, Stripe-metered"]
    AGENTS["External autonomous agents<br/>x402 micropayments + MCP discovery"]

    %% ===== External SaaS dependencies =====
    SAAS["ext SaaS<br/>LLMs (OpenAI / Anthropic / Cerebras), Tavily,<br/>GitHub, Azure, GCP, Cloudflare, Stripe / x402"]

    %% ===== Edges =====
    OPER -->|"govern, set principles, resolve decisions"| PLATFORM
    ARMIES -->|"build the platform (deep + fast)"| PLATFORM
    PLATFORM -->|"dispatch work, request review"| ARMIES
    FLEET -->|"consume internal contracts (private)"| CORE
    OSS -->|"adopt / contribute commodity scaffolding"| CORE
    DEVS -->|"subscribe + call (paid)"| GATEWAY
    AGENTS -->|"discover tool, pay per call (402/x402)"| GATEWAY
    PLATFORM -->|"reasoning, search, hosting, CI, billing"| SAAS

    %% ===== Styling =====
    classDef internal fill:#1e3a5f,stroke:#4a90d9,color:#fff;
    classDef open fill:#1d4d3e,stroke:#3ec98a,color:#fff;
    classDef commercial fill:#5c3b00,stroke:#e0a040,color:#fff;
    classDef extsaas fill:#3a2a4d,stroke:#a06cd5,color:#fff;
    classDef platform fill:#111827,stroke:#9ca3af,color:#fff;

    class PLATFORM,GATEWAY,CORE platform;
    class OPER,ARMIES,FLEET internal;
    class OSS open;
    class DEVS,AGENTS commercial;
    class SAAS extsaas;
```

> [!note] Legend
> Blue = internal / inner-source · Green = open-source community · Amber = external commercial (paying) · Purple = external SaaS dependency · Grey = the platform system + its gateway product surface.

## The bet, stated as architecture

**Value proposition.** Untool.ai is "a platform that helps build platforms" — a model-driven, ontology-first, agentic software-delivery system. A canonical model and ontology drive many projections (UI, contracts, code, skills, knowledge graph); two autonomous AI armies build and govern those projections through a hub-and-spoke topology coordinated on a shared board. The productized form is **Untool.ai**; **AgentArmy** is the running implementation.

**Four audiences, one discipline.** The same contract-first / mock-first discipline serves four distinct consumer classes whose *governance, visibility, and economics* differ: **internal plumbing** (private inter-layer contracts), **inner-source** (fleet agents and teams reusing shared contracts and building blocks), **open-source** (commodity scaffolding the world can fork), and **external commercial** (gated, metered consumers). The L0 boundary makes those four explicitly visible because they pull the architecture in four different directions.

**Monetization is the organizing constraint; security is the enabling gate.** The differentiated bet is *agent-native, pay-per-call* access — capabilities wrapped as **MCP servers behind an HTTP-402 / x402 metered gateway** so external autonomous agents discover a tool, receive a price, pay, and call ("agents that pay agents"). That gateway is the product, and it dictates the architecture rather than bolting on at the end. Security is the prerequisite, not a polish step: exposing LLM / UDA / agent compute to the world demands auth, per-principal rate limits, and **hard cost caps** — the named threat is **Denial of Wallet** (cost-asymmetry abuse from a single caller). Stripe meters human/dev customers; x402 settles autonomous-agent micropayments; both reconcile at the gateway.

**The open-core boundary.** The system deliberately splits what crosses the boundary as open versus operated: **open the recipe** — the template hub, agent definitions, runner infra, and contract-first tooling (Apache-2.0 / MIT, never source-available) to win adoption and trust; **sell the kitchen** — the live Universal Data Adapter, the hosted reasoning / ontology engine, and the agent runtime-as-a-service, i.e. everything that costs compute, LLM, or data spend to operate. The open-source community and the external commercial actors sit on opposite sides of that line, both visible at this level.

---

Related: [[API Strategy — Internal, External, Open & Monetized]] · [[Platform Atlas]] · [[Architecture Atlas — Conceptual to Contract]] · [[L1 — Capability & Domain Map]]
