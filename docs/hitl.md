# Human-in-the-Loop Decisions

Use HITL decision artifacts when an agent should not decide alone.

## Use HITL for

- License and public release decisions.
- Security exceptions.
- Long-lived workflow governance.
- Ambiguous architecture tradeoffs.
- Destructive or irreversible changes.

Blocked work should carry `awaiting-human`; the decision issue should carry `hitl-decision`.
