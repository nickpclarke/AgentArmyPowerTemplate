"""Hybrid Logical Clock (HLC) + canonical temporal envelope — reference implementation.

Governed by ARC-ADR-038 (Unified Process & Time Architecture). This is the *reference*
the fleet's clock seam is modeled on:

- middle-core swaps `SystemSerializationClock` for an `HlcSerializationClock` behind the
  existing `ISerializationClock` (RT5 PIN-F1) — C# port of this logic.
- backend-core / the runbook-orchestrator / event-bridge stamp the envelope on every
  CloudEvent and DBOS workflow step — Python, this module.

Why HLC and not "sync the clocks": wall clocks on separate containers always skew (NTP
gets ~ms, never 0). An HLC stays within NTP-distance of wall time *and* guarantees a
monotonic, causally-correct order across containers via a merge rule. NTP/chrony is the
physical baseline; the HLC is the ordering contract. See README.md.

Algorithm: Kulkarni et al., "Logical Physical Clocks" (2014). Stdlib only (ARC-ADR-031 D7
supply-chain minimalism).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional

# ── Design knobs (this is where your judgment shapes the clock's safety) ──────────────
# MAX_DRIFT_MS: how far the logical time may run ahead of this node's wall clock before we
# treat it as a fault. A remote node with a clock far in the future would otherwise drag
# our HLC forward indefinitely. Clamp protects causality from a single bad clock.
MAX_DRIFT_MS = 60_000  # 60s — tune to your NTP discipline (tighter once chrony is enforced)

# TIE_BREAK: when two events share the same physical ms, the counter orders them. The only
# real choice is what to do on overflow — here we let the counter grow (ints are unbounded
# in Python; the C# port should use int64 and roll the physical ms forward on overflow).


def _now_ms() -> int:
    """Physical time source. CLOCK_REALTIME in ms. The single seam to a test/fake clock."""
    return time.time_ns() // 1_000_000


@dataclass(order=True)
class Hlc:
    """A hybrid logical timestamp: (physical_ms, counter). Orderable; serializable."""

    physical_ms: int
    counter: int = 0

    def __str__(self) -> str:  # compact wire form, lexically sortable when zero-padded
        return f"{self.physical_ms}:{self.counter}"

    @classmethod
    def parse(cls, s: str) -> "Hlc":
        ms, _, c = s.partition(":")
        return cls(int(ms), int(c or 0))


class HybridLogicalClock:
    """Thread-safe HLC. Call `local()` to stamp a locally-originated event; call
    `update(remote)` when receiving an event carrying a remote HLC (the merge that
    propagates causality across containers)."""

    def __init__(self, now_ms=_now_ms, max_drift_ms: int = MAX_DRIFT_MS) -> None:
        self._now_ms = now_ms
        self._max_drift_ms = max_drift_ms
        self._last = Hlc(0, 0)
        self._lock = threading.Lock()
        self.last_skew_ms = 0  # observed skew on the most recent update() — export as the SLI

    def local(self) -> Hlc:
        """Stamp a locally-originated event. Monotonic: never returns a value <= the last."""
        with self._lock:
            pt = self._now_ms()
            last = self._last
            if pt > last.physical_ms:
                nxt = Hlc(pt, 0)
            else:
                # wall clock didn't advance (or went backwards) — advance the counter
                nxt = Hlc(last.physical_ms, last.counter + 1)
            self._last = nxt
            return nxt

    def update(self, remote: Hlc, max_drift_ms: Optional[int] = None) -> Hlc:
        """Merge a received remote HLC into ours and stamp the receive event.

        This is the heart of cross-container causal order: after `update`, our clock is
        >= both our previous time and the sender's time, so happens-before is preserved
        even when the two wall clocks disagree or events arrive out of order.

        `max_drift_ms` overrides the default bound for this one link — pass a looser value
        for the loose-clock edge (OmniDesk / W32Time) or a future cross-region gateway hop.
        """
        with self._lock:
            pt = self._now_ms()
            last = self._last
            bound = self._max_drift_ms if max_drift_ms is None else max_drift_ms
            self.last_skew_ms = remote.physical_ms - pt
            self._guard_drift(remote, pt, bound)
            new_phys = max(last.physical_ms, remote.physical_ms, pt)
            if new_phys == last.physical_ms == remote.physical_ms:
                counter = max(last.counter, remote.counter) + 1
            elif new_phys == last.physical_ms:
                counter = last.counter + 1
            elif new_phys == remote.physical_ms:
                counter = remote.counter + 1
            else:  # physical wall clock is ahead of both — fresh logical second
                counter = 0
            nxt = Hlc(new_phys, counter)
            self._last = nxt
            return nxt

    def _guard_drift(self, remote: Hlc, pt: int, bound: int) -> None:
        if remote.physical_ms - pt > bound:
            raise ClockDriftError(
                f"remote HLC {remote} is {remote.physical_ms - pt}ms ahead of local wall "
                f"clock (max {bound}ms for this link) — refusing to advance; check NTP/chrony"
            )


class ClockDriftError(RuntimeError):
    """Raised when a remote HLC is implausibly far ahead — a bad clock, not a fast one."""


def skew_ms(remote: Hlc, now_ms=_now_ms) -> int:
    """Observed clock skew (ms): how far a received HLC's physical time leads local wall
    time. Export this on every bus receive as the cross-cluster time-sync SLI
    (ARC-ADR-010); alert when it exceeds the tier's bound (low-ms intra-region, looser at
    the edge). Positive = remote ahead; negative = remote behind."""
    return remote.physical_ms - now_ms()


# ── Canonical temporal envelope (ARC-ADR-038) ────────────────────────────────────────
# Rides every CloudEvent (as extension attributes), lands on every PinnedElement, tags
# every DBOS workflow step. Conforms to temporal-envelope.schema.json.

@dataclass
class TemporalEnvelope:
    event_time: str           # ISO-8601 — when it happened at source (CloudEvents `time`)
    recorded_at: str          # ISO-8601 — transaction time (when the system recorded it)
    hlc: str                  # causal order across containers ("<ms>:<counter>")
    correlation_id: str       # root process-instance id — the saga key
    causation_id: str         # immediate parent event/step id
    valid_from: Optional[str] = None   # valid time (when the fact is true in the world)
    valid_to: Optional[str] = None
    processed_at: Optional[str] = None  # processing time (when this consumer handled it)
    extra: dict = field(default_factory=dict)

    # CloudEvents v1.0 extension attributes must be lowercase alphanumerics.
    _CE = {
        "event_time": "eventtime",
        "recorded_at": "recordedat",
        "hlc": "hlc",
        "correlation_id": "correlationid",
        "causation_id": "causationid",
        "valid_from": "validfrom",
        "valid_to": "validto",
        "processed_at": "processedat",
    }

    def to_cloudevent_extensions(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for attr, ce in self._CE.items():
            v = getattr(self, attr)
            if v is not None:
                out[ce] = v
        return out

    @classmethod
    def from_cloudevent(cls, ce: dict[str, Any]) -> "TemporalEnvelope":
        inv = {v: k for k, v in cls._CE.items()}
        kw = {inv[k]: v for k, v in ce.items() if k in inv}
        kw.setdefault("event_time", ce.get("time", ""))
        return cls(**kw)  # type: ignore[arg-type]


# ── Self-test (stdlib only) — `python hlc.py` ────────────────────────────────────────
def _selftest() -> None:
    # 1) local monotonicity even when wall clock is frozen
    frozen = HybridLogicalClock(now_ms=lambda: 1000)
    seq = [frozen.local() for _ in range(3)]
    assert seq == sorted(seq) and len(set(map(str, seq))) == 3, seq

    # 2) causal order survives a wall-clock inversion across two nodes
    a = HybridLogicalClock(now_ms=lambda: 5000)   # node A, clock ahead
    b = HybridLogicalClock(now_ms=lambda: 1000)   # node B, clock behind
    sent = a.local()                               # A emits at t=5000
    recv = b.update(sent)                          # B receives though its wall clock says 1000
    assert recv > sent, (sent, recv)               # B's stamp is causally after A's
    nxt = b.local()
    assert nxt > recv, (recv, nxt)                 # and B stays monotonic afterwards

    # 3) drift guard rejects an implausible future clock (region/link-aware bound)
    guarded = HybridLogicalClock(now_ms=lambda: 1000, max_drift_ms=10)
    try:
        guarded.update(Hlc(physical_ms=999_999, counter=0))
        raise AssertionError("expected ClockDriftError")
    except ClockDriftError:
        pass
    # a per-link looser bound (e.g. the OmniDesk edge leaf) lets the same skew through
    edge = HybridLogicalClock(now_ms=lambda: 1000, max_drift_ms=10)
    edge.update(Hlc(physical_ms=1200, counter=0), max_drift_ms=5000)  # +200ms tolerated on the edge link
    assert edge.last_skew_ms == 200, edge.last_skew_ms

    # 3b) skew SLI helper (export on every receive)
    assert skew_ms(Hlc(1500, 0), now_ms=lambda: 1000) == 500

    # 4) envelope round-trips through CloudEvents extension attributes
    env = TemporalEnvelope(
        event_time="2026-05-30T04:00:00Z", recorded_at="2026-05-30T04:00:01Z",
        hlc=str(sent), correlation_id="proc-1", causation_id="evt-0",
    )
    assert TemporalEnvelope.from_cloudevent(env.to_cloudevent_extensions()).hlc == str(sent)

    print("hlc.py self-test: OK")


if __name__ == "__main__":
    _selftest()
