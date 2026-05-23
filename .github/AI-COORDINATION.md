# AI Coordination

How Claude, Gemini, GitHub Copilot, and security scanning work together in this repo.

## The Flow

```
Issue created
  ↓
Size XS/S + clear scope?
  ├─ YES → label copilot-task
  │         ↓
  │         Copilot Coding Agent:
  │         • Creates branch
  │         • Implements changes
  │         • Opens PR
  │
  └─ NO → keep for Claude Code or manual work

PR opened
  ↓
  ├─ Gemini auto-reviews (always)
  ├─ Security scan runs (always)
  └─ Copilot auto-reviews (if enabled)
  ↓
Need strategic input?
  ├─ YES → @claude in a comment
  │         Claude responds with analysis
  │
  └─ NO → Wait for security + Gemini feedback
  ↓
All checks pass + approved?
  └─ Merge (auto or manual, depending on PR status)
```

## Who Does What

| Tool | Trigger | What it sees | When to use |
|------|---------|--------------|------------|
| **Gemini** | Every PR opens | Code diff + PR title/body | Always — automatic feedback |
| **Claude** | You mention @claude | PR conversation + code | >200 lines OR strategic decision needed |
| **Copilot Coding Agent** | `copilot-task` label | Issue description + workflow comment | XS/S bugs and stories, bounded scope |
| **Copilot Code Review** | Every PR (if enabled) | Code diff | First-pass feedback (automatic) |
| **Security Scan** | Every push/PR | Full codebase | Dependency + code vulnerabilities (automatic) |

## When to Mention @claude

```
DO @claude when:
  • PR is >200 lines + logic is non-obvious
  • Architectural decision: "should we do X or Y?"
  • Security implications beyond code style
  • Multi-file refactor affecting multiple systems
  • Gemini's review seems shallow for the complexity

DON'T mention when:
  • Copilot task, Gemini already reviewed, security passed
  • Simple doc fix or style cleanup
  • Clear bug fix with obvious solution
```

## Boundaries

**Copilot handles XS/S:**
- Single file or tightly related files (≤50 lines)
- Clear acceptance criteria
- No architecture decisions
- Template repo work only (docs, workflows, config)

**Claude Code handles M+:**
- Multi-file impact
- Architectural decisions
- Complex refactors
- Strategy / planning

**If Copilot task gets too complex:**
- Remove `copilot-task` label
- Add `agent-army-task` label
- It routes to Claude Code

## Security Scanning

When security scan fails on a PR:
1. Review findings in PR checks
2. **Don't merge** until resolved
3. Ask @claude if severity is unclear
4. Fix or document exception

---

## Setup Checklist

- [x] GitHub Copilot enabled (code review + coding agent)
- [x] Gemini GitHub App installed
- [x] Claude GitHub App installed
- [x] Vercel GitHub App installed
- [x] Security scanning enabled
- [ ] PR template updated (optional — good-to-have)
- [ ] Issue template updated (optional — good-to-have)
