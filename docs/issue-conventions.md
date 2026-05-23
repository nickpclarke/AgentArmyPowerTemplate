# Issue Conventions

Standard practices for creating and managing issues in AgentArmy.

## Issue Fields

Every issue must have:

| Field | When | Options |
|-------|------|---------|
| **Type** | At creation | Epic, Feature, Story, Enabler, Bug, Spike, Decision |
| **PI** | At creation | PI-1, PI-2, etc. |
| **Size** | At creation | XS, S, M, L, XL |
| **Estimate** | During planning | Story points (1,2,3,5,8,13) |
| **Priority** | At creation | P0, P1, P2 |
| **Status** | Auto-managed | Todo→Ready→In Progress→In Review→Done (+ Awaiting Decision for HITL) |

## Issue Types

### Epic
- Large body of work spanning multiple PIs
- Top-level item
- Contains Features as sub-issues
- Example: "Redesign authentication system"

### Feature
- Deliverable capability within a PI
- Parent of Stories
- Contains acceptance criteria at feature level
- Example: "Add multi-factor authentication"

### Story
- User-facing value, completable in one sprint
- Sub-issue of Feature
- Contains detailed acceptance criteria
- Example: "Implement TOTP 2FA"

### Enabler
- Technical work not directly user-facing
- Infrastructure, exploration, tooling
- Enables future work
- Example: "Set up performance monitoring"

### Bug
- Defect or unintended behavior
- Same level as Story
- Routed by size (XS/S → Copilot, M+ → Claude Code)
- Example: "Login fails on slow networks"

### Spike
- Time-boxed research (max 3 days)
- Explores unknown territory
- Output: decision or recommendation
- Example: "Evaluate OIDC providers"

## Acceptance Criteria Format

Use checklist format:

```markdown
## Acceptance Criteria

- [ ] Feature X is implemented
- [ ] Acceptance criteria Y is met
- [ ] Tests are added and passing
- [ ] Documentation is updated
- [ ] Performance impact is < 5%
```

## Linking Issues

Use these links to establish relationships:

```markdown
## Related
- Relates to #42
- Blocked by #38
- Blocks #50
- Duplicates #25

## Parent
Parent of #43, #44, #45
```

## PR Conventions

Every PR must:
1. Link back to issue: `Closes #N` / `Fixes #N` / `Resolves #N`
2. Be focused and reviewable (ideally <400 LOC)
3. Include tests
4. Pass all CI checks

## Labeling

| Label | Use Case |
|-------|----------|
| `copilot-task` | Copilot Coding Agent automation |
| `needs-deep-review` | Large PR requiring thorough review |
| `needs-security-review` | Security-sensitive change |
| `blocked` | Waiting on external factor |

## Examples

### Bug Issue
```markdown
# Title
Fix: User profile doesn't load after logout

## Type
Bug

## Size
S

## Acceptance Criteria
- [ ] Profile loads correctly after logout
- [ ] No stale cache issues
- [ ] Tests cover logout flow

## Steps to Reproduce
1. Log in
2. Log out
3. Try to access profile
```

### Feature Issue
```markdown
# Title
Add dark mode toggle

## Type
Feature

## PI
PI-2

## Size
M

## Acceptance Criteria
- [ ] Dark mode theme implemented
- [ ] Toggle in user settings
- [ ] Preference persisted
- [ ] Works across all pages
```

## Related Docs

- **[Quick Start](quick-start.md)**
- **[GitHub Projects](github-projects.md)**
