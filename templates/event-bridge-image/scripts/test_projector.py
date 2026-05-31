from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import httpx


MODULE_PATH = Path(__file__).with_name("webhook_projector.py")
SPEC = importlib.util.spec_from_file_location("webhook_projector", MODULE_PATH)
projector = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["webhook_projector"] = projector
SPEC.loader.exec_module(projector)


def subscription(**overrides):
    base = {
        "id": "capability-watchdog",
        "active": True,
        "subjects": ["platform.capability.changed.v1"],
        "filters": {
            "eventTypes": ["platform.capability.changed.v1"],
            "sources": ["urn:agentarmy:test"],
            "dataEquals": {"capabilityId": "platform.messaging.update-system"},
        },
        "sink": {
            "url": "https://subscriber.example.com/events?token=do-not-log",
            "auth": {
                "type": "hmac-sha256",
                "secretRef": "akv://agentarmy/subscriptions/capability-watchdog-hmac",
                "keyId": "watchdog-v1",
            },
        },
        "replayable": True,
    }
    base.update(overrides)
    return base


def event(**overrides):
    base = {
        "specversion": "1.0",
        "id": "event-1",
        "source": "urn:agentarmy:test",
        "type": "platform.capability.changed.v1",
        "time": "2026-05-31T19:05:00Z",
        "datacontenttype": "application/json",
        "data": {"capabilityId": "platform.messaging.update-system"},
    }
    base.update(overrides)
    return base


class ProjectorConfigTests(unittest.TestCase):
    def test_load_config_requires_capability_id(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"capabilityId": "wrong", "subscriptions": []}, handle)
            path = handle.name
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))

        with self.assertRaisesRegex(projector.ConfigError, "platform.messaging.update-system"):
            projector.load_config(path)

    def test_rejects_broad_subject_patterns(self):
        for subject in [">", "*", "platform.*", "fleet.*", "ops.>", "platform.capability.>.v1"]:
            with self.subTest(subject=subject):
                candidate = subscription(subjects=[subject])
                with self.assertRaises(projector.ConfigError):
                    projector.parse_subscription(candidate)

    def test_rejects_non_https_active_sink(self):
        candidate = subscription(
            sink={
                "url": "http://subscriber.example.com/events",
                "auth": {"type": "hmac-sha256", "secretRef": "akv://agentarmy/hmac"},
            }
        )
        with self.assertRaisesRegex(projector.ConfigError, "HTTPS"):
            projector.parse_subscription(candidate)

    def test_allows_local_http_only_with_dev_override(self):
        candidate = subscription(
            sink={
                "url": "http://localhost/events",
                "auth": {"type": "hmac-sha256", "secretRef": "akv://agentarmy/hmac"},
            }
        )
        parsed = projector.parse_subscription(candidate, allow_local_http=True)
        self.assertEqual(parsed.sink.url, "http://localhost/events")

    def test_security_family_requires_trust_replay_and_akv_refs(self):
        candidate = subscription(
            subjects=["platform.security.alert.v1"],
            filters={"eventTypes": ["platform.security.alert.v1"]},
            replayable=False,
            securityTrusted=True,
        )
        with self.assertRaisesRegex(projector.ConfigError, "replayable"):
            projector.parse_subscription(candidate)

        candidate = subscription(
            subjects=["platform.security.alert.v1"],
            filters={"eventTypes": ["platform.security.alert.v1"]},
            replayable=True,
            securityTrusted=False,
        )
        with self.assertRaisesRegex(projector.ConfigError, "securityTrusted"):
            projector.parse_subscription(candidate)

        candidate = subscription(
            subjects=["platform.security.alert.v1"],
            filters={"eventTypes": ["platform.security.alert.v1"]},
            replayable=True,
            securityTrusted=True,
            sink={
                "url": "https://subscriber.example.com/security",
                "auth": {"type": "hmac-sha256", "secretRef": "env://SECURITY_HMAC"},
            },
        )
        with self.assertRaisesRegex(projector.ConfigError, "akv://"):
            projector.parse_subscription(candidate)


