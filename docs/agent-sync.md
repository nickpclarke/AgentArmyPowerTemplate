# Agent Synchronization

AgentArmy maintains a **single source of truth** for AI agent definitions (`.claude/agents/categories/`) and automatically synchronizes them across multiple platforms: **Codex**, **Antigravity CLI**, and **GitHub apps** (Copilot, Gemini).

## Overview

```
.claude/agents/categories/ (172 agents — source of truth)
    ↓
    ├─→ Codex (.codex/agents/ — 169 TOML files)
    ├─→ Antigravity CLI (.agents/plugins/ — 11 plugin groups, 167 agents)
    └─→ GitHub automation workflows (Copilot + Gemini routing)
```

**Key principle:** Edit once in `.claude/agents/categories/*.md`, and the other platforms automatically stay in sync.

---

## Quick Start

### Audit Agent Sync Status

```bash
python scripts/orchestrate_agent_sync.py --audit
```

Output shows sync ratios, MCP server count, hook status, and script availability:

```
📌 SOURCE OF TRUTH
   Agents: 172  Status: ✅ OK

📌 CODEX SYNC
   Agents: 169  Sync ratio: 98.3%  Status: ✅ OK

📌 ANTIGRAVITY SYNC
   Plugins: 11  Agents: 167  Sync ratio: 97.1%  Status: ✅ OK

📌 MCP SERVERS
   Configured: 4  Status: ✅ Configured

📌 CODEX HOOKS
   SessionStart hook: ✅ Yes  Status: ✅ Active
```

### Full Synchronization

Run all syncs at once:

```bash
python scripts/orchestrate_agent_sync.py
```

---

## Synchronization Mechanisms

### 1. Claude Code → Codex

**Tool:** `scripts/sync_agents_to_codex.py`

**When:** Automatically on Codex `SessionStart` hook (`.codex/hooks.json`)

**What it does:**
- Reads Claude agent definitions from `.claude/agents/categories/*.md`
- Extracts YAML frontmatter (`name`, `description`, `tools`, `model`)
- Converts instructions (everything after `---`) to TOML
- Writes to `.codex/agents/*.toml` (one file per agent)
- Cleans stale files on each run

**Manual trigger:**
```bash
python scripts/sync_agents_to_codex.py
```

**Example output:**
```toml
# .codex/agents/security-architect.toml
name = "security-architect"
description = "Use this agent for enterprise security architecture..."
developer_instructions = """
You are a senior security architect with expertise...
"""
```

**Hook configuration** (`.codex/hooks.json`):
```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python scripts/sync_agents_to_codex.py",
        "timeout": 60,
        "statusMessage": "Syncing Claude agents to Codex agents..."
      }
    ]
  }
}
```

---

### 2. Claude Code → Antigravity CLI

**Tool:** `scripts/sync_agents_to_antigravity.py`

**When:** Manual (or integrate into CI/CD)

**What it does:**
- Reads Claude agent definitions and plugin metadata (`.claude-plugin/plugin.json`)
- Copies agent `.md` files into Antigravity plugin structure
- Supports workspace-local (default) and global (`--global`) destinations
- Organizes agents into 11 plugin groups (language specialists, infrastructure, data/AI, etc.)

**Workspace-local sync:**
```bash
python scripts/sync_agents_to_antigravity.py
# Output: .agents/plugins/
```

**Global user sync:**
```bash
python scripts/sync_agents_to_antigravity.py --global
# Output: ~/.gemini/antigravity-cli/plugins/
```

**Plugin structure** (`.agents/plugins/`):
```
voltagent-lang/
├── python-pro.md
├── typescript-pro.md
├── golang-pro.md
└── plugin.json

voltagent-infra/
├── aws-infra-engineer.md
├── gcp-infra-engineer.md
└── plugin.json

agentarmy-enterprise-architecture/
├── security-architect.md
├── enterprise-architect.md
└── plugin.json
```

---

### 3. MCP Servers (Remote Tools)

**Config file:** `.codex/config.toml`

