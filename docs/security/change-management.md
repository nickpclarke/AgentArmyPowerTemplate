# Security Change Management

Security-relevant changes must leave a clear trail from issue to PR to
validation to deployment. This is how future agents can prove what changed and
why.

The machine-readable change packet lives at
`contracts/security-change-record.example.json` and validates against
`contracts/security-change-record.schema.json` with
`python tools/validate-security-change-records.py`. Fleet Console consumes this
packet through `contracts/security-dashboard-state.example.json`, so the native
untool/HVFS change trail is the agent-facing source of truth while GitHub issue
links remain bootstrap mirrors.

## Security-Relevant Changes

Treat a change as security-relevant when it touches:

- Authentication, authorization, sessions, JWTs, roles, or service identity.
- Secrets, Key Vault, `secretRef`, credential broker, provider keys, or spend
  caps.
- Public ingress, WAF, Cloudflare Access, routing, or MCP/control-plane paths.
- CI/CD, deployment, image build, SBOM, provenance, signing, runners, or
  workflow permissions.
- Telemetry redaction, audit logs, evidence anchors, incident runbooks, or
  autonomous remediation.
- UDA query policy, forge/sieve gates, data access, privacy, or retention.

## Required Trail

1. Issue describes the risk, control, and acceptance criteria.
2. PR links the issue and names the validation commands.
3. Review includes the relevant security lens or subagent.
4. CI produces evidence artifacts where applicable.
5. Deployment records the image digest, revision, smoke test, and rollback path.
6. Residual risk is added to `risk-register.md` if it remains.

## PR Checklist

```markdown
## Security Change Checklist

- [ ] Linked issue:
- [ ] Controls affected:
- [ ] Secrets touched: none / names only
- [ ] Telemetry reviewed for redaction:
- [ ] Tests or validation:
- [ ] Evidence artifacts:
- [ ] Rollback:
- [ ] Residual risk:
```

## Exception Rule

Exceptions require a linked accepted-risk issue with owner, expiry, and review
date. Permanent exceptions are architecture decisions and need an ADR or a
Decision artifact.
