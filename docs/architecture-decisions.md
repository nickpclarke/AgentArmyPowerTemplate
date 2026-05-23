# Architecture Decisions

How to document significant architecture decisions using Architecture Decision Records (ADRs).

## What is an ADR?

An Architecture Decision Record (ADR) documents:
- **Decision**: What choice are we making?
- **Context**: Why are we making it? What problem does it solve?
- **Alternatives**: What other options did we consider?
- **Rationale**: Why is this the best choice?
- **Consequences**: What are the trade-offs?

## Format (MADR v4.0)

```markdown
# [Decision Title]

**Status**: Proposed | Decided | Superseded | Deprecated

## Context

[Problem statement. Why do we need this decision?]

## Decision

[Statement of the decision we've made.]

## Alternatives

### [Alternative 1]
[Pros/cons]

### [Alternative 2]
[Pros/cons]

## Rationale

[Why did we choose this? Trade-offs considered.]

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Risk 1
- Risk 2

## Related Decisions
- Relates to [ADR-001]
- Supersedes [ADR-003]
```

## Using /ea-adr Skill

In Claude Code:

```
/ea-adr migrate from monolith to microservices
```

Returns:
- ADR document in MADR format
- Context and problem statement
- Alternatives analysis
- Recommended decision
- Consequences and risks

## Example

```markdown
# Use PostgreSQL for transactional database

**Status**: Decided

## Context
We need a reliable, ACID-compliant database for order processing.
Current MySQL has scaling limitations and limited JSONB support.

## Alternatives

### MySQL 8+
- Pros: Operational familiarity, lower licensing costs
- Cons: Limited JSONB, scaling challenges, weaker JSON indexing

### MongoDB
- Pros: Flexible schema, horizontal scaling
- Cons: Eventually consistent, ACID transactions limited

### PostgreSQL
- Pros: ACID compliance, JSONB support, JSON indexing, horizontal scaling via sharding
- Cons: More complex operational model, licensing questions at scale

## Decision
Adopt PostgreSQL as primary transactional database.

## Consequences

### Positive
- Strong ACID guarantees
- Excellent JSON support for flexible schema
- Community-driven development
- Cost transparency

### Negative
- Team learning curve (Postgres administration)
- Connection pooling complexity
- More resources than MySQL
```

## Managing ADRs

Store ADRs in version control (Git) so they're:
- Versioned and timestamped
- Reviewable via pull requests
- Searchable by other engineers
- Historical record of decisions

## Related Docs

- **[Wardley Mapping](wardley.md)**
- **[Capability Maps](capability-maps.md)**