class ProjectorFilterTests(unittest.TestCase):
    def test_active_matching_subscription_delivers(self):
        parsed = projector.parse_subscription(subscription())
        matches = projector.matching_subscriptions([parsed], "platform.capability.changed.v1", event())
        self.assertEqual([match.id for match in matches], ["capability-watchdog"])

    def test_inactive_subscription_delivers_nothing(self):
        parsed = projector.parse_subscription(subscription(active=False))
        matches = projector.matching_subscriptions([parsed], "platform.capability.changed.v1", event())
        self.assertEqual(matches, [])

    def test_non_matching_subject_or_type_delivers_nothing(self):
        parsed = projector.parse_subscription(subscription())
        self.assertEqual(
            projector.matching_subscriptions([parsed], "platform.adoption.changed.v1", event()),
            [],
        )
        self.assertEqual(
            projector.matching_subscriptions(
                [parsed],
                "platform.capability.changed.v1",
                event(type="platform.capability.other.v1"),
            ),
            [],
        )


class ProjectorDeliveryTests(unittest.TestCase):
    def test_hmac_headers_are_per_subscription_and_idempotent(self):
        parsed = projector.parse_subscription(subscription())
        body = json.dumps(event()).encode("utf-8")
        headers = projector.build_headers(parsed, event(), body, {"akv://agentarmy/subscriptions/capability-watchdog-hmac": "secret"})

        self.assertEqual(headers["Content-Type"], "application/cloudevents+json")
        self.assertEqual(headers["User-Agent"], "AgentArmy-Webhook-Projector/0.1")
        self.assertEqual(headers["X-AgentArmy-Capability"], "platform.messaging.update-system")
        self.assertEqual(headers["X-AgentArmy-Subscription-Id"], "capability-watchdog")
        self.assertEqual(headers["Idempotency-Key"], "urn:agentarmy:test#event-1")
        self.assertRegex(headers["X-AgentArmy-Delivery-Id"], r"^[0-9a-f]{64}$")
        self.assertIn("kid=watchdog-v1", headers["X-AgentArmy-Signature-256"])
        self.assertIn("sha256=", headers["X-AgentArmy-Signature-256"])
        self.assertNotIn("secret", json.dumps(headers))

    def test_unresolved_secret_ref_fails_closed(self):
        parsed = projector.parse_subscription(subscription())
        with self.assertRaisesRegex(projector.ConfigError, "unresolved secretRef"):
            projector.build_headers(parsed, event(), b"{}", {})

    def test_cloudflare_access_headers_resolve_from_secret_refs(self):
        parsed = projector.parse_subscription(
            subscription(
                sink={
                    "url": "https://subscriber.example.com/events",
                    "auth": {
                        "type": "cloudflare-access-service-token",
                        "clientIdSecretRef": "akv://agentarmy/cf/id",
                        "clientSecretSecretRef": "akv://agentarmy/cf/secret",
                    },
                }
            )
        )
        headers = projector.build_headers(
            parsed,
            event(),
            b"{}",
            {"akv://agentarmy/cf/id": "client-id", "akv://agentarmy/cf/secret": "client-secret"},
        )
        self.assertEqual(headers["CF-Access-Client-Id"], "client-id")
        self.assertEqual(headers["CF-Access-Client-Secret"], "client-secret")

    def test_deliver_subscription_classifies_success_and_retry(self):
        parsed = projector.parse_subscription(subscription())
        seen_requests = []

        async def handler(request: httpx.Request) -> httpx.Response:
            seen_requests.append(request)
            return httpx.Response(503)

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await projector.deliver_subscription(
                    client,
                    parsed,
                    event(),
                    b"{}",
                    {"akv://agentarmy/subscriptions/capability-watchdog-hmac": "secret"},
                )

        result = asyncio.run(run())
        self.assertFalse(result.delivered)
        self.assertTrue(result.retryable)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(seen_requests[0].headers["content-type"], "application/cloudevents+json")

    def test_sanitize_log_value_redacts_url_query_and_secret_shapes(self):
        raw = "https://subscriber.example.com/events?token=secret bearer abc.def akv://vault/path"
        redacted = projector.sanitize_log_value(raw)
        self.assertIn("https://subscriber.example.com/events", redacted)
        self.assertNotIn("token=secret", redacted)
        self.assertNotIn("abc.def", redacted)
        self.assertNotIn("akv://vault/path", redacted)


if __name__ == "__main__":
    unittest.main()
