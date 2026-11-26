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
_MAX_OUTPUT_BYTES = 50_000


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



# Import-time pins are deny-only guards against accidentally rebound
# same-process fixture helpers. They do not sandbox hostile Python code.
_EVENT_TYPE = PrivateDiagnosticEvent
_PREVIEW_TYPE = PrivateDiagnosticPreview
_EVENT_ATTRS = ("sequence", "component", "stage", "outcome", "reason")
_PREVIEW_ATTRS = ("first_sequence", "last_sequence", "count", "final_sha256", "canonical_jsonl")
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_DENIALS = ("trusted_audit_evidence", "external_log_export_authorized", "action_authorized")
_EVENT_ORIGINAL = tuple(vars(_EVENT_TYPE).get(n) for n in (*_EVENT_ATTRS, *_HOOKS))
_PREVIEW_ORIGINAL = tuple(vars(_PREVIEW_TYPE).get(n) for n in (*_PREVIEW_ATTRS, *_HOOKS, *_DENIALS))
_ORIGINAL_JSON = json
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_SHA = _SHA
_ORIGINAL_COMPONENT = _COMPONENT
_ORIGINAL_STAGE = _STAGE
_ORIGINAL_OUTCOME = _OUTCOME
_ORIGINAL_REASON = _REASON
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_EVENTS = _MAX_EVENTS
_ORIGINAL_MAX_SEQUENCE = _MAX_SEQUENCE
_ORIGINAL_MAX_OUTPUT_BYTES = _MAX_OUTPUT_BYTES


def _require_original_diagnostic_protocol() -> None:
    # Run before reading any event fields, anchor, or making a codec call.
    if (
        PrivateDiagnosticEvent is not _EVENT_TYPE
        or PrivateDiagnosticPreview is not _PREVIEW_TYPE
        or any(vars(_EVENT_TYPE).get(n) is not original for n, original in zip(
            (*_EVENT_ATTRS, *_HOOKS), _EVENT_ORIGINAL, strict=True,
        ))
        or any(vars(_PREVIEW_TYPE).get(n) is not original for n, original in zip(
            (*_PREVIEW_ATTRS, *_HOOKS, *_DENIALS), _PREVIEW_ORIGINAL, strict=True,
        ))
        or json is not _ORIGINAL_JSON
        or hashlib is not _ORIGINAL_HASHLIB
        or json.dumps is not _ORIGINAL_DUMPS
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or _SHA is not _ORIGINAL_SHA
        or _COMPONENT is not _ORIGINAL_COMPONENT
        or _STAGE is not _ORIGINAL_STAGE
        or _OUTCOME is not _ORIGINAL_OUTCOME
        or _REASON is not _ORIGINAL_REASON
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or type(_MAX_EVENTS) is not int
        or _MAX_EVENTS != _ORIGINAL_MAX_EVENTS
        or type(_MAX_SEQUENCE) is not int
        or _MAX_SEQUENCE != _ORIGINAL_MAX_SEQUENCE
        or type(_MAX_OUTPUT_BYTES) is not int
        or _MAX_OUTPUT_BYTES != _ORIGINAL_MAX_OUTPUT_BYTES
    ):
        raise PrivateDiagnosticRejected("diagnostic protocol or denial descriptor changed")


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
    _require_original_diagnostic_protocol()
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
        _require_original_diagnostic_protocol()
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
    for index, (_event, seq, component, stage, outcome, reason) in enumerate(pins):
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
    if len(serialized.encode("ascii")) > _MAX_OUTPUT_BYTES:
        raise PrivateDiagnosticRejected("diagnostic output budget exceeded")
    epoch()
    preview = PrivateDiagnosticPreview(
        start_sequence, start_sequence + len(events) - 1, len(events), chain, serialized,
    )
    epoch()
    if (
        type(preview) is not _PREVIEW_TYPE
        or preview.first_sequence != start_sequence
        or preview.last_sequence != start_sequence + len(events) - 1
        or preview.count != len(events)
        or preview.final_sha256 != chain
        or preview.canonical_jsonl != serialized
    ):
        raise PrivateDiagnosticRejected("diagnostic preview carrier changed")
    for denial in _DENIALS:
        epoch()
        if getattr(preview, denial) is not False:
            raise PrivateDiagnosticRejected("diagnostic gained forbidden authority")
        epoch()
    return preview
