# Copilot Task Labeling

How to label issues for GitHub Copilot Coding Agent automation.

## The copilot-task Label

Add the `copilot-task` label to issues you want Copilot to handle automatically.

### Copilot will:
1. Create a feature branch
2. Implement the change
3. Open a PR
4. Auto-merge when CI passes

## When to Use copilot-task

**Use for:**
- Bug fixes (XS size)
- Simple features (S size)
- Clear requirements and acceptance criteria
- Isolated changes (single file or related files)

**Don't use for:**
- Architecture decisions
- Complex multi-file refactors
- Ambiguous requirements
- Large features (L/XL)

## Labeling Guidelines

1. Set **Size** to XS or S
2. Set **Type** to Bug or Story
3. Write clear **acceptance criteria**
4. Add `copilot-task` label
5. Copilot picks it up automatically

## Example: Bug Fix

```markdown
## Title
Fix: API timeout on slow networks

## Acceptance Criteria
- [ ] Increase default timeout to 30s
- [ ] Add exponential backoff retry logic
- [ ] Tests cover timeout scenario

## Labels
copilot-task, bug, S size
```

## Monitoring Copilot's Work

1. Watch the board — Status auto-updates
2. Check PR for changes
3. Provide feedback if needed

If PR is incomplete:
- Remove `copilot-task`
- Add `agent-army-task`
- Assign Claude Code specialist

## Related Docs

- **[Copilot Army Guide](copilot.md)**
- **[FAQ](faq.md)**
