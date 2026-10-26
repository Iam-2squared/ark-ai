"""Disconnected privacy-minimal diagnostic ledger for fixed public codes.

Only allowlisted, non-payload codes can be serialized. Output is caller
asserted and does NOT attest owner, trusted time, consent, audit durability,
issuer or authorization. Never write private values through this API.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_COMPONENT = frozenset((
    "memory", "planner", "privacy", "registry", "tool", "startup", "observation",
))
_STAGE = frozenset(("ingress", "preflight", "commit", "recovery", "postcheck"))
_OUTCOME = frozenset(("rejected", "deferred", "reviewed"))
_REASON = frozenset((
    "invalid_type", "stale", "conflict", "quota", "quarantined", "missing_evidence",
    "untrusted_claim", "integrity_mismatch", "nonreplay_required",
))
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_EVENTS = 128
_MAX_SEQUENCE = 2**63 - 1
_DOMAIN = b"ARK-detached-private-diagnostics-v1\0"


class PrivateDiagnosticRejected(ValueError):
    """A diagnostic contains unsafe, unknown or discontinuous public codes."""


@dataclass(frozen=True, slots=True)
class PrivateDiagnosticEvent:
    sequence: int
    component: str
    stage: str
    outcome: str
    reason: str


@dataclass(frozen=True, slots=True)
class PrivateDiagnosticPreview:
    first_sequence: int
    last_sequence: int
    count: int
    final_sha256: str
    canonical_jsonl: str = field(repr=False)

    @property
    def trusted_audit_evidence(self) -> bool:
        return False

    @property
    def external_log_export_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


def render_private_diagnostic_ledger(
    events: tuple[PrivateDiagnosticEvent, ...],
    *,
    start_sequence: int,
    retained_anchor_sha256: str,
) -> PrivateDiagnosticPreview:
    """Return bounded deterministic JSONL containing ONLY fixed public codes.

    Caller-supplied anchor is not authenticated; caller must independently
    retain and compare it. No files, network calls or actual audit writes.
    """
    if (
        type(events) is not tuple or not 1 <= len(events) <= _MAX_EVENTS
        or any(type(event) is not PrivateDiagnosticEvent for event in events)
        or type(start_sequence) is not int
        or not 1 <= start_sequence <= _MAX_SEQUENCE
        or start_sequence > _MAX_SEQUENCE - len(events) + 1
        or type(retained_anchor_sha256) is not str
        or _SHA.fullmatch(retained_anchor_sha256) is None
    ):
        raise PrivateDiagnosticRejected("invalid diagnostic envelope")
    original = tuple(events)
    pins = tuple(
        (event, event.sequence, event.component, event.stage, event.outcome, event.reason)
        for event in original
    )

    def epoch() -> None:
        if len(events) != len(pins) or any(
            events[i] is not saved[0] or any(
                now is not before for now, before in zip(
                    (saved[0].sequence, saved[0].component, saved[0].stage,
                     saved[0].outcome, saved[0].reason), saved[1:], strict=True,
                )
            ) for i, saved in enumerate(pins)
        ):
            raise PrivateDiagnosticRejected("diagnostic carrier changed during review")

    epoch()
    chain = retained_anchor_sha256
    lines: list[str] = []
    for index, (event, seq, component, stage, outcome, reason) in enumerate(pins):
        epoch()
        if (
            type(seq) is not int or seq != start_sequence + index
            or type(component) is not str or component not in _COMPONENT
            or type(stage) is not str or stage not in _STAGE
            or type(outcome) is not str or outcome not in _OUTCOME
            or type(reason) is not str or reason not in _REASON
        ):
            raise PrivateDiagnosticRejected("unknown public code or sequence gap")
        data = [1, seq, component, stage, outcome, reason, chain]
        canonical = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        chain = hashlib.sha256(_DOMAIN + canonical.encode("ascii")).hexdigest()
        lines.append(json.dumps(
            {"v": 1, "seq": seq, "component": component, "stage": stage,
             "outcome": outcome, "reason": reason, "prior": data[-1], "sha256": chain},
            sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        ))
    epoch()
    serialized = "\n".join(lines) + "\n"
    if len(serialized.encode("ascii")) > 50_000:
        raise PrivateDiagnosticRejected("diagnostic output budget exceeded")
    epoch()
    return PrivateDiagnosticPreview(
        start_sequence, start_sequence + len(events) - 1, len(events), chain, serialized,
    )
