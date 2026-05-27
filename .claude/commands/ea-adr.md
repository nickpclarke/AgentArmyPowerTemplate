# Architecture Decision Record

Create or review an Architecture Decision Record (ADR) in MADR v4.0 format.

## Usage

```
/ea-adr [decision title or topic]
```

Examples:

```
/ea-adr API gateway technology selection
/ea-adr authentication strategy for B2B customers
/ea-adr data replication approach for disaster recovery
/ea-adr review ARC-ADR-021 — should we extract llm-gateway to its own repo?
```

## What to do (explicit dispatch)

Pick **one** sub-agent based on what the user actually asked for, then invoke
it via the **Agent** tool — do not draft the ADR yourself:

| User intent | Sub-agent | Why |
|---|---|---|
| Draft a NEW ADR for a decision that's not yet recorded | `togaf-adm-advisor` | Knows MADR v4.0 structure cold, anchors the doc in the right TOGAF ADM phase, and pulls in the correct artifact templates (Statement of Architecture Work, Architecture Definition Document, etc.). |
| Review an EXISTING ADR, propose changes, or evaluate trade-offs against decision drivers | `architect-reviewer` | Trained on macro-level architectural patterns + technology choices and gives a structured second-opinion read against the existing ADRs and decision drivers. |
| Orchestrate a multi-ADR program (multiple cross-cutting decisions in flight, full ADM phase coordination) | `enterprise-architect` | Senior orchestrator — only when scope clearly exceeds a single ADR. |

When the user's phrasing is ambiguous between "new" and "review," ask one
clarifying question before dispatching. Don't guess and dispatch to the
wrong specialist.

### Prompt to pass to the sub-agent

Hand the sub-agent enough to work independently:

- The full decision title/topic from `/ea-adr [...]`
- File path the ADR should land at: `docs/decisions/ARC-ADR-[NNN]-[kebab-title].md`
  where `[NNN]` is the next available number under `docs/decisions/`
- Status to start in: **Proposed** (unless the user said otherwise)
- Repo conventions: link related ADRs by file name, MADR v4.0 sections required
  (Context, Decision Drivers, Considered Options, Decision Outcome, Pros and
  Cons of Options, Confirmation, More Information)

### Required ADR sections (MADR v4.0)

The sub-agent must produce all of these:

- **Context and Problem Statement** — why this decision is needed now
- **Decision Drivers** — architecture principles, requirements, constraints
- **Considered Options** — 3–4 alternatives evaluated (not 1; not 10)
- **Decision Outcome** — chosen option + positive and negative consequences
- **Pros and Cons of Options** — structured analysis per option
- **Confirmation** — how to verify the decision is implemented correctly
- **More Information** — related ADRs, follow-up decisions needed

## Document convention

ADRs are stored as:

```
docs/decisions/ARC-ADR-[NNN]-[kebab-title].md
```

Status flow: **Proposed → Accepted → Deprecated → Superseded**

## Why ADRs

ADRs are the primary mechanism for recording architectural decisions in the
Architecture Repository. Every significant architectural choice should have
one. They are the institutional memory that survives team turnover and the
ground truth that future ADRs build on.

## When NOT to invoke /ea-adr

- Pure code-review questions → use `code-reviewer` directly
- Cross-cutting solution architecture for a single feature → `solution-architect`
- Strategic positioning / value-chain mapping → `/wardley`
- Business-capability investment planning → `/capability-map`
- A discovered fork in code requiring a human/AI app decision → `hitl-coordinator`
  (creates a Decision Artifact issue on the board, distinct from a long-form ADR)
