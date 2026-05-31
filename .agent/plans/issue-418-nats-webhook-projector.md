# ExecPlan: Issue 418 NATS-to-webhook projector

## Goal

Adopt capability `platform.messaging.update-system` in AgentArmy by adding the
smallest coherent NATS-to-webhook projector bridge for platform update
subscriptions.

## Context

- Issue: https://github.com/nickpclarke/AgentArmy/issues/418
- Target: Implement the NATS-to-webhook projector bridge for platform update subscriptions
- Owner lens: `async-messaging-engineer`
- Reviewer lenses: `mcp-developer`, `api-designer`, `contract-test-engineer`, `security-auditor`
- Existing bridge image: `templates/event-bridge-image/`
- Existing relay: `templates/event-bridge-image/scripts/nats-relay.py`

## Non-goals

- Do not replace the existing inbound webhook receiver.
- Do not introduce a new source of truth; webhook delivery is a projection from NATS CloudEvents.
- Do not require a live broker for unit validation.

## Source Of Truth

- `AGENTS.md`
- `CLAUDE.md`
- `docs/decisions/ARC-ADR-022-event-bus-bridges.md`
- `ontology/platform-self-model/generated/lexicon.yaml`
- Issue #418 comments and adoption target

The issue references `docs/untool-bootstrap-order.md` and
`docs/platform-capability-log.feed.json`, but those files are absent in this
checkout. Preserve the names from the issue comments and generated lexicon.

## Work Breakdown

1. Add `project-webhooks` entrypoint mode.
2. Add `webhook_projector.py` with subscription loading, MECE family validation,
   CloudEvent filters, webhook auth headers, and redacted logging helpers.
3. Add JSON Schema and example subscription config.
4. Add unit tests for validation, filtering, auth, and redaction.
5. Update README, image manifest, and contracts registry.
6. Validate with unit and syntax checks, then open a PR with `Closes #418`.

## File Ownership

- Implementation: `templates/event-bridge-image/scripts/webhook_projector.py`
- Tests: `templates/event-bridge-image/scripts/test_projector.py`
- Docs/config: `templates/event-bridge-image/README.md`,
  `templates/event-bridge-image/image.json`,
  `templates/event-bridge-image/entrypoint.sh`
- Contract: `contracts/platform-update-subscription.schema.json`,
  `contracts/examples/platform-update-subscription.example.json`,
  `docs/contracts.md`

## Tests And Validation

- `python -m unittest templates.event-bridge-image.scripts.test_projector`
  is not module-safe because of hyphenated directories; run the file directly.
- `python -m unittest discover -s templates/event-bridge-image/scripts -p test_projector.py -v`
- `python -m py_compile templates/event-bridge-image/scripts/webhook_projector.py templates/event-bridge-image/scripts/test_projector.py`
- `python -m json.tool contracts/platform-update-subscription.schema.json`
- `python -m json.tool contracts/examples/platform-update-subscription.example.json`

## Risks

- Live JetStream round-trip is not covered by unit tests in this slice.
- Azure Key Vault resolution is represented as fail-closed `akv://` refs unless
  a runtime secret reference map is injected.

## Decision Log

- Keep the older `relay-outbound` mode intact and add a new `project-webhooks`
  mode for subscription-aware delivery.
- Require HTTPS and explicit auth for active sinks; allow no unauthenticated
  active webhook deliveries.
- Require replayable, `akv://`-referenced auth for `platform.security.*`.
