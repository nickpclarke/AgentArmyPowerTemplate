# 11 · Enterprise Architecture

TOGAF ADM-aligned enterprise architecture agents for US commercial and federal contexts. Covers the full EA lifecycle from Architecture Vision through Implementation Governance, with dedicated agents for Wardley strategic mapping, business capabilities, data architecture, platform engineering, security, and US regulatory compliance.

## Agents

| Agent | Model | TOGAF Phase | Purpose |
|---|---|---|---|
| `enterprise-architect` | opus | All phases | TOGAF ADM orchestrator, Architecture Repository governance, Architecture Vision |
| `togaf-adm-advisor` | sonnet | All phases | Phase-specific deliverable guidance, artifact templates, ADM tailoring |
| `wardley-strategist` | opus | A, B, E | Wardley value chains, evolution positioning, doctrine, climate, gameplay |
| `business-architect` | sonnet | B | Capability maps, value streams, operating models, BIZBOK |
| `solution-architect` | sonnet | E, F | ABB → SBB translation, solution docs, vendor evaluation, transition architectures |
| `information-architect` | sonnet | C (Data) | CDM/LDM, MDM, data governance, lineage, ILM, DAMA DMBOK |
| `capability-planner` | sonnet | B, E, F | WSJF prioritization, investment roadmaps, portfolio backlog linking |
| `integration-architect` | sonnet | C (App), D | API strategy, EDA, canonical data model, ESB modernization |
| `security-architect` | opus | Cross-cutting | Zero Trust (NIST SP 800-207), NIST CSF 2.0, FedRAMP, CMMC |
| `platform-architect` | sonnet | D | IDP, Team Topologies, Backstage, golden paths, DORA metrics |
| `us-regulatory-architect` | sonnet | Cross-cutting | FISMA/RMF, HIPAA, CMMC, PCI DSS v4, SOX ITGC, CCPA/CPRA |

## Typical Engagement Flows

### New Initiative (Technology Investment)
```
enterprise-architect (Architecture Vision, Phase A)
  → wardley-strategist (strategic positioning)
  → business-architect (Phase B: capabilities, value streams)
  → capability-planner (WSJF, investment case)
  → information-architect (Phase C: data architecture)
  → integration-architect (Phase C: application integration)
  → security-architect (security by design)
  → us-regulatory-architect (compliance constraints)
  → solution-architect (Phase E/F: SBBs, transition architecture)
  → platform-architect (Phase D: technology standards)
  → enterprise-architect (Architecture Contract, Phase G)
```

### Strategic Review (Where Should We Invest?)
```
wardley-strategist (map current landscape)
  → business-architect (capability maturity assessment)
  → capability-planner (WSJF scoring, heat maps)
  → enterprise-architect (Architecture Roadmap update)
```

### Platform Engineering Program
```
enterprise-architect (scope, principles)
  → platform-architect (IDP architecture, Team Topologies design)
  → security-architect (shift-left security design)
  → integration-architect (API gateway, service mesh)
  → capability-planner (platform capability roadmap)
```

### Regulatory Compliance Program
```
us-regulatory-architect (requirement decomposition)
  → security-architect (control design)
  → information-architect (data classification, retention)
  → solution-architect (compliant SBB selection)
```

## US Context

All agents are designed for US enterprise and federal contexts:
- **Framework alignment:** TOGAF 10, FEAF, BIZBOK, DAMA DMBOK 2, NIST CSF 2.0, NIST AI RMF
- **Regulatory coverage:** FISMA/FedRAMP, HIPAA, CMMC 2.0, PCI DSS v4, SOX, CCPA/CPRA
- **No UK-specific frameworks:** No GDS, TCoP, Green Book, Orange Book, G-Cloud, or UK GDPR dependencies
- **Wardley mapping:** Adapted for US commercial and federal strategic positioning

## Wardley Mapping Source Material

The `wardley-strategist` agent incorporates patterns from Simon Wardley's mapping methodology adapted for US enterprise use. The five-stage pipeline (value chain → map → doctrine → climate → gameplay) follows the analytical structure pioneered in the ArcKit project, with US regulatory and commercial context replacing UK government frameworks.

Maps render as OWM syntax compatible with https://create.wardleymaps.ai
