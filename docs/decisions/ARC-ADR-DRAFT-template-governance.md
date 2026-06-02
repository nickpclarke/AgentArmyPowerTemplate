| Field | Value |
|---|---|
| Status | Proposed |
| Date | YYYY-MM-DD |
| Owner | Template maintainers |
| Related | Template governance |

---

# ARC-ADR-DRAFT: Template Governance

## Context

Derived repositories need clear boundaries between reusable template content and organization-specific implementation.

## Decision

Keep the public template neutral and require placeholders for owners, URLs, project numbers, secrets, and environment-specific identifiers.

## Consequences

Template updates remain broadly reusable. Teams must document any local customization in their derived repository.

## Validation

A no-product-term audit and docs build run before publishing template updates.
