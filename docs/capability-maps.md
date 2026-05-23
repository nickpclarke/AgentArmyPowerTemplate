# Business Capability Maps

Hierarchical decomposition of organizational capabilities.

## What is a Capability?

A capability is something the organization "does" — abstractly.

Examples:
- Account Management (sign up, login, profile)
- Order Processing (quote, create, fulfill)
- Inventory Management (track stock, reorder)
- Reporting (financial reports, analytics)

## Capability Hierarchy

```
Level 0: Customer Engagement
├── Level 1: Account Management
│   ├── Level 2: Authentication
│   ├── Level 2: User Profile
│   └── Level 2: Billing
├── Level 1: Support
│   ├── Level 2: Ticketing
│   ├── Level 2: Knowledge Base
│   └── Level 2: Chat
└── Level 1: Analytics
    ├── Level 2: Metrics
    ├── Level 2: Reports
    └── Level 2: Dashboards
```

## Building a Capability Map

### 1. Identify Business Domains
What are the major areas your business operates in?

### 2. Define Level 1 Capabilities
What are the key capabilities within each domain?

### 3. Decompose to Level 2
What sub-capabilities support each Level 1 capability?

### 4. Map to Technology
What systems/services implement each capability?

### 5. Assess Maturity
For each capability:
- Current state (manual/fragmented/integrated/optimized)
- Desired state
- Gaps and investments needed

## Using /capability-map Skill

In Claude Code:

```
/capability-map financial services
```

Returns:
- Hierarchical capability breakdown
- Technology mapping
- Investment heat map
- Roadmap recommendations

## Investment Prioritization

For each capability, assess:

| Dimension | Score | Notes |
|-----------|-------|-------|
| Strategic Importance | H/M/L | Core to business? |
| Current Performance | H/M/L | How mature? |
| Gap | — | (Strategic - Current) |
| Investment Priority | H/M/L | (Higher gap = higher priority) |

## Related Docs

- **[Wardley Mapping](wardley.md)**
- **[Architecture Decisions](architecture-decisions.md)**
