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
- **[Routing Matrix](routing-matrix.md)** — Detailed decision tree
- **[GitHub Projects](github-projects.md)** — Shared coordination plane
