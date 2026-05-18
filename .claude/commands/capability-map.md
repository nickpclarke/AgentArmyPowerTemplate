# Capability Map

Generate a business capability model and investment heat map for a business domain.

## Usage

```
/capability-map [business domain or organization name]
```

Example:
```
/capability-map our healthcare revenue cycle management
/capability-map the customer engagement domain
/capability-map the entire enterprise (high-level L0 only)
```

## What This Does

Invokes the `business-architect` agent to produce:

1. **L0 Capability Domains** — top-level capability groupings (5-9 items)
2. **L1 Capabilities** — major capabilities within each domain
3. **L2 Capabilities** (if domain is specified) — granular capabilities with definitions
4. **Capability Cards** — for each L1/L2: definition, owner, systems, current maturity, strategic importance
5. **Investment Heat Map** — color-coded table (Invest / Maintain / Harvest / Divest / Transform)
6. **Maturity Heat Map** — current vs target maturity gap visualization

Then optionally hands off to `capability-planner` for WSJF scoring and investment sequencing.

## Rules for Capability Modeling

- Capabilities describe WHAT, not HOW or WHO
- Capabilities are stable across org restructures
- Names are noun phrases, not verb phrases
- No technology in capability names
- Each capability has a single accountable owner

## Output Format

Text-format capability tree + markdown table heat maps. Copy into your Architecture Repository.
