# Icon library (full-colour brand marks)

Full-colour SVG logos for the self-model viewer, vendored from
[gilbarbara/logos](https://github.com/gilbarbara/logos) (CC0). They are **inlined as
data-URIs** at emit time (`tools/selfmodel/emit.py`) so the viewer stays offline and
PNG-export-safe. Logos render on a white chip (replacing the colour disc); the type colour
moves to the border ring. Brands with no CC0 mark fall back to a lettermark.

## Available now (33)

| Category | Icons |
|---|---|
| **Clouds** | `microsoftazure` · `googlecloud` · `aws` · `vercel` · `cloudflare` |
| **Databases / data** | `postgresql` · `redis` · `mongodb` · `neo4j` · `supabase` |
| **Messaging / infra** | `natsdotio` · `kafka` · `kubernetes` · `terraform` · `docker` |
| **AI / LLM** | `openai` · `anthropic` · `huggingface` · `mistral` · `meta` · `githubcopilot` |
| **Dev / tools** | `github` · `git` · `postman` · `apache` · `openapiinitiative` |
| **Languages / frameworks** | `python` · `rust` · `typescript` · `react` · `nextjs` · `fastapi` · `dotnet` |

Lettermark fallback (no CC0 logo yet): Cerebras, ArcadeDB, Gemini, Ollama, Cohere,
LangChain, DuckDB, Arrow — and any abstract node type.

## Architecture icons (official cloud service icons)

A second set lives in **`arch/`** — official **Azure architecture** service icons (from
[benc-uk/icon-collection](https://github.com/benc-uk/icon-collection), MIT): `azure-container`
(Container Instances/Apps), `azure-appservice`, `azure-keyvault`, `azure-acr`, `azure-postgres`.
The viewer's **icon-set** selector switches `brand logos ↔ architecture` live; a node with no
service icon falls back to its brand logo. Map via `ARCH_BY_ID` / `ARCH_BY_TYPE` in `emit.py`.
GCP / AWS / CNCF packs slot in the same way when we need them.

## How the mapping works

In `tools/selfmodel/emit.py`:

- **`ICON_BY_ID`** — pin a specific instance to a brand: `"org-anthropic": "anthropic"`,
  `"plat-postgres": "postgresql"`, `"army-copilot": "githubcopilot"`. Use `"@Label"` to force
  a lettermark (e.g. `"org-cerebras": "@Cerebras"`).
- **`ICON_BY_TYPE`** — fallback per node *type*: `"Contract": "openapiinitiative"`,
  `"PlatformContainer": "docker"`.
- Anything unmatched → a 2-letter lettermark from the node name.

## Adding an icon (the easy path)

```bash
# 1. drop the SVG (slug = filename, no extension)
curl -L "https://cdn.jsdelivr.net/gh/gilbarbara/logos/logos/<slug>.svg" \
  -o ontology/platform-self-model/viz/icons/<name>.svg
# 2. map it in emit.py  →  ICON_BY_ID["plat-foo"] = "<name>"   (or ICON_BY_TYPE)
# 3. regenerate
python tools/selfmodel/emit.py
```

That's it — the emitter inlines it automatically. Same path applies when the **universal
adapters** register a new connector/LLM partner: add the brand SVG + one map line and every
node of that kind picks up the logo.
