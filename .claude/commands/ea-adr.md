# Architecture Decision Record

Create an Architecture Decision Record (ADR) in MADR v4.0 format for a significant architectural decision.

## Usage

```
/ea-adr [decision title or topic]
```

Example:
```
/ea-adr API gateway technology selection
/ea-adr authentication strategy for B2B customers
/ea-adr data replication approach for disaster recovery
```

## What This Does

Invokes the `togaf-adm-advisor` agent to produce a complete MADR v4.0 Architecture Decision Record covering:

- **Context and Problem Statement** — why this decision is needed
- **Decision Drivers** — architecture principles, requirements, constraints being balanced
- **Considered Options** — 3-4 alternatives evaluated
- **Decision Outcome** — chosen option with positive and negative consequences
- **Pros and Cons of Options** — structured analysis per option
- **Confirmation** — how to verify the decision is implemented correctly
- **More Information** — related ADRs, follow-up decisions needed

## Document Convention

ADRs are stored as:
```
docs/decisions/ARC-ADR-[NNN]-[kebab-title].md
```

Status values: Proposed → Accepted → Deprecated → Superseded

## Context

ADRs are the primary mechanism for recording architectural decisions in the Architecture Repository. Every significant architectural choice should have an ADR. They are the institutional memory that survives team turnover.
