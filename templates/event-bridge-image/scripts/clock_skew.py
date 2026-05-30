"""Cross-cluster clock-skew SLI for the event bus (ARC-ADR-038 §5).

On every bus receive, parse the temporal envelope's HLC from a CloudEvent and measure how
far the event's origin clock leads local wall time. Emit a structured NDJSON metric line to
stdout — the otel-collector / tail.mjs pipeline ingests it (ARC-ADR-010). No OTel SDK
dependency (honours the event-bridge's minimal shim list).

Sign: positive => origin clock ahead of local; negative => behind. Alert when |skew| exceeds
the link's bound (low-ms intra-region per ARC-ADR-038 §5; looser at the edge).
Mirrors the hub reference helper tools/temporal/hlc.py::skew_ms.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional


def parse_hlc_physical_ms(hlc: Optional[str]) -> Optional[int]:
    """Extract the physical-ms component from an HLC wire string '<ms>:<counter>'."""
    if not hlc:
        return None
    head = hlc.split(":", 1)[0].strip()
    try:
        return int(head)
    except ValueError:
        return None


def skew_ms(hlc_physical_ms: int, now_ms: Optional[int] = None) -> int:
    """How far the origin HLC's physical time leads local wall time (positive => ahead)."""
    local = now_ms if now_ms is not None else time.time_ns() // 1_000_000
    return hlc_physical_ms - local


def skew_record(event: dict[str, Any], now_ms: Optional[int] = None) -> Optional[dict[str, Any]]:
    """Build an NDJSON skew-metric record from a CloudEvent, or None if it carries no HLC.

    Reads the `hlc` extension attribute (the ARC-ADR-038 temporal envelope). Gracefully
    no-ops for legacy events that predate envelope stamping.
    """
    physical = parse_hlc_physical_ms(event.get("hlc"))
    if physical is None:
        return None
    return {
        "metric": "fleet.clock.skew_ms",
        "value": skew_ms(physical, now_ms),
        "source": event.get("source"),
        "type": event.get("type"),
        "hlc": event.get("hlc"),
    }


def emit_skew(event: dict[str, Any], now_ms: Optional[int] = None) -> Optional[dict[str, Any]]:
    """Compute and print the skew metric as one NDJSON line; returns the record (or None)."""
    record = skew_record(event, now_ms)
    if record is not None:
        print(json.dumps(record), flush=True)
    return record


def _selftest() -> None:
    rec = skew_record({"hlc": "1200:0", "source": "x", "type": "t"}, now_ms=1000)
    assert rec is not None and rec["value"] == 200, rec          # origin 200ms ahead
    assert parse_hlc_physical_ms("1500:7") == 1500               # counter component ignored
    assert skew_record({"source": "x"}, now_ms=1000) is None     # legacy event, no hlc → no-op
    assert skew_record({"hlc": "bogus"}, now_ms=1000) is None    # malformed hlc → no-op

    # Contract seam (ARC-ADR-038 §5): a real fleet.pin.recorded CloudEvent — exactly the shape
    # middle-core's PinCloudEvent.BuildRecordedJson emits — is read by this parser. Pins the
    # producer (middle-core) ↔ consumer (event-bridge) envelope agreement.
    pin_event = {
        "specversion": "1.0",
        "id": "abc123",
        "source": "urn:agentarmy:mc",
        "type": "fleet.pin.recorded",
        "time": "2026-05-30T04:00:00.0000000Z",
        "datacontenttype": "application/json",
        "data": {"content_hash": "abc123", "agent_id": "middle-core-runtime"},
        "hlc": "1748577600142:0",
    }
    pin_rec = skew_record(pin_event, now_ms=1748577600000)
    assert pin_rec is not None, pin_rec
    assert pin_rec["value"] == 142, pin_rec                       # 1748577600142 - 1748577600000
    assert pin_rec["type"] == "fleet.pin.recorded", pin_rec
    assert pin_rec["source"] == "urn:agentarmy:mc", pin_rec

    print("clock_skew.py self-test: OK")


if __name__ == "__main__":
    _selftest()
