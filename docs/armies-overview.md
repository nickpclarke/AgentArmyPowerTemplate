# The Three Armies

AgentArmy coordinates three specialized armies, each with distinct strengths and operating models.

## 🧠 Claude Code Army

**Depth, strategy, and architectural expertise.**

### Strengths
- Deep thinking and complex problem-solving
- Multi-file refactoring and architecture design
- Security audits and compliance work
- Enterprise patterns and scalability planning
- Handles ambiguous requirements

### How to Delegate
1. Create an issue on the GitHub Projects board
2. Assign the correct specialist (e.g., `backend-developer`, `react-specialist`)
3. Set Type, PI, and Size fields
4. Agent picks up issue and works locally
5. Opens PR with `Closes #N` link
6. `auto-status` workflow moves issue to Done on merge

### Best For
- Requirements analysis and user story refinement
- System architecture and design decisions
- Large features (L/XL stories)
- Code reviews and security audits
- Complex refactoring

### Response Time
Slower but deeper — typically hours to days depending on complexity.

---

## ⚡ GitHub Copilot Army

**Speed, simplicity, and GitHub-native operations.**

### Strengths
- Lightweight task automation
- PR review and feedback
- GitHub Projects board queries via `@board-manager`
- Fast turnaround on simple tasks
- Runs entirely within GitHub

### How to Delegate
1. Create an issue or label existing issue with `copilot-task`
2. Copilot Coding Agent automatically:
   - Creates a branch
   - Implements the change
   - Opens a PR with `Closes #N`
3. Auto-merge on green CI

### Best For
- Bug fixes (XS/S size)
- Simple features (S size, clear requirements)
- PR reviews (automatic on all PRs)
- Board queries and status checks
- Label-based automation

### Response Time
Fast — typically minutes to hours. Perfect for iteration velocity.

---

## 🚀 Antigravity CLI / Gemini Army

**Autonomous execution with lightweight agentic control.**

### Strengths
- Gemini's autonomous reasoning and planning
- Lightweight agent execution (no heavy sessions)
- CLI-native workflows and scripting
- Quick research and knowledge synthesis
- Multi-round problem solving with less overhead

### How to Delegate
1. Create an issue with specialized domain tags
2. Trigger via Antigravity CLI: agents automatically synced from Claude definitions
3. Or run ad-hoc: `antigravity chat --agent security-architect`

### Best For
- Quick research and exploration
- CLI automation and scripting
- Lightweight agents for exploratory work
- Parallel multi-agent coordination
- Autonomous problem decomposition

### Response Time
Fast to very fast — optimized for lightweight execution and quick turnaround.

---

## 🔄 Shared Agent Definitions

All three armies read from **the same agent definitions** (`.claude/agents/categories/`):

- **Claude Code** uses agents directly via `Agent()` tool
- **Codex** receives synced agents in `.codex/agents/` via `SessionStart` hook
- **Antigravity CLI** receives agents organized as plugins in `.agents/plugins/` (workspace) or `~/.gemini/antigravity-cli/plugins/` (global)

**Synchronization mechanisms:**
- **Codex**: Automatic on `SessionStart` hook via `.codex/hooks.json`
- **Antigravity**: Manual sync via orchestrator — `python scripts/orchestrate_agent_sync.py --antigravity [--global]`
- **GitHub apps**: Receive routing definitions from source of truth

Edit agent definitions once in `.claude/agents/categories/`, then orchestrate synchronization across platforms.

See **[Agent Synchronization](agent-sync.md)** for full details and orchestration commands.

---

## 🗺️ Routing Matrix

| Task | Army | Why |
|------|------|-----|
| Fix a bug (XS/S) | Copilot | Fast, GitHub-native |
| Simple feature (S, clear spec) | Copilot | Speed and velocity |
| Large feature (L/XL) | Claude Code | Depth and architecture |
| Architect a system | Claude Code | Strategic thinking |
| API → database pipeline | Claude Code (`dlt-engineer`) | Pipeline specialists |
| Data warehouse prep | Claude Code (`dlt-engineer`) | ETL/ELT expertise |
| Security audit | Claude Code | Deep analysis |
| PR review (any size) | Copilot | Automatic + Copilot |
| Refactor monolith | Claude Code | Complex, multi-file |
| Simple code generation | Copilot | Speed |
| Quick research / exploration | Antigravity CLI | Lightweight, autonomous |
| Multi-agent exploration | Antigravity CLI | Parallel agent spawning |
| Ad-hoc scripting | Antigravity CLI | CLI-native workflows |
| Autonomous problem decomposition | Antigravity CLI | Gemini reasoning + lightweight execution |

---

## 🎯 Principles

### 1. **Route Early, Route Right**
Avoid generalist work. Pick the specialist before creating the issue.

### 2. **Define of Ready**
Every issue needs: Type, PI, Size, Estimate, acceptance criteria.

### 3. **Closes #N**
Every PR must link back to its issue with `Closes #N` in the body.

### 4. **Status Follows Work**
`auto-status` workflow moves issues automatically. Don't manually update status unless correcting.

### 5. **Specialize, Don't Duplicate**
Armies don't overlap. Copilot handles GitHub-native work. Claude Code handles depth. dlt handles pipelines.

---

## 📚 Learn More

- **[Specialist Roster](agents.md)** — specialist agents across 11 categories
- **[Agent Synchronization](agent-sync.md)** — How agents sync across platforms (Codex, Antigravity, MCP servers)
- **[Routing Matrix](routing-matrix.md)** — Detailed decision tree
- **[GitHub Projects](github-projects.md)** — Shared coordination plane
- **[Codex Integration](codex.md)** — Codex-specific workflows and hooks
- **[Copilot Setup](copilot.md)** — GitHub Copilot configuration and best practices
