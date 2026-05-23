# Frequently Asked Questions

## Armies & Routing

### How do I know which army to use?
Use this decision tree:
1. **XS/S bug or feature** with clear requirements? → **Copilot** (label `copilot-task`)
2. **L/XL feature or architecture**? → **Claude Code** (assign specialist)
3. **Data pipeline or ETL/ELT**? → **dlt** (assign `dlt-engineer`)

See [Armies Overview](armies-overview.md) for details.

### Can Copilot handle my task?
Copilot is best for:
- Bug fixes (XS, isolated change)
- Small features (S, clear spec)
- PR reviews
- Board queries (@board-manager)

If your task requires architecture, deep thinking, or multi-file changes, use Claude Code.

### What if I'm not sure which specialist to pick?
Start with the domain:
- **Backend/API** → `backend-developer` (they'll sub-delegate to language specialist)
- **Frontend** → `frontend-developer` (they'll sub-delegate)
- **Data** → `dlt-engineer` or `data-engineer`
- **Architecture** → `architect-reviewer`
- **Security** → `security-auditor`

The specialist will escalate if needed.

---

## GitHub Projects & Workflow

### Why isn't my issue moving to "Done"?
**Reason**: Your PR doesn't contain `Closes #N` / `Fixes #N` / `Resolves #N`.

**Fix**: 
```
# In PR body, add:
Closes #42
```

The `auto-status` workflow only fires when this link exists.

### Can I manually update Status?
Generally no. Let `auto-status` manage it:
- Issue created → Backlog
- Moved to Ready field → Ready
- PR opened → In Progress
- PR merged with `Closes #N` → Done

**Exception**: If workflow fails, manually correct Status. Don't override routine updates.

### What's the difference between Type and Size?
- **Type** (Epic/Feature/Story/Enabler/Bug/Spike) = what kind of work
- **Size** (XS/S/M/L/XL) = how much effort

Both are required. Type tells you the hierarchy; Size tells you the routing.

---

## SAFe & Planning

### What's a PI (Program Increment)?
A ~10-week planning horizon with:
- 5 sprints (2-week iterations)
- 1 PI goal
- Quarterly business review

Set the `PI` field on all issues during planning.

### What's the difference between Size and Estimate?
- **Size** (XS/S/M/L/XL) = t-shirt estimate for routing
- **Estimate** (story points: 1,2,3,5,8,13) = Fibonacci scale for velocity tracking

Both are independent fields. Size drives routing; Estimate drives velocity.

### How do I prioritize work?
Use the Priority field:
- **P0** = Must ship this sprint
- **P1** = Should ship this PI
- **P2** = Backlog; deprioritize

Sort the board by Priority during sprint planning.

---

## Claude Code & Workflows

### How long does Claude Code take?
Depends on Size:
- XS (0.5 day) → 15-30 min
- S (1 day) → 1-4 hours
- M (3 days) → 4-24 hours
- L (1 week) → 1-3 days
- XL (>1 week) → 3+ days + planning overhead

Copilot is faster for XS/S. Claude Code is deeper but slower.

### Can I add Claude Code to a GitHub Actions?
Not directly. Create an issue, Claude Code works locally, opens a PR. GitHub Actions then tests the PR.

For automation within Actions, use Copilot Coding Agent or GitHub Scripts.

### What's the difference between Claude Code and Copilot?
| Aspect | Claude Code | Copilot |
|--------|------------|---------|
| **Where** | Local IDE / CLI | GitHub web |
| **Speed** | Slower (deeper) | Fast (shallow) |
| **Complexity** | L/XL tasks | XS/S tasks |
| **Concurrency** | 1 agent per PR | Automatic on all PRs |
| **Think time** | Yes (reasoning) | No |

---

## Copilot Army & Automation

### How do I trigger Copilot Coding Agent?
Add the `copilot-task` label to an issue. Copilot will:
1. Create a branch
2. Implement changes
3. Open a PR
4. Auto-merge on green CI

No manual intervention needed.

### Can Copilot do complex features?
Sometimes, if:
- Requirements are crystal clear
- Feature is small (S size)
- No architectural decisions needed

Otherwise, it's better handled by Claude Code.

### What's @board-manager?
GitHub Copilot Chat extension for querying the GitHub Projects board:

```
@board-manager What issues are in In Progress?
@board-manager Show me P0 issues for PI-1
@board-manager Who's working on the auth feature?
```

Requires the extension installed in your Copilot Chat.

---

## dlt Data Pipelines

### What's dlt?
**dlt** = "data load tool" — a lightweight Python framework for ETL/ELT pipelines.

Handles:
- Source extraction (API, file, database)
- Incremental loading (full + delta)
- Schema inference & evolution
- Destination wiring (DuckDB, BigQuery, Snowflake, Postgres)

### When should I use dlt vs manual scripts?
**Use dlt if**:
- You need incremental loading
- Schema might change
- Multiple destinations
- Data quality checks needed

**Use manual scripts if**:
- One-off ETL
- Destination is fixed
- No future changes expected

dlt is better for production pipelines. Manual scripts are fine for exploration.

### How do I add a new source?
1. Create an issue with source specification
2. Assign `dlt-engineer`
3. Include: API docs, auth requirements, incremental loading strategy
4. dlt-engineer creates source connector
5. Merge to `dlt_pipelines/sources/`

---

## Security & Compliance

### When should I use security-auditor?
For:
- Security architecture review
- Vulnerability assessment
- Compliance gap analysis
- Code security audit
- Risk identification

For actual implementation of security controls, use `security-engineer`.

### What's the difference between security-auditor and security-engineer?
- **security-auditor** → Finds vulnerabilities (assessment)
- **security-engineer** → Implements controls (defense)

Use auditor for discovery. Use engineer for remediation.

---

## Contributing & Development

### Can I fork and modify agents?
Yes. Agents in `.claude/agents/categories/` are templates.
- Copy and customize for your team
- Don't break MECE distinctiveness
- Use `/agent-distinctiveness-advocate` to validate changes

### How do I add a new agent?
1. Create agent definition in `.claude/agents/categories/{category}/`
2. Follow the template structure
3. Ensure it's semantically distinct (MECE)
4. Run audit to validate: `/agent-distinctiveness-advocate`

### Can I modify workflows?
Yes, but carefully:
- `auto-status` is critical — don't break the Status → Issue link
- `copilot-review` should run on all PRs
- `copilot-coding-agent` routes by label
- `deploy-docs` builds mkdocs on doc changes

Test workflow changes on a feature branch first.

---

## Troubleshooting

### My PR didn't auto-merge
Check:
1. Is `Closes #N` in the PR body?
2. Did CI pass (green checks)?
3. Is auto-merge enabled on the repo?
4. Are there required reviewers blocking?

### A Copilot PR is incomplete
1. Remove `copilot-task` label
2. Add `agent-army-task` label
3. Assign Claude Code specialist
4. They'll extend or rewrite as needed

### Status didn't auto-update
1. Check PR body for `Closes #N` / `Fixes #N` / `Resolves #N`
2. Check `auto-status` workflow ran without error
3. If still broken, manually update Status field
4. Report bug on GitHub Issues

---

## Learning Resources

- **[Quick Start](quick-start.md)** — 5-minute setup
- **[Armies Overview](armies-overview.md)** — Three armies model
- **[Routing Matrix](routing-matrix.md)** — Decision tree
- **[Agent Roster](agents.md)** — 168+ specialists
- **[GitHub Projects](github-projects.md)** — Coordination plane
- **[SAFe Framework](safe.md)** — PI planning
