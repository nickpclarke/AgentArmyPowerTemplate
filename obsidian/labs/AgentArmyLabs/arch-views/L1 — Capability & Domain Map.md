---
tags: [moc, platform, arch-view, capability]
track: platform
date: 2026-05-28
---
# L1 — Capability & Domain Map

**🗺 [[Architecture Atlas — Conceptual to Contract]] · ⬆ [[L0 — Untool.ai System Context]] · ⬇ [[L2 — Container Topology (Tier x Repo)]] · 🧭 [[Platform Atlas]]**

> [!abstract] What this view answers
> *What the platform can do, grouped into domains, and which spoke realizes each.* This decomposes the single L0 system into a capability model — eight domains, each annotated with its realizing repo (`hub` / `FE` / `MC` / `BE`) and a maturity read. It sits between the L0 context and the per-layer notes below it.

## Capability map

```mermaid
flowchart TB
    subgraph UI["UI — realized by FE (frontend-core)"]
        direction TB
        UI1["Projection UIs from model"]:::live
        UI2["CopilotKit chat surface"]:::live
        UI3["BFF: session-cookie to JWT"]:::live
    end

    subgraph API["API — realized by BE (backend-core)"]
        direction TB
        API1["OpenAPI / GraphQL contracts"]:::live
        API2["Metered MCP / 402 gateway"]:::planned
        API3["Stripe + x402 billing"]:::planned
        API4["MCP tool packaging"]:::building
    end

    subgraph WORK["Worker / Agent-runtime — realized by MC (middle-core)"]
        direction TB
        WK1["Scenario execution"]:::building
        WK2["Agentic loop: policy + evidence + safety"]:::building
        WK3["Model to projection factory"]:::live
        WK4["Universal Data Adapter pipelines"]:::building
    end

    subgraph DATA["Data — realized by BE (backend-core)"]
        direction TB
        D1["ArcadeDB graph + vector store"]:::live
        D2["Embeddings: Cohere embed-v-4"]:::live
        D3["UDA connector registry"]:::building
        D4["Projection / evidence pipelines"]:::building
    end

    subgraph KNOW["Knowledge / Ontology — realized by MC + BE"]
        direction TB
        K1["RDF ingest + SHACL validation"]:::building
        K2["Fuseki reasoning store"]:::planned
        K3["Ontology to code forge"]:::building
        K4["UFO / BFO modeling"]:::building
    end

    subgraph INFRA["Infra — realized by hub"]
        direction TB
        I1["Self-hosted ACA runners"]:::live
        I2["Container tiering: platform / app / function"]:::live
        I3["Secrets: Key Vault / OIDC"]:::live
        I4["Cloud-agent control plane (MCP)"]:::live
    end

    subgraph GOV["Governance — realized by hub"]
        direction TB
        G1["HITL decision pattern"]:::live
        G2["ADRs + ARMY_PRINCIPLES"]:::live
        G3["Contract registry"]:::live
        G4["Agent onboarding rubric"]:::live
    end

    subgraph DELIV["Delivery / Ops — realized by hub"]
        direction TB
        Dv1["Two-army routing"]:::live
        Dv2["Fleet heartbeat"]:::live
        Dv3["Contract registry + mocks"]:::building
        Dv4["Autonomous review loop + CI"]:::live
    end

    classDef live fill:#1d4d3e,stroke:#3ec98a,color:#fff;
    classDef building fill:#5c3b00,stroke:#e0a040,color:#fff;
    classDef planned fill:#3a2a4d,stroke:#a06cd5,color:#fff;
```

> [!note] Legend
> Green = live · Amber = building (active work in flight) · Purple = planned. Domain headers name the realizing spoke: `FE` frontend-core, `MC` middle-core, `BE` backend-core, `hub` the template repo.

## The capability model

**Domain decomposition.** The eight domains are a MECE capability cut of the L0 system: three are *product* domains the spokes deliver against (UI, API, Worker/Agent-runtime, Data), one is the *differentiating intelligence* (Knowledge/Ontology), and three are *platform-of-platforms* domains the hub owns to keep the fleet coherent (Infra, Governance, Delivery/Ops). Each domain is a stable grouping of capabilities, not an org chart — a capability can be co-realized across spokes (Knowledge/Ontology spans MC for modeling/forge and BE for the read surface and reasoning store), which is why this view annotates realization separately from grouping.

**Spoke ownership.** Realization maps cleanly to the hub-and-spoke topology: **FE (frontend-core)** owns UI — model-driven projection screens, the CopilotKit chat surface, and the BFF that injects JWTs (ARC-ADR-002). **BE (backend-core)** owns API and Data — the contract surface, the planned metered MCP/402 gateway, ArcadeDB graph+vector storage, and the UDA connector registry. **MC (middle-core)** owns Worker/Agent-runtime — scenario execution, the policy/evidence/safety agentic spine, and the model→projection factory — and co-owns Knowledge/Ontology. **hub** owns Infra, Governance, and Delivery/Ops — the runners, container tiering, secrets, HITL/ADR governance, the contract registry, and the two-army control loop with its fleet heartbeat.

**Where the investment heat is.** Live capabilities cluster in the platform substrate (runners, container tiering, secrets, governance, two-army routing, heartbeat) and the data store (ArcadeDB + embeddings) — the table stakes are in place. The active heat is on two fronts: the **forge / ontology** track (ontology→code forge, RDF ingest + SHACL, UFO/BFO modeling per ARC-ADR-029 and recent scaffold work) and the **contract backlog** (registry + mocks, MCP packaging) that unblocks parallel spoke development. The strategically valuable but still-planned capabilities — the metered MCP/402 gateway, Stripe + x402 billing, and the Fuseki reasoning store — are exactly the monetized core from L0; they are gated behind the contract and forge work maturing first.

---

Related: [[L0 — Untool.ai System Context]] · [[Platform Atlas]] · [[Layer — UI]] · [[Layer — API]] · [[Layer — Worker]] · [[Layer — Data]] · [[Layer — Infra]] · [[Architecture Atlas — Conceptual to Contract]]
