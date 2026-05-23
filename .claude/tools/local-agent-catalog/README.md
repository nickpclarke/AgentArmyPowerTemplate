# local-agent-catalog

Bash functions for agent discovery and routing decisions. Used by agents when deciding which subagent to invoke.

**Not a user-facing tool.** This is for agent decision-making during subagent routing.

## Setup

Source the config in your script:

```bash
source .claude/tools/local-agent-catalog/config.sh
```

## Functions

### Search & Discovery

**`local_agent_catalog_search <query>`**
- Case-insensitive substring match on name, description, category, or tier
- Returns: `agent_name|description|category|tier`
- Exit code: 0 if found, 1 if not

Example:
```bash
local_agent_catalog_search "react" | while IFS='|' read name desc cat tier; do
  echo "$name — $desc (in $cat/$tier)"
done
```

**`local_agent_catalog_list_category <category>`**
- List all agents in a category
- Returns: `agent_name|description|tier`

Example:
```bash
local_agent_catalog_list_category "02-language-specialists"
```

**`local_agent_catalog_list_categories`**
- List all categories with agent counts
- Returns: `category_code|structure_type|agent_count`

### Agent Details

**`local_agent_catalog_get_agent <agent_name>`**
- Full agent definition (frontmatter + body)
- Returns: raw markdown

Example:
```bash
local_agent_catalog_get_agent "react-specialist" | head -20
```

**`local_agent_catalog_get_metadata <agent_name>`**
- Structured metadata (name, description, category, tier, tools, model)
- Returns: `name|description|category|tier|tools|model`

Example:
```bash
local_agent_catalog_get_metadata "python-pro" | tr '|' '\n'
```

### Routing & Decision Support

**`local_agent_catalog_get_routing_guidance <query>`**
- Get routing rules from TAXONOMY.md (category 02 language specialists)
- Searches for tie-breaker examples matching the query
- Returns: relevant rules or "not found" message

Example:
```bash
local_agent_catalog_get_routing_guidance "language vs framework"
```

**`local_agent_catalog_find_overlaps <agent_name>`**
- Find agents in the same tier (potential overlaps)
- Returns: `agent_name|description`

Example:
```bash
local_agent_catalog_find_overlaps "fastapi-developer"
# Output: react-specialist, angular-architect, etc. (other framework agents)
```

**`local_agent_catalog_exists <agent_name>`**
- Check if an agent exists (returns 0/1)

Example:
```bash
if local_agent_catalog_exists "rust-engineer"; then
  echo "Found it"
fi
```

## Use Cases

### 1. Find the right agent for a task

```bash
# Search for agents matching the task
results=$(local_agent_catalog_search "optimize slow database queries")

# Multiple candidates? Check overlaps and get routing guidance
if [ $(echo "$results" | wc -l) -gt 1 ]; then
  local_agent_catalog_get_routing_guidance "database optimization"
fi
```

### 2. Route to the most specific agent

```bash
# When you have a task about React performance
if local_agent_catalog_search "react optimization" | grep -q "react-specialist"; then
  # Prefer react-specialist over performance-engineer
  subagent_type="react-specialist"
fi
```

### 3. Escalate when ambiguous

```bash
# If multiple agents could handle this, ask agent-distinctiveness-advocate
candidates=$(local_agent_catalog_search "CI/CD pipeline")
if [ $(echo "$candidates" | wc -l) -gt 1 ]; then
  # Call agent-distinctiveness-advocate to pick the best one
  Agent(subagent_type: "agent-distinctiveness-advocate")
fi
```

### 4. Build routing logic

```bash
# Example: Route based on tier (language vs framework)
task_type="$1"

if echo "$task_type" | grep -qi "language\|idiom\|type system"; then
  # Search language-tier agents
  local_agent_catalog_search "python" | grep "languages" | head -1
elif echo "$task_type" | grep -qi "framework\|convention"; then
  # Search framework-tier agents
  local_agent_catalog_search "python" | grep "frameworks" | head -1
fi
```

## Integration with MECE Governance

The catalog returns **tier information** (languages/, frameworks/, platforms/) so you can:
- Check if an agent is in the right tier for the task
- Detect when multiple tiers might apply (escalate to agent-distinctiveness-advocate)
- Reference TAXONOMY.md for explicit routing rules

## Data Format

All functions return pipe-delimited data for easy parsing:

```bash
# Parse a search result
IFS='|' read agent_name description category tier <<< "python-pro|Language idioms and async patterns|02-language-specialists|languages"

# Parse metadata
IFS='|' read name desc cat tier tools model < <(local_agent_catalog_get_metadata "fastapi-developer")
```

## Performance Notes

- Functions use `find` + `grep` (fast for 170 agents)
- No external API calls or caching needed
- Runs locally, no network dependency

## Debugging

Check that config.sh was sourced:

```bash
type local_agent_catalog_search  # Should show "is a function"
```

Verify paths:

```bash
echo "$LOCAL_AGENT_CATALOG_AGENTS_DIR"
echo "$LOCAL_AGENT_CATALOG_TAXONOMY"
```
