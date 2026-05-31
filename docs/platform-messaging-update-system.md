# Platform Messaging Update System

Capability ID: `platform.messaging.update-system`

AgentArmy adopts this capability through the event-bridge `project-webhooks`
mode. The bridge consumes NATS JetStream CloudEvents, applies active platform
update subscription filters, and projects matching events to subscriber webhook
sinks. The webhook projector is not a source of truth; it forwards the canonical
CloudEvent already present on the bus.

## Message Families

The projector accepts only these MECE subject families:

- `platform.capability.*`
- `platform.adoption.*`
- `platform.hvfs.*`
- `fleet.agent.*`
- `platform.security.*`

Whole-broker scopes, top-level wildcards, and foreign families fail closed.

## Subscription Contract

Source: `contracts/platform-update-subscription.schema.json`

Each subscription declares:

- `id`
- `active`
- `subjects`
- optional exact CloudEvents filters
- `sink.url`
- `sink.auth`
- replay/security posture flags

Active sinks must use HTTPS and one of the documented auth modes:

- `hmac-sha256`
- `cloudflare-access-service-token`

`platform.security.*` subscriptions must be `securityTrusted`, `replayable`,
HTTPS, and backed by `akv://` secret refs.

## Delivery Contract

The projector sends the NATS CloudEvent as a structured CloudEvents HTTP POST:

```http
POST {sink.url}
Content-Type: application/cloudevents+json
User-Agent: AgentArmy-Webhook-Projector/0.1
X-AgentArmy-Capability: platform.messaging.update-system
X-AgentArmy-Subscription-Id: <subscription id>
X-AgentArmy-Delivery-Id: <stable delivery id>
X-AgentArmy-Attempt: <1-based attempt>
Idempotency-Key: <ce-source>#<ce-id>
```

Delivery is at-least-once. Subscribers must dedupe by
`X-AgentArmy-Delivery-Id`, `Idempotency-Key`, or the CloudEvents `id`.

## Validation

Focused local validation:

```powershell
python -m unittest discover -s templates/event-bridge-image/scripts -p test_projector.py -v
python -m py_compile templates/event-bridge-image/scripts/webhook_projector.py templates/event-bridge-image/scripts/test_projector.py
python -m json.tool contracts/platform-update-subscription.schema.json
python -m json.tool contracts/platform-update-cloudevent.schema.json
python -m json.tool contracts/examples/platform-update-subscription.example.json
python -m json.tool contracts/examples/platform-update-cloudevent.example.json
```
