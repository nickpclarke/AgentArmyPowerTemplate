# Access Review

Run this review quarterly and after any Sev1/Sev2 incident involving identity,
secrets, or production access.

Machine-checkable records validate against `contracts/access-review.schema.json`.
Use `python tools/validate-access-reviews.py` before storing the redacted review
packet in HVFS or mirroring it to bootstrap evidence channels.

## Scope

- GitHub organization, repositories, teams, apps, deploy keys, classic PATs.
- GitHub Actions environments, secrets, variables, and self-hosted runners.
- Azure subscriptions, resource groups, Container Apps, Key Vault, managed
  identities, service principals, federated credentials, role assignments.
- Cloudflare Access policies and service tokens.
- Provider consoles for LLM/API keys and spend caps.
- Production admin paths and break-glass credentials.

## Review Checklist

| Area | Check | Evidence |
|---|---|---|
| GitHub users | Every member is expected and has the minimum role. | Member/team export |
| GitHub apps | Installed apps are expected and scoped. | App installation export |
| Classic PATs | No classic PAT remains for automation unless risk accepted. | Secret inventory |
| Actions secrets | Secrets are named, owned, and justified. | Repo/org secret list |
| Environments | Production deploys require approval and OIDC. | Environment export |
| Runners | Self-hosted runners match the private/trusted-only model. | Runner list |
| Azure RBAC | Managed identities have minimum resource scope. | Role assignment export |
| Key Vault | Access is least privilege; secret names match manifest. | KV RBAC/export |
| Cloudflare | MCP/control routes require service token or approved identity. | Access policy export |
| Providers | Keys have caps, owners, and rotation dates. | Provider dashboard export |

## Signoff Template

```markdown
Review period:
Reviewer:
Date:

Findings:
- 

Removed access:
- 

Exceptions:
- 

Follow-up issues:
- 
```

## Failure Rule

Unexpected privileged access is a Sev2 by default. If the access is confirmed
to have been used suspiciously, escalate to Sev1.
