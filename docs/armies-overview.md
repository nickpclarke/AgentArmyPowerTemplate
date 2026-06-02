# Armies Overview

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
1. Create an issue on the GitHub Projects board.
2. Assign the correct specialist (e.g., `backend-developer`, `react-specialist`).
3. Set Type, PI, and Size fields.
4. Agent picks up issue and works locally.
5. Opens PR with `Closes #N` link.
6. `auto-status` workflow moves issue to Done on merge.

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
1. Create an issue or label existing issue with `copilot-task`.
2. Copilot Coding Agent automatically:
   - Creates a branch
   - Implements the change
   - Opens a PR with `Closes #N`
3. Auto-merge on green CI.

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
1. Create an issue with specialized domain tags.
2. Trigger via Antigravity CLI: agents automatically synced from Claude definitions.
3. Or run ad-hoc: `antigravity chat --agent security-architect`.

---

## 🔄 Shared Agent Definitions

All three armies read from **the same agent definitions** (`.claude/agents/categories/`):
- **Claude Code** uses agents directly via `Agent()` tool.
- **Codex** receives synced agents in `.codex/agents/` via `SessionStart` hook.
- **Antigravity CLI** receives agents organized as plugins in `.agents/plugins/`.

---

## 🗺️ Routing Matrix

| Task | Army | Why |
|------|------|-----|
| Fix a bug (XS/S) | Copilot | Fast, GitHub-native |
| Simple feature (S, clear spec) | Copilot | Speed and velocity |
| Large feature (L/XL) | Claude Code | Depth and architecture |
| Architect a system | Claude Code | Strategic thinking |
| Security audit | Claude Code | Deep analysis |
| PR review (any size) | Copilot | Automatic + Copilot |
| Refactor monolith | Claude Code | Complex, multi-file |
| Quick research / exploration | Antigravity CLI | Lightweight, autonomous |
| Multi-agent exploration | Antigravity CLI | Parallel agent spawning |
