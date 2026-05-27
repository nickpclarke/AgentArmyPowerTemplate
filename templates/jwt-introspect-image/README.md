# jwt-introspect-image — scaffold

**Status:** scaffold (image.json + this README + setup.sh placeholder).

## What this image will be

A small JWT-introspection sidecar that any spoke can call to verify a forwarded user JWT (per [ARC-ADR-002](../../docs/decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md)). Centralizes JWKS caching, leeway handling, and revocation lookups so each spoke doesn't re-implement RS256 verify + JWKS rotation logic separately.

The verify-once-in-BE design from ADR-002 doesn't prohibit other spokes from *also* verifying defensively — this sidecar makes that cheap. Particularly useful as MC starts handling tools that act on the user's behalf.

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Cross-cutting** — auth verification belongs in a sidecar, not duplicated across every spoke.
- **Small static surface** — a single `/introspect` endpoint; tiny binary.
- **Independent rollout** — JWKS issuer changes, leeway tuning, or revocation-cache updates ship without touching any spoke.

## Backlog row

No new backlog row — realizes the verification half of [ARC-ADR-002](../../docs/decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md), which is already in the registry.
