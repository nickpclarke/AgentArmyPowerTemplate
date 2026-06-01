# Claude Design ↔ AgentArmy — connection notes

Findings from evaluating whether (and how) this fleet connects to **Claude
Design** (Anthropic Labs product, research preview, powered by Opus 4.7;
launched 2026-04-17; available to Pro / Max / Team / Enterprise).

## Can this Claude Code session connect directly to Claude Design?

**No direct programmatic connection.** Claude Design exposes no MCP server or
API; there is no Claude Design tool in this session, and Anthropic ships no
programmable surface for it. The integration is **document/file exchange**, not
a live socket — and the primary automated flow runs Claude Design → Claude
Code, not the reverse.

## The three real bridges

1. **Repo → Claude Design (import / onboarding).** Point Claude Design at a
   GitHub repo URL, drag in a local code folder, or upload a Figma `.fig` /
   documents (DOCX, PPTX, XLSX, PDF) / assets. It extracts colors, typography,
   components, and spacing into a reusable design system. *Caveat:* large repos
   lag — link a focused subdirectory, not the monorepo. (See this package's
   `README.md` for curated entry points.)

2. **Claude Design → Claude Code (handoff).** When a design is ready to build,
   Claude Design emits a **proprietary handoff bundle** — component structure as
   a machine-readable spec, the design tokens used on the canvas, the layout
   hierarchy, and referenced assets. The format is deliberately not a JSON
   design-token standard; it's tuned for two models from the same lab. You
   generate it in Claude Design and pass it to Claude Code; it can't be authored
   by hand.

3. **Figma.** Claude Design ingests Figma `.fig` files on the way *in* (parsed
   locally in-browser, never uploaded). It has **no Figma export** — a
   round-trip back to Figma requires a third party (e.g. Anima) or the
   read-only Figma plugin for Claude Code.

## Export surfaces (out of Claude Design)

Internal org URL · folder · Canva · PDF · PPTX · standalone HTML. No Figma, no
live API.

## Implication for AgentArmy

- The hub repo is orchestration/templates with no product UI — a poor import
  target. The product design system lives in **`frontend-core`**; onboard
  Claude Design against that spoke.
- This `design/claude-design-import/` package is the curated, low-noise bundle
  to feed Claude Design until/unless we wire onboarding directly at the
  `frontend-core` styling subtree.

## Sources

- Anthropic — Introducing Claude Design by Anthropic Labs
- The New Stack — Anthropic launches Claude Design, a Figma and Canva rival
- Claude Help Center — Set up your design system in Claude Design
- Claude Help Center — Get started with Claude Design
- claudefa.st — Claude Design to Claude Code handoff mechanics
- Figma Blog — From Claude Code to Figma (read-only plugin direction)
