# Secrets Rotation Policy

Operational policy for rotating credentials across the AgentArmy fleet. Realizes the **security-architect** finding in [ARC-ADR-024](../decisions/ARC-ADR-024-platform-maturity-audit.md) (closes hub issue [#221](https://github.com/nickpclarke/AgentArmy/issues/221)). Companion to [ARC-ADR-011](../decisions/ARC-ADR-011-runtime-secret-resolution-workload-identity.md) (workload identity) and [`docs/arcadedb-secret-hardening.md`](../arcadedb-secret-hardening.md).

## Scope

Every credential the fleet holds is one of:

- A **provider key** the platform forwards to an external API (LLM providers, embed providers).
- A **JWT signing key** the platform uses to mint or verify session tokens.
- A **datastore root password** the platform uses to manage a Platform-tier service.
- A **GitHub credential** the fleet uses for cross-repo automation.
- A **shared webhook secret** used for HMAC verification of inbound webhooks.

All five categories must rotate. None should live longer than the cadence below without renewal. Stale credentials past their rotation window are a finding the heartbeat will eventually probe (TODO — `secrets-stale` check, see follow-up at the bottom).

## Cadence

| Credential | Storage | Cadence | Mode | Overlap window |
|---|---|---|---|---|
| **JWT signing key** ([ARC-ADR-002](../decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md)) | Key Vault `akv01-agentarmy` → `JWT_SIGNING_KEY` | **90 days** | Dual-key — `current` + `previous` both accepted by verifier; producer signs with `current` only | **7 days** |
| **OPENAI_API_KEY** | KV → `OPENAI_API_KEY` (`*_FILE` mounted) | **180 days** or on-incident | Provider dashboard generates new key, KV secret updated, ACA revision activated to pick up | None — old key revoked immediately after new key verified |
| **ANTHROPIC_API_KEY** | KV → `ANTHROPIC_API_KEY` | **180 days** or on-incident | Same as OpenAI | Same |
| **ARCADEDB root password** | KV → `ARCADEDB_ROOT_PASSWORD` | **180 days** | Rotate via ArcadeDB Studio → Security; update KV; activate new ACA revision (entrypoint reads `*_FILE`) | **24 hours** (old password kept active during revision swap) |
| **ARCADEDB platform_reader password** | KV → `ARCADEDB_PASSWORD` | **180 days** | Same pattern | Same |
| **Postgres root password** (DBOS metadata store) | KV → `POSTGRES_PASSWORD` | **180 days** | Postgres `ALTER USER`; KV update; ACA revision activate | **24 hours** |
| **PROJECT_TOKEN** (classic GitHub PAT for Projects v2) | Repo secret + KV `PROJECT_TOKEN` | **90 days** *— OR migrate to GitHub App (issue [#222](https://github.com/nickpclarke/AgentArmy/issues/222))* | Regenerate PAT; update both KV + repo secrets across all 4 repos | None — old PAT revoked after first successful workflow run with new |
| **CLAUDE_CODE_OAUTH_TOKEN** | Repo secret + KV | Per Anthropic guidance (default 365 days; renew on expiry) | Re-run `claude setup-token` interactively; update KV + repo secrets | None |
| **GHRUNNERPAT** (self-hosted runner registration token) | KV → `GHRUNNERPAT` | **90 days** | Regenerate PAT with `repo` + `workflow` scopes; KV update; new runner pods pick up on next scale-up | None — running runners keep working until next scale-up |
| **GitHub webhook HMAC secret** (event-bridge) | KV → `GITHUB_WEBHOOK_SECRET` | **180 days** or on-incident | New secret in GitHub webhook config + KV; bridge picks up via `*_FILE` on next revision | **24 hours** (both secrets accepted via dual-secret validation in bridge — TODO) |

## Triggers (rotate sooner than the cadence)

- **Any incident** involving suspected credential exposure (e.g. a PR leaked a secret via misconfigured logging) → rotate immediately + add to incident log per [ADR-024](../decisions/ARC-ADR-024-platform-maturity-audit.md) finding 5.
- **Personnel change** with admin-level access → rotate PROJECT_TOKEN, CLAUDE_CODE_OAUTH_TOKEN, and any role-bound credentials.
- **Public exposure** of a credential in git history (even if rotated) → rotate again to invalidate any cache the leaked value may sit in.
- **Provider security advisory** (OpenAI / Anthropic publish a key-compromise notice) → rotate within 24h of advisory.

## Mechanism (the "*_FILE refresh" pattern)

All ACA containers consume secrets via the `*_FILE` env pattern documented in the Image Standard: env var points at a file path; the value is read at process start (or on demand). Rotation:

1. Producer (us or provider) issues a new secret value.
2. Update the Key Vault secret (`akv01-agentarmy`) — KV versions the secret automatically.
3. Activate a new ACA revision. ACA's `secretref` resolves the latest KV version on container start; the new revision reads the new value.
4. Smoke-test the new revision (one healthy probe response).
5. Shift traffic to the new revision; deactivate the old.
6. Revoke the old credential at the producer (provider portal / ArcadeDB Studio / Postgres `ALTER USER`).

The KV-versioning-plus-ACA-revision pattern is what makes rotation safe — no in-place secret swap that could be observed mid-update.

## Dual-key vs cutover

- **Dual-key (with overlap)** — JWT signing, ArcadeDB user passwords, webhook HMAC. The verifier accepts both `current` and `previous` for the overlap window so existing sessions don't break.
- **Cutover** — OpenAI / Anthropic / GitHub PATs. The provider supplies one key at a time; the rotation is "issue new → verify new works → revoke old."

When in doubt, prefer dual-key + 24h overlap. The cost is one extra env entry; the benefit is no user-visible session breakage.

## Automation

Currently manual — operator runs rotation per cadence. The maturity target is automated rotation via Key Vault rotation policies + Event Grid → ACA revision update workflow:

```
KV secret rotates → Event Grid event → GitHub Actions workflow → az containerapp update --revision-suffix rotation-<date>
```

This is dispatched as issue [#221](https://github.com/nickpclarke/AgentArmy/issues/221) ("Document + implement secret rotation policy"). This document closes the "document" half; the "implement" half is the automation workflow above (separate PR).

## Verification

Today's verification surfaces:

- **GitHub secret scanning + push protection** — once enabled (separate audit follow-up), catches any credential committed to a repo.
- **Image Standard `agentarmy-doctor.mjs`** — checks each `image.json` declares secrets via `fileEnv` rather than `env` (file-based wins).
- **Heartbeat** (`tools/fleet-heartbeat.mjs`) — proposed follow-up: add a `secrets-stale` check that reads KV secret `lastUpdated` timestamps and warns when any exceeds its cadence + 14 days. Files an issue if `--apply`.

The third item turns this policy from documentation into measurement — what's measured improves. See follow-up below.

## Follow-ups

- [ ] Implement the KV → Event Grid → GitHub Actions rotation pipeline (issue [#221](https://github.com/nickpclarke/AgentArmy/issues/221) implementation half).
- [ ] Migrate `PROJECT_TOKEN` from classic PAT to GitHub App (issue [#222](https://github.com/nickpclarke/AgentArmy/issues/222)) — this single change removes the highest-blast-radius credential from the rotation list.
- [ ] Add `secrets-stale` check to `tools/fleet-heartbeat.mjs` — reads KV secret timestamps + emits warn findings on stale credentials.
- [ ] Enable GitHub secret scanning + push protection on all 4 repos (covered separately under [`docs/security/`](.) — TODO when this dir grows).
- [ ] Document IR runbook for "leaked PAT" (issue [#220](https://github.com/nickpclarke/AgentArmy/issues/220) → separate IR docs work).

## References

- [ARC-ADR-002](../decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md) — JWT forwarding contract
- [ARC-ADR-011](../decisions/ARC-ADR-011-runtime-secret-resolution-workload-identity.md) — Workload identity + KV-backed runtime secret resolution
- [ARC-ADR-024](../decisions/ARC-ADR-024-platform-maturity-audit.md) — Maturity audit (security-architect finding)
- [`docs/arcadedb-secret-hardening.md`](../arcadedb-secret-hardening.md) — ArcadeDB-specific secret patterns
- Image Standard ([`docs/image-standard.md`](../image-standard.md)) — secret declaration convention via `fileEnv`
