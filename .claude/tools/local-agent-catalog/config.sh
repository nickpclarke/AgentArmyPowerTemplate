#!/usr/bin/env bash
# local-agent-catalog configuration
# bash functions for agent discovery and routing decisions
# sourced by agents when they need to route work to other agents

set -euo pipefail

# --- PATHS ---
readonly LOCAL_AGENT_CATALOG_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly LOCAL_AGENT_CATALOG_AGENTS_DIR="${LOCAL_AGENT_CATALOG_REPO_ROOT}/agents/categories"
readonly LOCAL_AGENT_CATALOG_TAXONOMY="${LOCAL_AGENT_CATALOG_REPO_ROOT}/../.claude/agents/categories/02-language-specialists/TAXONOMY.md"

export LOCAL_AGENT_CATALOG_REPO_ROOT LOCAL_AGENT_CATALOG_AGENTS_DIR LOCAL_AGENT_CATALOG_TAXONOMY

# --- SEARCH & DISCOVERY ---

# Search agents by name, description, or category (case-insensitive substring)
# Returns: agent_name|description|category|tier
local_agent_catalog_search() {
  local query="$1"
  local found=0

  # Search through all agent .md files
  while IFS= read -r agent_file; do
    [ -z "$agent_file" ] && continue

    local agent_name=$(basename "$agent_file" .md)
    local agent_dir=$(dirname "$agent_file")
    local category=$(basename "$(dirname "$agent_dir")")
    local tier=$(basename "$agent_dir")

    # Extract description from frontmatter
    local description=$(sed -n 's/^description: "\(.*\)"$/\1/p' "$agent_file" | head -1)

    # Case-insensitive match on name, description, or category/tier
    if echo "$agent_name" | grep -qi "$query" || \
       echo "$description" | grep -qi "$query" || \
       echo "$category" | grep -qi "$query" || \
       echo "$tier" | grep -qi "$query"; then
      echo "$agent_name|$description|$category|$tier"
      found=1
    fi
  done < <(find "${LOCAL_AGENT_CATALOG_AGENTS_DIR}" -name "*.md" -type f | sort)

  return $((found == 0))
}

# Get all agents in a specific category
# Returns: agent_name|description|tier
local_agent_catalog_list_category() {
  local category="$1"
  local category_dir="${LOCAL_AGENT_CATALOG_AGENTS_DIR}/${category}"

  if [ ! -d "$category_dir" ]; then
    echo "ERROR: Category not found: $category" >&2
    return 1
  fi

  while IFS= read -r agent_file; do
    [ -z "$agent_file" ] && continue
    local agent_name=$(basename "$agent_file" .md)
    local tier=$(basename "$(dirname "$agent_file")")
    local description=$(sed -n 's/^description: "\(.*\)"$/\1/p' "$agent_file" | head -1)
    echo "$agent_name|$description|$tier"
  done < <(find "$category_dir" -name "*.md" -type f | sort)
}

# List all categories with agent counts
# Returns: category_code|category_name|agent_count|tier (if applicable)
local_agent_catalog_list_categories() {
  while IFS= read -r cat_dir; do
    [ -z "$cat_dir" ] && continue
    [ "$(basename "$cat_dir")" = "." ] && continue

    local cat_name=$(basename "$cat_dir")
    local agent_count=$(find "$cat_dir" -name "*.md" -type f 2>/dev/null | wc -l)

    # Check if this has tiers (like category 02)
    if [ -d "$cat_dir/languages" ] || [ -d "$cat_dir/frameworks" ] || [ -d "$cat_dir/platforms" ]; then
      echo "$cat_name|with-tiers|$agent_count"
    else
      echo "$cat_name|flat|$agent_count"
    fi
  done < <(find "${LOCAL_AGENT_CATALOG_AGENTS_DIR}" -maxdepth 1 -type d ! -name "." | sort)
}

# --- AGENT DETAILS ---

# Get full agent definition (name, description, tools, model)
# Returns: frontmatter + body
local_agent_catalog_get_agent() {
  local agent_name="$1"
  local agent_file=$(find "${LOCAL_AGENT_CATALOG_AGENTS_DIR}" -name "${agent_name}.md" -type f)

  if [ -z "$agent_file" ]; then
    echo "ERROR: Agent not found: $agent_name" >&2
    return 1
  fi

  cat "$agent_file"
}

# Get agent metadata (name, description, category, tier, tools, model)
# Returns: name|description|category|tier|tools|model
local_agent_catalog_get_metadata() {
  local agent_name="$1"
  local agent_file=$(find "${LOCAL_AGENT_CATALOG_AGENTS_DIR}" -name "${agent_name}.md" -type f)

  if [ -z "$agent_file" ]; then
    echo "ERROR: Agent not found: $agent_name" >&2
    return 1
  fi

  local description=$(sed -n 's/^description: "\(.*\)"$/\1/p' "$agent_file" | head -1)
  local tools=$(sed -n 's/^tools: \[\(.*\)\]$/\1/p' "$agent_file" | head -1)
  local model=$(sed -n 's/^model: \(.*\)$/\1/p' "$agent_file" | head -1)
  local category=$(basename "$(dirname "$(dirname "$agent_file")")")
  local tier=$(basename "$(dirname "$agent_file")")

  echo "$agent_name|$description|$category|$tier|$tools|$model"
}

# --- ROUTING & DECISION SUPPORT ---

# Get routing guidance for a task from TAXONOMY.md (category 02 only)
# Returns: relevant routing rules and tie-breaker examples
local_agent_catalog_get_routing_guidance() {
  local query="$1"

  if [ ! -f "$LOCAL_AGENT_CATALOG_TAXONOMY" ]; then
    echo "ERROR: TAXONOMY.md not found" >&2
    return 1
  fi

  # Search TAXONOMY.md for tie-breaker examples matching the query
  sed -n '/## Tie-Breaker Examples/,/^## /p' "$LOCAL_AGENT_CATALOG_TAXONOMY" | \
    grep -i -A 3 "$query" || echo "No specific routing rules found for: $query. See TAXONOMY.md for tier definitions."
}

# Find agents that might overlap with a given agent (same category/tier)
# Returns: agent_name|description
local_agent_catalog_find_overlaps() {
  local agent_name="$1"
  local agent_file=$(find "${LOCAL_AGENT_CATALOG_AGENTS_DIR}" -name "${agent_name}.md" -type f)

  if [ -z "$agent_file" ]; then
    echo "ERROR: Agent not found: $agent_name" >&2
    return 1
  fi

  local agent_dir=$(dirname "$agent_file")

  # Find all agents in the same tier
  while IFS= read -r other_file; do
    [ -z "$other_file" ] && continue
    [ "$other_file" = "$agent_file" ] && continue

    local other_name=$(basename "$other_file" .md)
    local description=$(sed -n 's/^description: "\(.*\)"$/\1/p' "$other_file" | head -1)
    echo "$other_name|$description"
  done < <(find "$agent_dir" -name "*.md" -type f | sort)
}

# --- HELPERS ---

# Format agent info as a table row (for human-readable output)
local_agent_catalog_format_row() {
  local agent_name="$1"
  local description="$2"
  local category="$3"
  local tier="$4"

  printf "| %-30s | %-50s | %-20s |\n" "$agent_name" "${description:0:47}..." "$category/$tier"
}

# Validate an agent exists
local_agent_catalog_exists() {
  local agent_name="$1"
  [ -f "$(find "${LOCAL_AGENT_CATALOG_AGENTS_DIR}" -name "${agent_name}.md" -type f 2>/dev/null)" ]
}