**Supported servers:**
- GCP BigQuery (remote via HTTP)
- GCP Cloud Storage (remote via HTTP)
- GCP Cloud Observability (remote via HTTP)
- GCP Vertex AI Agent Registry (remote API)

**Configuration:**
```toml
[mcp_servers.gcp-bigquery]
url = "${GCP_BIGQUERY_MCP_URL}"
bearer_token_env_var = "GCP_BEARER_TOKEN"

[mcp_servers.gcp-storage]
url = "${GCP_STORAGE_MCP_URL}"
bearer_token_env_var = "GCP_BEARER_TOKEN"

[mcp_servers.gcp-observability]
url = "${GCP_OBSERVABILITY_MCP_URL}"
bearer_token_env_var = "GCP_BEARER_TOKEN"

[mcp_servers.gcp-vertex-agents]
url = "https://${GCP_REGION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT_ID}/locations/${GCP_REGION}/agents/gcp-mcp-server:callMcp"
bearer_token_env_var = "GCP_BEARER_TOKEN"
```

**Setup:**
1. Set environment variables in your shell or CI/CD:
   - `GCP_BEARER_TOKEN` — GCP service account token
   - `GCP_BIGQUERY_MCP_URL` — HTTP endpoint for BigQuery MCP
   - `GCP_STORAGE_MCP_URL` — HTTP endpoint for Storage MCP
   - `GCP_OBSERVABILITY_MCP_URL` — HTTP endpoint for Observability MCP
   - `GCP_PROJECT_ID` — Your GCP project ID
   - `GCP_REGION` — GCP region (e.g., `us-central1`)

2. Codex and Antigravity CLI automatically load `.codex/config.toml` at startup.

---

## Unified Orchestrator

**Tool:** `scripts/orchestrate_agent_sync.py`

Single entry point for all sync operations. Replaces the need to run individual scripts.

### Usage

```bash
# Full sync: Codex + Antigravity (workspace-local)
python scripts/orchestrate_agent_sync.py

# Audit only (read-only, no changes)
python scripts/orchestrate_agent_sync.py --audit

# Sync Codex only
python scripts/orchestrate_agent_sync.py --codex

# Sync Antigravity only (workspace-local)
python scripts/orchestrate_agent_sync.py --antigravity

# Sync Antigravity globally
python scripts/orchestrate_agent_sync.py --antigravity --global
```

### Output Example

```
🚀 STARTING FULL AGENT SYNC
============================================================
🔄 Syncing Claude agents → Codex...
   ✅ Synced 172 agents to .codex/agents/
🔄 Syncing Claude agents → Antigravity CLI (workspace (.agents/plugins))...
   ✅ Synced 11 plugins with 167 total agents

📊 AUDIT REPORT
============================================================

📌 SOURCE OF TRUTH
   Agents: 172  Status: ✅ OK

📌 CODEX SYNC
   Agents: 169  Sync ratio: 98.3%  Status: ✅ OK

📌 ANTIGRAVITY SYNC
   Plugins: 11  Agents: 167  Sync ratio: 97.1%  Status: ✅ OK

📌 MCP SERVERS
   Configured: 4  Status: ✅ Configured

📌 CODEX HOOKS
   SessionStart hook: ✅ Yes  Status: ✅ Active

📌 SYNC SCRIPTS
   sync_agents_to_codex.py: ✅
   sync_agents_to_antigravity.py: ✅
   Status: ✅ All present

============================================================
✅ ALL SYNCS SUCCESSFUL
```

---

## Integration with CI/CD

### Codex SessionStart Hook

Already configured in `.codex/hooks.json`. Codex will auto-run `sync_agents_to_codex.py` at the start of every session.

### GitHub Actions (Optional)

Add to a CI workflow to auto-sync agents on main branch updates:

```yaml
name: Sync agents on main update

on:
  push:
    branches:
      - main
    paths:
      - '.claude/agents/categories/**'
      - 'scripts/sync_*.py'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: python scripts/orchestrate_agent_sync.py
      - run: git add .codex/agents/ .agents/plugins/
      - run: git commit -m "chore: auto-sync agents" || true
      - run: git push
```

