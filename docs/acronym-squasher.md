# Acronym Squasher

A platform capability that sweeps the docs for **undefined acronyms** — the little
mines of dissonance that slow every reader and every onboarding agent — and turns
them into hover-to-understand tooltips. Detect → Enforce → Unpack.

The single source of truth is **[glossary.md](glossary.md)**. Everything else is
generated or checked against it.

## The three layers

| Layer | What it does | Where |
|---|---|---|
| **Detect** | scans every `docs/**/*.md`, finds acronyms / products / fleet modules used but **not** defined, ranked by frequency | `node tools/acronyms.mjs` |
| **Unpack** | generates `*[ACR]: expansion` lines from the glossary so MkDocs renders an `<abbr>` hover tooltip for every acronym, site-wide | `node tools/acronyms.mjs abbr` → `docs/includes/abbreviations.md` |
| **Enforce** | CI fails any PR that introduces an undefined acronym, and fails if the generated tooltips drift from the glossary | `.github/workflows/acronym-coverage.yml` |

## Usage

```bash
node tools/acronyms.mjs                 # coverage report + ranked gaps (acronyms / products / modules)
node tools/acronyms.mjs find JWT        # look up one acronym's definition
node tools/acronyms.mjs --missing       # full undefined list, one per line
node tools/acronyms.mjs --acronyms --ci # exit 1 if any *acronym* is undefined (CI gate)
node tools/acronyms.mjs abbr            # regenerate docs/includes/abbreviations.md from the glossary
node tools/acronyms.mjs --root          # scan the whole repo, not just docs/
```

## Adding a term

1. Add it to **[glossary.md](glossary.md)** — either a thematic section
   (`**TERM** — definition.`) or the A–Z **Acronym Index**.
2. Run `node tools/acronyms.mjs abbr` and commit the regenerated
   `docs/includes/abbreviations.md`.
3. That's it — the tooltip renders everywhere, and the CI gate goes green.

## How detection works

Three patterns, because three term-classes have different shapes: all-caps
acronyms (`HMAC`), CamelCase products (`ArcadeDB`), and hyphenated fleet modules
(`event-bridge`). Noise is filtered out — config keys (`AZURE_*`), SQL/HTTP verbs,
ID stems (`F4`, `RT5`), and project feature-IDs (`MCR-F*`) are not acronyms and are
excluded. Only the **acronym** bucket is CI-gated; product and module proper-nouns
are reported but not required to be defined.

> **Why it matters:** an undefined acronym is comprehension debt — every reader pays
> interest. Defining acronyms *with* acronyms just plants new mines (defining `HTTPS`
> introduced `TLS`; `R2RML` introduced `RDB`), which is exactly why the gate is
> recursive: the sweep isn't done until the definitions themselves are clean.
