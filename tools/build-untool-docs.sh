#!/usr/bin/env bash
# Assemble the untool.ai PLATFORM docs into a curated tree (untool-docs-src/) and build the
# separate untool site (mkdocs.untool.yml -> site-untool/). Only platform content is staged,
# so the AgentArmy army/template/agent-glossary pages never appear on docs.untool.ai.
#
# Sources (all from this repo's docs/, plus spoke docs synced in):
#   docs/untool/index.md             -> home (index.md)
#   docs/untool/ontology-and-use-cases.md
#   docs/untool-platform.md          -> platform-architecture.md
#   docs/platform/<spoke>/           -> synced spoke platform docs (Platform Layers)
#   docs/decisions/ARC-ADR-*.md      -> Architecture Decisions
#   docs/stylesheets/untool.css      -> brand
#
# Spoke sync uses scripts/sync-spoke-docs.sh (graceful; honours SPOKE_SYNC_TOKEN/SPOKE_SRC_ROOT).
set -uo pipefail
cd "$(dirname "$0")/.."

SRC="untool-docs-src"
rm -rf "$SRC" site-untool
mkdir -p "$SRC/stylesheets" "$SRC/decisions"

# --- Home + top-level platform pages -------------------------------------------------------
cp docs/untool/index.md                    "$SRC/index.md"
cp docs/untool/ontology-and-use-cases.md   "$SRC/ontology-and-use-cases.md"
cp docs/untool-platform.md                 "$SRC/platform-architecture.md"
cp docs/stylesheets/untool.css             "$SRC/stylesheets/untool.css"

# Brand wordmark JS + footer-only legal pages (hidden from nav via legal/.pages).
mkdir -p "$SRC/javascripts" "$SRC/legal"
cp docs/untool/javascripts/wordmark.js     "$SRC/javascripts/wordmark.js"
cp docs/untool/legal/*.md                  "$SRC/legal/"
cp docs/untool/legal/.pages                "$SRC/legal/.pages"

# Top-level order/titles (awesome-pages).
cat > "$SRC/.pages" <<'PAGES'
nav:
  - index.md
  - platform-architecture.md
  - ontology-and-use-cases.md
  - platform
  - decisions
PAGES

# --- Architecture Decisions (all platform ADRs) --------------------------------------------
cp docs/decisions/ARC-ADR-*.md "$SRC/decisions/" 2>/dev/null || true
[ -f docs/decisions/ADR-BACKLOG.md ] && cp docs/decisions/ADR-BACKLOG.md "$SRC/decisions/"
printf 'title: Architecture Decisions\n' > "$SRC/decisions/.pages"

# --- Platform Layers (synced spoke docs) ---------------------------------------------------
# Reuse the spoke sync (writes docs/platform/<spoke>/), then copy the result into the tree.
mkdir -p "$SRC/platform"
cp docs/platform/index.md "$SRC/platform/index.md" 2>/dev/null || true
cp docs/platform/.pages   "$SRC/platform/.pages"   2>/dev/null || true
bash scripts/sync-spoke-docs.sh || echo "::warning::spoke sync had issues (continuing)"
for s in frontend-core backend-core middle-core; do
  [ -d "docs/platform/$s" ] && cp -r "docs/platform/$s" "$SRC/platform/$s"
done

echo "assembled $SRC/ :"
find "$SRC" -maxdepth 2 -type d | sed 's/^/  /'

# --- Build ---------------------------------------------------------------------------------
mkdocs build -f mkdocs.untool.yml
echo "built site-untool/ ($(find site-untool -name '*.html' 2>/dev/null | wc -l) pages)"
