# ARC-ADR-008: Adopt shadcn/ui as the frontend-core design system

| Field | Value |
|---|---|
| **ID** | ARC-ADR-008 |
| **Status** | Accepted |
| **Date** | 2026-05-29 |
| **Deciders** | Repo owner (nick) — Option C (hybrid) |
| **Supersedes** | — |
| **Superseded by** | — |
| **Tags** | frontend-core, design-system, shadcn, tailwind, nextjs, react19, a11y |

> **ADR-008 numbering note.** Three draft PRs each authored a *different* `ARC-ADR-008`
> (#41 shadcn · #72 `@figma/code-connect` lite · #78 in-house "untool" DS). **This file is the
> single canonical 008.** The other two are withdrawn — see _Supersedes the drafts_ below. The hub
> (`nickpclarke/AgentArmy`) owns the canonical `ARC-ADR-###` registry; confirm `008` upstream.

## Context

frontend-core (Next.js App Router + React 19 + CopilotKit, per ADR-007) hand-rolls every UI
primitive over a CSS-variable token layer (`app/theme.css`). That does not scale: it duplicates
accessibility plumbing and invites visual drift. A design-system direction was needed.

Three candidate directions were explored as draft PRs:
- **#41** — bake-off spike: shadcn/ui vs MUI, measured. shadcn was ~5× lighter (~14 KB vs ~75 KB
  all-in), RSC-native, vendored in-repo, CSS-var theming continuous with `theme.css`.
- **#78** — a bespoke in-house "untool.ai" design system (brand + data-viz primitives + a
  homegrown Figma bridge).
- **#72** — official `@figma/code-connect` lite pilot.

See `docs/design-system/DECISION-shadcn-vs-inhouse.md` for the full comparison.

## Decision

**Option C (hybrid): shadcn/ui as the base, with selective in-house extensions on top.**

- **Base — shadcn/ui** (Radix + Tailwind v4, vendored in `components/ui/`) for all commodity
  interactive chrome (button, dialog, input, table, card, badge, …). Rationale (decider's words):
  an **obvious common visual language that other systems use**; the **copy-in / fork model** lets
  us own components in-repo and even **contribute upstream**; extend via **shadcn's own methodology**
  (`npx shadcn@latest add <name>`).
- **Extension — bespoke data-viz primitives** that shadcn does not and will not ship
  (Sparkline, SmallMultiples, Numeric, Annotation), rebuilt on the shadcn token layer. These are
  the differentiated ~20% the analytics/cockpit product actually needs.
- **Brand / visual identity — deferred to a dedicated design pass** (Claude design), not hand-built
  here. The earlier in-house *visual* attempt (#78) and its messy v0 Figma were rejected on
  execution quality; only the *functional* data-viz primitives from that direction are salvaged.

> Trade-off accepted: shadcn (Tailwind) and any retained CSS-Module primitives coexist during
> migration; the token layers (`app/theme.css` ↔ shadcn tokens) converge to one source of truth.

## Consequences

**Adopted now (this PR):**
- `components/ui/` — vendored shadcn primitives: button, badge, card, dialog, input, table.
- `lib/utils.ts` (`cn`), `components.json` (so `npx shadcn add` works), `postcss.config.mjs`.
- `app/tailwind.css` — Tailwind v4 + stock **neutral** shadcn tokens, AA-tuned, dark wired to the
  existing `[data-theme="dark"]` switch.
- `/design-system` — living primitive gallery.
- Deps: tailwindcss v4, @tailwindcss/postcss, tw-animate-css, @radix-ui/react-{dialog,slot},
  class-variance-authority, clsx, tailwind-merge, lucide-react. `.npmrc` sets
  `legacy-peer-deps=true` (React 19 is ahead of Radix 1.0.x peer ranges).

**Deliberate constraint — Preflight off (incremental adoption):** `app/tailwind.css` imports only
Tailwind's `theme` + `utilities` layers, **not** Preflight, so the existing CSS-Module screens are
not visually reset. Flip to the single `@import "tailwindcss";` once the app is fully migrated.

**Follow-ups (separate PRs):** migrate existing screens (search/cockpit/ingest/sources) onto the
primitives; reconcile `app/theme.css` tokens with the shadcn token layer toward one source of
truth; move the `globals.css` unlayered `a {}` into `@layer base` before enabling Preflight.

### Supersedes the drafts
- **#41 (shadcn spike)** — graduated here; the `design-lab` benchmark routes are not brought over.
- **#78 (in-house untool DS)** — rejected; its bespoke primitives/brand/Figma bridge are dropped.
- **#72 (`@figma/code-connect` lite)** + **#65/#66** — withdrawn under this decision.

(PR cleanup — closing #41/#65/#66/#72/#78 — is left to the repo owner.)
