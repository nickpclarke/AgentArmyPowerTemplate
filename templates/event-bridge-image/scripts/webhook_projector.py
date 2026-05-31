"""NATS-to-webhook projector for platform update subscriptions.

This mode realizes the AgentArmy adoption target for capability
``platform.messaging.update-system``: subscribe to the canonical platform update
message families on NATS JetStream, apply active subscription filters, and POST
matching CloudEvents to registered webhook sinks.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import json
import os
import re
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

try:
    import nats
except ImportError:  # pragma: no cover - unit tests do not need a broker client.
    nats = None


CAPABILITY_ID = "platform.messaging.update-system"
ALLOWED_FAMILIES = (
    "platform.capability",
    "platform.adoption",
    "platform.hvfs",
    "fleet.agent",
    "platform.security",
)
SECURITY_FAMILY = "platform.security"
SUBJECT_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SECRET_VALUE_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._-]+|gh[pousr]_[a-z0-9_]+|sk-[a-z0-9_-]+|"
    r"aws_secret_access_key\s*=\s*[^\s]+|client_secret\s*=\s*[^\s]+|akv://[^\s]+)"
)
URL_RE = re.compile(r"https?://[^\s\"']+")


class ConfigError(ValueError):
    """Raised when subscription configuration is unsafe or malformed."""


@dataclass(frozen=True)
class SinkAuth:
    type: str
    secret_ref: str | None = None
    key_id: str | None = None
    client_id_ref: str | None = None
    client_secret_ref: str | None = None


@dataclass(frozen=True)
class Sink:
    url: str
    auth: SinkAuth


@dataclass(frozen=True)
class Subscription:
    id: str
    active: bool
    subjects: tuple[str, ...]
    event_types: tuple[str, ...]
    sources: tuple[str, ...]
    data_equals: dict[str, Any]
    sink: Sink
    replayable: bool
    security_trusted: bool


@dataclass(frozen=True)
class DeliveryResult:
    subscription_id: str
    delivered: bool
    retryable: bool
    status_code: int | None = None


def sanitize_log_value(value: Any) -> str:
    """Redact URLs, query strings, and common token-shaped values."""

    text = str(value)
    text = URL_RE.sub(lambda m: redact_url(m.group(0)), text)
    text = SECRET_VALUE_RE.sub("[redacted]", text)
    return text


def redact_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return "[redacted-url]"
    host = parsed.hostname or "unknown"
    port = f":{parsed.port}" if parsed.port else ""
    return urlunparse((parsed.scheme, f"{host}{port}", parsed.path, "", "", ""))


def sink_host(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname or "unknown"


def sink_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def subject_family(subject: str) -> str | None:
    for family in ALLOWED_FAMILIES:
        if subject == family or subject.startswith(f"{family}."):
            return family
    return None


def validate_subject_pattern(pattern: str) -> None:
    if pattern in {"*", ">"}:
        raise ConfigError(f"subject pattern is too broad: {pattern}")

    tokens = pattern.split(".")
    if any(token == "" for token in tokens):
        raise ConfigError(f"subject pattern has an empty token: {pattern}")
    if ">" in tokens[:-1]:
        raise ConfigError(f"subject pattern has non-terminal > wildcard: {pattern}")
    for token in tokens:
        if token in {"*", ">"}:
            continue
        if not SUBJECT_TOKEN_RE.match(token):
            raise ConfigError(f"subject pattern has an invalid token: {pattern}")

    if len(tokens) < 3:
        raise ConfigError(f"subject pattern must include a message family: {pattern}")
    if tokens[0] == "platform" and tokens[1] in {"*", ">"}:
        raise ConfigError(f"subject pattern escapes platform family boundary: {pattern}")
    if tokens[0] == "fleet" and tokens[1] in {"*", ">"}:
        raise ConfigError(f"subject pattern escapes fleet family boundary: {pattern}")

    family = subject_family(pattern.replace(".*", ".x").replace(".>", ".x"))
    if family is None:
        raise ConfigError(f"subject pattern is outside platform update families: {pattern}")


def subject_matches(pattern: str, subject: str) -> bool:
    pattern_tokens = pattern.split(".")
    subject_tokens = subject.split(".")

    for index, token in enumerate(pattern_tokens):
        if token == ">":
            return True
        if index >= len(subject_tokens):
            return False
        if token == "*":
            continue
        if token != subject_tokens[index]:
            return False
    return len(pattern_tokens) == len(subject_tokens)


def is_private_literal_host(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def resolved_private_hosts(host: str) -> list[str]:
    if is_private_literal_host(host):
        return [host]
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except OSError:
        return []
    blocked: list[str] = []
    for info in infos:
        address = info[4][0]
        if is_private_literal_host(address):
            blocked.append(address)
    return blocked


def validate_sink_url(url: str, *, allow_local_http: bool = False, resolve_dns: bool = False) -> None:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        raise ConfigError("sink URL must not contain credentials")
    if not parsed.hostname:
        raise ConfigError("sink URL must include a host")
    host = parsed.hostname.lower()
    local_host = host in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https":
        if not (allow_local_http and parsed.scheme == "http" and local_host):
            raise ConfigError("active webhook sinks must use HTTPS")
    if host == "169.254.169.254" or is_private_literal_host(host):
        if not (allow_local_http and local_host):
            raise ConfigError("sink URL points to a blocked private or metadata address")
    if resolve_dns:
        blocked = resolved_private_hosts(host)
        if blocked and not (allow_local_http and local_host):
            raise ConfigError("sink host resolves to a blocked private address")


def read_secret_ref(secret_ref: str, secret_map: dict[str, str] | None = None) -> str:
    secret_map = secret_map or {}
    if secret_ref in secret_map:
        return secret_map[secret_ref]
    if secret_ref.startswith("env://"):
        env_name = secret_ref.removeprefix("env://")
        value = os.environ.get(env_name)
        if value:
            return value
    if secret_ref.startswith("file://"):
        return Path(secret_ref.removeprefix("file://")).read_text(encoding="utf-8").strip()
    raise ConfigError(f"unresolved secretRef: {sanitize_log_value(secret_ref)}")


def load_secret_map() -> dict[str, str]:
    raw = os.environ.get("PROJECTOR_SECRET_REFS_JSON", "")
    if not raw:
        return {}
    candidate = Path(raw)
    if candidate.exists():
        raw = candidate.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ConfigError("PROJECTOR_SECRET_REFS_JSON must be a JSON object of string refs to string values")
    return data


def subscription_secret_refs(subscription: Subscription) -> list[str]:
    auth = subscription.sink.auth
    if auth.type == "hmac-sha256":
        return [auth.secret_ref or ""]
    return [auth.client_id_ref or "", auth.client_secret_ref or ""]


def validate_active_secret_refs(subscriptions: list[Subscription], secret_map: dict[str, str]) -> None:
    for subscription in subscriptions:
        if not subscription.active:
            continue
        for secret_ref in subscription_secret_refs(subscription):
            read_secret_ref(secret_ref, secret_map)


def parse_auth(raw: dict[str, Any]) -> SinkAuth:
    auth_type = raw.get("type")
    if auth_type == "hmac-sha256":
        secret_ref = raw.get("secretRef")
        if not isinstance(secret_ref, str) or not secret_ref:
            raise ConfigError("hmac-sha256 auth requires secretRef")
        key_id = raw.get("keyId")
        if key_id is not None and not isinstance(key_id, str):
            raise ConfigError("hmac-sha256 keyId must be a string")
        return SinkAuth(type=auth_type, secret_ref=secret_ref, key_id=key_id)
    if auth_type == "cloudflare-access-service-token":
        client_id_ref = raw.get("clientIdSecretRef")
        client_secret_ref = raw.get("clientSecretSecretRef")
        if not isinstance(client_id_ref, str) or not isinstance(client_secret_ref, str):
            raise ConfigError("Cloudflare Access auth requires clientIdSecretRef and clientSecretSecretRef")
        return SinkAuth(type=auth_type, client_id_ref=client_id_ref, client_secret_ref=client_secret_ref)
    raise ConfigError("webhook sink auth must be hmac-sha256 or cloudflare-access-service-token")


def parse_subscription(raw: dict[str, Any], *, allow_local_http: bool = False, resolve_dns: bool = False) -> Subscription:
    sub_id = raw.get("id")
    if not isinstance(sub_id, str) or not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,127}$", sub_id):
        raise ConfigError("subscription id must be 3-128 safe characters")

    subjects = raw.get("subjects")
    if not isinstance(subjects, list) or not subjects or not all(isinstance(s, str) for s in subjects):
        raise ConfigError(f"subscription {sub_id} requires subjects")
    for subject in subjects:
        validate_subject_pattern(subject)

    filters = raw.get("filters", {})
    if not isinstance(filters, dict):
        raise ConfigError(f"subscription {sub_id} filters must be an object")
    event_types = filters.get("eventTypes", [])
    sources = filters.get("sources", [])
    data_equals = filters.get("dataEquals", {})
    if not isinstance(event_types, list) or not all(isinstance(v, str) for v in event_types):
        raise ConfigError(f"subscription {sub_id} eventTypes must be strings")
    if not isinstance(sources, list) or not all(isinstance(v, str) for v in sources):
        raise ConfigError(f"subscription {sub_id} sources must be strings")
    if not isinstance(data_equals, dict):
        raise ConfigError(f"subscription {sub_id} dataEquals must be an object")

    sink_raw = raw.get("sink")
    if not isinstance(sink_raw, dict):
        raise ConfigError(f"subscription {sub_id} requires a sink")
    sink_url = sink_raw.get("url")
    if not isinstance(sink_url, str):
        raise ConfigError(f"subscription {sub_id} sink.url must be a string")
    active = bool(raw.get("active", False))
    if active:
        validate_sink_url(sink_url, allow_local_http=allow_local_http, resolve_dns=resolve_dns)
    auth_raw = sink_raw.get("auth")
    if not isinstance(auth_raw, dict):
        raise ConfigError(f"subscription {sub_id} sink.auth is required")
    auth = parse_auth(auth_raw)

    subscription = Subscription(
        id=sub_id,
        active=active,
        subjects=tuple(subjects),
        event_types=tuple(event_types),
        sources=tuple(sources),
        data_equals=data_equals,
        sink=Sink(url=sink_url, auth=auth),
        replayable=bool(raw.get("replayable", False)),
        security_trusted=bool(raw.get("securityTrusted", False)),
    )
    validate_security_subscription(subscription)
    return subscription


def validate_security_subscription(subscription: Subscription) -> None:
    touches_security = any(subject_family(subject.replace(".>", ".x").replace(".*", ".x")) == SECURITY_FAMILY for subject in subscription.subjects)
    if not touches_security:
        return
    if not subscription.security_trusted:
        raise ConfigError(f"subscription {subscription.id} must be securityTrusted for platform.security.*")
    if not subscription.replayable:
        raise ConfigError(f"subscription {subscription.id} must be replayable for platform.security.*")
    if subscription.sink.auth.type == "hmac-sha256":
        refs = [subscription.sink.auth.secret_ref]
    else:
        refs = [subscription.sink.auth.client_id_ref, subscription.sink.auth.client_secret_ref]
    if not all(ref and ref.startswith("akv://") for ref in refs):
        raise ConfigError(f"subscription {subscription.id} must use akv:// secret refs for platform.security.*")


def load_config(path: str, *, allow_local_http: bool = False, resolve_dns: bool = False) -> list[Subscription]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("capabilityId") != CAPABILITY_ID:
        raise ConfigError(f"capabilityId must be {CAPABILITY_ID}")
    subscriptions = raw.get("subscriptions")
    if not isinstance(subscriptions, list):
        raise ConfigError("subscriptions must be a list")
    parsed = [
        parse_subscription(item, allow_local_http=allow_local_http, resolve_dns=resolve_dns)
        for item in subscriptions
        if isinstance(item, dict)
    ]
    if len(parsed) != len(subscriptions):
        raise ConfigError("each subscription must be an object")
    return parsed


def event_matches(subscription: Subscription, subject: str, event: dict[str, Any]) -> bool:
    if not subscription.active:
        return False
    if not any(subject_matches(pattern, subject) for pattern in subscription.subjects):
        return False
    if subscription.event_types and event.get("type") not in subscription.event_types:
        return False
    if subscription.sources and event.get("source") not in subscription.sources:
        return False
    data = event.get("data", {})
    if not isinstance(data, dict):
        return False if subscription.data_equals else True
    for key, expected in subscription.data_equals.items():
        if data.get(key) != expected:
            return False
    return True


def matching_subscriptions(subscriptions: list[Subscription], subject: str, event: dict[str, Any]) -> list[Subscription]:
    return [subscription for subscription in subscriptions if event_matches(subscription, subject, event)]


def make_idempotency_key(event: dict[str, Any]) -> str:
    return f"{event.get('source', 'unknown')}#{event.get('id', 'unknown')}"


def make_delivery_id(subscription: Subscription, event: dict[str, Any]) -> str:
    raw = f"{subscription.id}:{event.get('source', '')}:{event.get('id', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_headers(
    subscription: Subscription,
    event: dict[str, Any],
    body: bytes,
    secret_map: dict[str, str] | None = None,
    *,
    attempt: int = 1,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/cloudevents+json",
        "User-Agent": "AgentArmy-Webhook-Projector/0.1",
        "Idempotency-Key": make_idempotency_key(event),
        "X-AgentArmy-Capability": CAPABILITY_ID,
        "X-AgentArmy-Subscription-Id": subscription.id,
        "X-AgentArmy-Delivery-Id": make_delivery_id(subscription, event),
        "X-AgentArmy-Attempt": str(attempt),
    }
    if event.get("id"):
        headers["ce-id"] = str(event["id"])
    if event.get("type"):
        headers["ce-type"] = str(event["type"])
    if event.get("source"):
        headers["ce-source"] = str(event["source"])

    auth = subscription.sink.auth
    if auth.type == "hmac-sha256":
        secret = read_secret_ref(auth.secret_ref or "", secret_map)
        timestamp = str(int(time.time()))
        signature_payload = timestamp.encode("utf-8") + b"." + body
        signature = hmac.new(secret.encode("utf-8"), signature_payload, hashlib.sha256).hexdigest()
        headers["X-AgentArmy-Timestamp"] = timestamp
        key_id = auth.key_id or sink_url_hash(subscription.sink.url)
        headers["X-AgentArmy-Signature-256"] = f"t={timestamp},kid={key_id},sha256={signature}"
    elif auth.type == "cloudflare-access-service-token":
        headers["CF-Access-Client-Id"] = read_secret_ref(auth.client_id_ref or "", secret_map)
        headers["CF-Access-Client-Secret"] = read_secret_ref(auth.client_secret_ref or "", secret_map)
    return headers


async def deliver_subscription(
    client: httpx.AsyncClient,
    subscription: Subscription,
    event: dict[str, Any],
    body: bytes,
    secret_map: dict[str, str] | None = None,
) -> DeliveryResult:
    headers = build_headers(subscription, event, body, secret_map)
    try:
        response = await client.post(subscription.sink.url, content=body, headers=headers)
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        print(
            json.dumps(
                {
                    "event": "platform.webhook.delivery_failed",
                    "subscription": subscription.id,
                    "sinkHost": sink_host(subscription.sink.url),
                    "sinkUrlHash": sink_url_hash(subscription.sink.url),
                    "error": sanitize_log_value(exc),
                    "retryable": True,
                }
            ),
            flush=True,
        )
        return DeliveryResult(subscription.id, delivered=False, retryable=True)

    delivered = 200 <= response.status_code < 300
    retryable = response.status_code >= 500 or response.status_code == 429
    print(
        json.dumps(
            {
                "event": "platform.webhook.delivered" if delivered else "platform.webhook.delivery_rejected",
                "subscription": subscription.id,
                "sinkHost": sink_host(subscription.sink.url),
                "sinkUrlHash": sink_url_hash(subscription.sink.url),
                "status": response.status_code,
                "retryable": retryable,
            }
        ),
        flush=True,
    )
    return DeliveryResult(subscription.id, delivered=delivered, retryable=retryable, status_code=response.status_code)


async def handle_message(msg: Any, subscriptions: list[Subscription], client: httpx.AsyncClient, secret_map: dict[str, str]) -> None:
    subject = getattr(msg, "subject", "")
    try:
        event = json.loads(msg.data)
    except json.JSONDecodeError:
        await msg.ack()
        return

    matches = matching_subscriptions(subscriptions, subject, event)
    if not matches:
        await msg.ack()
        return

    body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
    results = [await deliver_subscription(client, subscription, event, body, secret_map) for subscription in matches]
    if all(result.delivered or not result.retryable for result in results):
        await msg.ack()
    else:
        await msg.nak(delay=5)


def unique_subjects(subscriptions: list[Subscription]) -> list[str]:
    subjects: list[str] = []
    for subscription in subscriptions:
        for subject in subscription.subjects:
            if subscription.active and subject not in subjects:
                subjects.append(subject)
    return subjects


async def consume_subject(js: Any, subject: str, durable_prefix: str, subscriptions: list[Subscription], secret_map: dict[str, str]) -> None:
    durable = f"{durable_prefix}-{hashlib.sha256(subject.encode('utf-8')).hexdigest()[:10]}"
    sub = await js.subscribe(subject, durable=durable, manual_ack=True)
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                msg = await sub.next_msg(timeout=30)
            except Exception:
                continue
            await handle_message(msg, subscriptions, client, secret_map)


async def main() -> None:
    if nats is None:
        print("nats-py is required for project-webhooks mode", file=sys.stderr)
        sys.exit(2)
    config_path = os.environ.get("SUBSCRIPTIONS_FILE", "/etc/agentarmy/platform-update-subscriptions.json")
    allow_local_http = os.environ.get("PROJECTOR_ALLOW_LOCAL_HTTP", "0") == "1"
    resolve_dns = os.environ.get("PROJECTOR_VALIDATE_DNS", "0") == "1"
    subscriptions = load_config(config_path, allow_local_http=allow_local_http, resolve_dns=resolve_dns)
    secret_map = load_secret_map()
    if os.environ.get("PROJECTOR_VALIDATE_SECRETS_ON_START", "1") != "0":
        validate_active_secret_refs(subscriptions, secret_map)
    subjects = unique_subjects(subscriptions)
    if not subjects:
        print("projector has no active subscription subjects", file=sys.stderr)
        sys.exit(2)

    nats_url = os.environ.get("NATS_URL", "nats://nats:4222")
    durable_prefix = os.environ.get("DURABLE_NAME", "platform-update-webhook-projector")
    print(
        json.dumps(
            {
                "event": "platform.webhook.projector_started",
                "capabilityId": CAPABILITY_ID,
                "nats": sanitize_log_value(nats_url),
                "subjects": subjects,
                "subscriptions": [subscription.id for subscription in subscriptions if subscription.active],
            }
        ),
        flush=True,
    )
    nc = await nats.connect(nats_url)
    js = nc.jetstream()
    await asyncio.gather(
        *(consume_subject(js, subject, durable_prefix, subscriptions, secret_map) for subject in subjects)
    )


if __name__ == "__main__":
    asyncio.run(main())
