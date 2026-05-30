#!/usr/bin/env bash
# Sync each spoke repo's docs/ into the hub at docs/platform/<spoke>/ so the unified
# untool.ai docs site (built here) aggregates every layer. Each spoke stays the single
# source of truth for its own docs; this copies a fresh snapshot at build time.
#
# Auth: set SPOKE_SYNC_TOKEN (or GH_TOKEN) to a PAT with read access to the private
# spokes. Without a token it tries an anonymous clone (works only if public).
#
# Graceful: a spoke that can't be cloned or has no docs/ is skipped with a ::warning::,
# so the docs build never fails just because one layer is unavailable.
#
# Local dry-run against your existing clones (no network/token):
#   SPOKE_SRC_ROOT=/c/Dev ./scripts/sync-spoke-docs.sh
set -uo pipefail

OWNER="${SPOKE_OWNER:-nickpclarke}"
SPOKES="${SPOKES:-frontend-core backend-core middle-core}"
DEST_ROOT="docs/platform"
TOKEN="${SPOKE_SYNC_TOKEN:-${GH_TOKEN:-}}"
SRC_ROOT="${SPOKE_SRC_ROOT:-}"   # if set, copy from local clones instead of cloning

# Friendly section titles (awesome-pages reads a per-dir .pages we drop in).
title_for() {
  case "$1" in
    frontend-core) echo "Frontend Core (UI / BFF)";;
    backend-core)  echo "Backend Core (Knowledge Platform)";;
    middle-core)   echo "Middle Core (Agent Runtime)";;
    *)             echo "$1";;
  esac
}

synced=0
for s in $SPOKES; do
  dest="$DEST_ROOT/$s"
  rm -rf "$dest"; mkdir -p "$dest"
  srcdocs=""
  if [ -n "$SRC_ROOT" ] && [ -d "$SRC_ROOT/$s/docs" ]; then
    srcdocs="$SRC_ROOT/$s/docs"
  else
    tmp="$(mktemp -d)"
    url="https://github.com/$OWNER/$s.git"
    [ -n "$TOKEN" ] && url="https://x-access-token:${TOKEN}@github.com/$OWNER/$s.git"
    if git clone --depth 1 "$url" "$tmp" >/dev/null 2>&1 && [ -d "$tmp/docs" ]; then
      srcdocs="$tmp/docs"
    fi
  fi
  if [ -z "$srcdocs" ]; then
    echo "::warning::sync-spoke-docs: could not get docs/ for $s — skipping"
    rmdir "$dest" 2>/dev/null || true
    continue
  fi
  cp -r "$srcdocs/." "$dest/"
  # Give the layer a friendly nav title (don't clobber a .pages the spoke shipped).
  [ -f "$dest/.pages" ] || printf 'title: %s\n' "$(title_for "$s")" > "$dest/.pages"
  echo "synced: $s -> $dest"
  synced=$((synced + 1))
done

echo "sync-spoke-docs: $synced layer(s) synced into $DEST_ROOT/"
