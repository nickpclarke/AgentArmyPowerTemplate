# hmac-verify-image — scaffold

**Status:** scaffold (image.json + this README + setup.sh placeholder).

## What this image will be

Reusable HMAC-signature verification sidecar. Sits in front of any spoke that needs to accept signed webhooks (GitHub `X-Hub-Signature-256`, Stripe `Stripe-Signature`, Postmark `X-Postmark-Signature`, etc.). Verifies the signature constant-time, applies replay protection (5-min TTL by delivery-id), then proxies the verified request to the upstream spoke.

This lifts a pattern that already exists inside `templates/event-bridge-image/` — separating it now (a) lets it be reused without copy-pasting and (b) gives it its own image-doctor so the security invariant is testable in isolation.

## Why function-tier

- **Independent rollout** — security primitives ship without rebuilding their host spoke.
- **Composable** — drop it in front of any new spoke that takes signed input, no spoke code changes.
- **Auditable in isolation** — its doctor proves the constant-time + replay invariants without depending on the host spoke being up.

## Backlog row

No new backlog row — this image realizes the verification half of `contracts/webhook-receiver.openapi.yaml` (already in the registry) for any signed-webhook source.