---

## Editing Agents

### Add or Edit an Agent

1. Edit the source file: `.claude/agents/categories/{category}/{agent-name}.md`

**File format:**
```yaml
---
name: agent-name
description: "Short description for routing and discovery"
tools: "Read, Write, Edit, Bash, Glob, Grep"
model: sonnet
---

Full instructions here. This becomes the developer_instructions field.
Can be multiple paragraphs, code blocks, etc.
```

2. Run the orchestrator to sync:
```bash
python scripts/orchestrate_agent_sync.py
```

3. Commit changes:
```bash
git add .claude/agents/categories/ .codex/agents/ .agents/plugins/
git commit -m "feat: update {agent-name} agent definition"
git push
```

### Sync Ratio Understanding

- **Codex ratio:** Usually 95-100% (some agents may not have TOML equivalents)
- **Antigravity ratio:** Usually 90-100% (depends on plugin.json coverage)

If ratios drop below expectations, check:
- Are new agents missing `---` frontmatter?
- Are plugin definitions updated in `.claude-plugin/plugin.json`?
- Did the sync script error? (Re-run with verbose output)

---

## Troubleshooting

### Agents not syncing to Codex

```bash
# Check for syntax errors in agent files
python scripts/sync_agents_to_codex.py

# Verify YAML frontmatter is valid
grep -r "^---$" .claude/agents/categories/
```

### Agents not syncing to Antigravity

```bash
# Check plugin.json files exist
find .claude/agents/categories -name "plugin.json"

# Check for directory structure
ls -la .agents/plugins/

# Re-run sync
python scripts/sync_agents_to_antigravity.py
```

### MCP servers not loading

```bash
# Verify environment variables are set
env | grep GCP_

# Check .codex/config.toml syntax
python3 -c "import tomllib; tomllib.load(open('.codex/config.toml', 'rb'))"

# Verify URLs are correct (should not have typos or redirects)
curl -H "Authorization: Bearer $GCP_BEARER_TOKEN" "$GCP_BIGQUERY_MCP_URL/health" || echo "MCP unreachable"
```

### Codex hook not running

```bash
# Check hook configuration
cat .codex/hooks.json

# Manually trigger sync
python scripts/sync_agents_to_codex.py

# Inspect hook logs in Codex session output
```

---

## Multi-Army Coordination

Agent sync enables **seamless multi-platform agentic building:**

| Platform | Agents sourced from | Use case |
|----------|---|---|
| **Claude Code** | `.claude/agents/categories/` (direct) | Deep, strategic, complex features |
| **Codex** | `.codex/agents/` (synced from Claude) | GitHub-native reviews, board integration |
| **Antigravity CLI** | `.agents/plugins/` (synced from Claude) | Lightweight Gemini tasks, quick fixes |
| **GitHub Copilot** | GitHub app routing (XS/S issues) | Fast coding, well-scoped tasks |

All three armies read from the same agent definitions. Changes propagate automatically via sync scripts and hooks.

---

## Advanced: Customizing Sync

### Exclude agents from sync

Edit the sync script to filter agents:

```python
# In scripts/sync_agents_to_codex.py, add a filter:
if md_file.name in ['README.md', 'TAXONOMY.md', 'internal-only.md']:
    continue
```

### Add custom sync targets

Create a new `sync_agents_to_{platform}.py` script following the same pattern:
1. Read `.claude/agents/categories/*.md`
2. Parse frontmatter + instructions
3. Convert to target format
4. Write to target directory

Then integrate into `orchestrate_agent_sync.py`.

---

## Summary

- **Source:** `.claude/agents/categories/` (172 agents)
- **Codex:** `.codex/agents/` (auto-sync on SessionStart)
- **Antigravity:** `.agents/plugins/` (manual or CI/CD)
- **Orchestrator:** `python scripts/orchestrate_agent_sync.py` (audit or full sync)
- **MCP Tools:** 4 GCP services (BigQuery, Storage, Observability, Vertex AI)

Edit agents once. Everywhere stays in sync.
