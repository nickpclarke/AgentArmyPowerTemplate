# Using Claude Code

Guide to working with Claude Code within AgentArmy.

## What is Claude Code?

Claude Code is a specialized AI agent that works locally and deeply on complex tasks. It's part of the Claude Code Army and excels at:

- Architecture and design decisions
- Complex refactoring and multi-file changes
- Security audits and compliance work
- Integration challenges
- Performance optimization

## When to Use Claude Code

**Best for:**
- Large features (L/XL size)
- Architecture decisions
- Complex bugs with unclear root cause
- Security and compliance work
- Cross-cutting refactoring

**Not ideal for:**
- Simple bug fixes (use Copilot instead)
- Quick code generation (use Copilot instead)
- Exploratory work without clear direction

## How to Delegate to Claude Code

1. Create an issue on GitHub Projects with:
   - Type, PI, Size, Estimate filled
   - Clear acceptance criteria
   - Any context or constraints
2. Assign the appropriate specialist (e.g., `backend-developer`, `react-specialist`)
3. Claude Code picks up the issue
4. Works locally, creates feature branch
5. Opens PR with `Closes #N` reference
6. `auto-status` workflow moves issue to Done on merge

## Working with Claude Code

### Issue Requirements

Your issue should have:
- **Type**: Feature, Bug, Enabler, etc.
- **Size**: XS/S (Copilot), M/L/XL (Claude Code)
- **Acceptance Criteria**: Clear definition of done
- **Context**: Any relevant links, related issues, constraints

### Example Issue Template

```markdown
## Acceptance Criteria

- [ ] Feature X is implemented
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Performance baseline maintained

## Context

Related to #42. Uses API from #38.

## Constraints

- Must not break existing integrations
- Performance impact must be < 5%
```

### PR Conventions

Claude Code will open PRs that:
- Link to the issue: `Closes #N`
- Are focused and reviewable (ideally <400 LOC)
- Include tests
- Pass CI checks

## Tips for Success

1. **Be specific** — Clear requirements lead to better solutions
2. **Provide context** — Link related issues, share architecture docs
3. **Set realistic timelines** — Larger tasks take longer
4. **Trust the process** — Claude Code will think deeply before implementing
5. **Review PRs thoroughly** — Feedback improves the outcome

## Availability

Claude Code operates on-demand. Response times:

- XS (≤0.5 day): 15-30 minutes
- S (≤1 day): 1-4 hours
- M (≤3 days): 4-24 hours
- L (≤1 week): 1-3 days
- XL (>1 week): 3+ days (consider breaking into stories)

## Related Resources

- **[Armies Overview](armies-overview.md)** — When to use which army
- **[Routing Matrix](routing-matrix.md)** — Finding the right specialist
- **[FAQ](faq.md)** — Common questions
