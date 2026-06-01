# Untool.ai — design-system brief (for Claude Design)

A map of the **canonical Untool.ai design system** so you can point Claude
Design at the right source during onboarding.

> **Correction / read this first.** The canonical design system is **not** in
> this hub repo. It lives in the **`frontend-core` spoke** as a set of formal
> **contracts** (W3C DTCG design tokens, theme, icons, per-component API
> declarations, and Figma Code Connect mappings). This hub checkout contains
> only API/health contracts — none of the design-system artifacts are vendored
> here — so this brief is an **index/pointer**, not the source of token values.
> The cockpit theme below is a secondary operator-console skin, not the product
> design system.

## Canonical source: `frontend-core/contract/`

These are documented in [`docs/contracts.md`](../../docs/contracts.md) (rows
FE-1…FE-8). This `contract/` subdirectory is small and focused — the ideal
Claude Design onboarding target (the docs warn against pointing it at a whole
monorepo).

| ID | Artifact | Path (in `frontend-core`) | Format | Role |
|---|---|---|---|---|
| FE-1 | **Design tokens** | `contract/design-tokens.json` | JSON-Schema, **W3C DTCG** | Colors, type, spacing — feeds every component + iOS mirror |
| FE-3 | **Theme contract** | `contract/theme.json` | JSON-Schema | Light / dark / **branded** variants; builds on FE-1 |
| FE-4 | **Icon set** | `contract/icons.json` | JSON | SVG sprite + name registry |
| FE-2 | **Component API registry** | `contract/components/<Component>.api.ts` | TypeScript declarations | One per shipped component → Figma Code Connect + consumers |
| FE-8 | **Figma Code Connect** | `.figma/*.figma.tsx` | Code Connect mappings | Component ↔ Figma node bindings |
| FE-7 | **iOS-shared models** | `contract/ios-shared.openapi.yaml` | OpenAPI | Shared type defs for web + SwiftUI |

### How to onboard Claude Design against it

1. **Best:** give Claude Design the `frontend-core` **GitHub URL**, scoped to
   the `contract/` subdirectory. It reads the DTCG `design-tokens.json` and
   `theme.json` natively and extracts the palette, type scale, and variants —
   the W3C DTCG format is exactly what it's built to ingest.
2. The `.figma/` Code Connect mappings + a Figma `.fig` give it the component ↔
   design bindings (Figma is ingest-only; Claude Design has no Figma export).
3. This brief + the cockpit appendix below are only a fallback seed if you can't
   point it at `frontend-core` directly.

> **To bake real token values into this brief:** this hub checkout can't read
> `frontend-core` (separate repo, out of scope here). Paste or vendor
> `frontend-core/contract/design-tokens.json` + `theme.json` and I'll regenerate
> this brief from the actual values.

---

## Appendix — operator cockpit skin (secondary, *not* the product DS)

Real tokens from `extensions/arcadedb-cockpit/public/styles.css` in this hub.
This is the ArcadeDB operator console's dark, neon-accent skin — useful only as
a small code sample of an internal tool's look, **not** the Untool.ai product
design system.

- **Surfaces:** `--bg #090c10`, `--panel #101820`, `--line #263744` (+ insets `#091017`, `#0d151c`, `#070b0f`)
- **Text:** `--text #eff7fb`, `--muted #8ea2ad`
- **Accents:** `--cyan #38e8ff`, `--lime #a9ff45`, `--magenta #ff4fd8`, `--red #ff5c70`
- **Type:** Inter; display weights 800–900; scale 26/20/19/13/12/11px
- **Shape/motion:** radius 8px (999px pills); 160ms ease transitions; soft shadow `0 18px 48px rgba(0,0,0,0.38)`
- **Shell:** CSS grid — 72px rail + fluid content; 76px topbar / body / 124px dock
