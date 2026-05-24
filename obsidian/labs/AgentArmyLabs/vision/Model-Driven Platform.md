---
tags: [vision, moc]
---
# Model-Driven Platform — the vision

> [!abstract] The bet
> One canonical **model** describes the platform's objects, relationships, scenarios, policy, and projections. Everything else — C# contracts, ArcadeDB schema, OpenAPI, agent tools, this ontology — is a **projection** of that model. Code is disposable; the model is the asset.

This is the convergence of two threads we've been treating separately:
- [[Middle-Core]] — model → generated C# + an in-memory hypergraph runtime + evidence.
- [[Universal Data Adapter]] — a connection registry whose **CDM is the same model**.

## The expansion
- [[One Model, Many Projections]] — the unifying mechanic
- [[Codegen vs Interpreted]] — the core architectural tension
- [[Evidence as a Primitive]] — trust, audit, and the deterministic spine
- [[Scenarios as Agent Tools]] — why this *is* the agent capability layer
- [[Skills as a Projection]] — the model as a *skill factory* (C# is just one output)
- [[Governance in the Model]] — policy/DMN/SHACL as data, not bolt-ons
- [[Prior Art]] — LinkML, Foundry, EnterpriseWeb, Temporal, dbt
- [[Open Questions and Risks]] — where this could go wrong

> [!tip] Why it matters for AgentArmy
> Agents are non-deterministic. A deterministic, evidenced, model-driven core is the **stable spine** they act *through*: agents propose, the runtime disposes, evidence proves.
