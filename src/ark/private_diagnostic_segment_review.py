"""Bounded read-only review of multiple retained public diagnostic segments.

This module connects already reviewed detached JSONL segment verification
without storing private data. Every anchor, length and tip is CALLER asserted;
matching chains are not authenticated audit, proof of user consent, a trusted
clock, file custody, cleanup permission, or tool execution authority.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import private_diagnostic_ledger_verify as verifier

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_SEGMENTS = 8
_MAX_EVENTS = 128
_MAX_BYTES = 50_000
_MAX_SEQUENCE = 2**63 - 1
_ORIGINAL_SHA = _SHA
_ORIGINAL_LIMITS = (_MAX_SEGMENTS, _MAX_EVENTS, _MAX_BYTES, _MAX_SEQUENCE)
_ORIGINAL_VERIFIER_MODULE = verifier
_ORIGINAL_VERIFY = verifier.verify_private_diagnostic_jsonl


class RetainedDiagnosticChainRejected(ValueError):
    """Detached public-only segment chain or retained envelope is inconsistent."""


@dataclass(frozen=True, slots=True)
class RetainedDiagnosticSegment:
    first_sequence: int
    count: int
    anchor_sha256: str
    tip_sha256: str
    canonical_jsonl: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class RetainedDiagnosticChainReview:
    first_sequence: int
    last_sequence: int
    count: int
    segment_count: int
    final_sha256: str

    @property
    def audit_authenticated(self) -> bool:
        return False

    @property
    def cleanup_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False

    @property
    def private_data_export_authorized(self) -> bool:
        return False


_SEGMENT_TYPE = RetainedDiagnosticSegment
_RESULT_TYPE = RetainedDiagnosticChainReview
_SEGMENT_FIELDS = (
    "first_sequence", "count", "anchor_sha256", "tip_sha256", "canonical_jsonl",
)
_RESULT_FIELDS = (
    "first_sequence", "last_sequence", "count", "segment_count", "final_sha256",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_DENIALS = (
    "audit_authenticated", "cleanup_authorized",
    "tool_execution_authorized", "private_data_export_authorized",
)
_ORIGINAL_SEGMENT_FIELDS = tuple(
    vars(_SEGMENT_TYPE).get(name) for name in (*_SEGMENT_FIELDS, *_HOOKS)
)
_ORIGINAL_RESULT_FIELDS = tuple(
    vars(_RESULT_TYPE).get(name)
    for name in (*_RESULT_FIELDS, *_HOOKS, *_DENIALS)
)


def _protocol() -> None:
    # Check class descriptors and the verifier callback BEFORE a payload or
    # retained tip is read. This is a local error fence, not a Python sandbox.
    if (
        RetainedDiagnosticSegment is not _SEGMENT_TYPE
        or RetainedDiagnosticChainReview is not _RESULT_TYPE
        or verifier is not _ORIGINAL_VERIFIER_MODULE
        or verifier.verify_private_diagnostic_jsonl is not _ORIGINAL_VERIFY
        or _SHA is not _ORIGINAL_SHA
        or any(type(n) is not int for n in (
            _MAX_SEGMENTS, _MAX_EVENTS, _MAX_BYTES, _MAX_SEQUENCE,
        ))
        or (_MAX_SEGMENTS, _MAX_EVENTS, _MAX_BYTES, _MAX_SEQUENCE)
        != _ORIGINAL_LIMITS
        or any(
            vars(_SEGMENT_TYPE).get(name) is not original
            for name, original in zip(
                (*_SEGMENT_FIELDS, *_HOOKS), _ORIGINAL_SEGMENT_FIELDS,
                strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                (*_RESULT_FIELDS, *_HOOKS, *_DENIALS),
                _ORIGINAL_RESULT_FIELDS, strict=True,
            )
        )
    ):
        raise RetainedDiagnosticChainRejected("diagnostic segment review protocol changed")


def verify_retained_diagnostic_segments(
    segments: tuple[RetainedDiagnosticSegment, ...],
    *,
    expected_start_sequence: int,
    expected_count: int,
    retained_anchor_sha256: str,
    expected_final_sha256: str,
) -> RetainedDiagnosticChainReview:
    """Verify a bounded, gap-free series against separately held scalar claims.

    A whole-series expected count and tip prevent a suffix from silently
    disappearing when its metadata are retained independently. An attacker
    who can rewrite both log and every retained scalar can forge this proof.
    No filesystem or actual audit/executor operation is performed.
    """
    _protocol()
    if (
        type(segments) is not tuple
        or not 1 <= len(segments) <= _MAX_SEGMENTS
        or any(type(segment) is not _SEGMENT_TYPE for segment in segments)
        or type(expected_start_sequence) is not int
        or not 1 <= expected_start_sequence <= _MAX_SEQUENCE
        or type(expected_count) is not int
        or not 1 <= expected_count <= _MAX_EVENTS
        or expected_start_sequence > _MAX_SEQUENCE - expected_count + 1
        or type(retained_anchor_sha256) is not str
        or _SHA.fullmatch(retained_anchor_sha256) is None
        or type(expected_final_sha256) is not str
        or _SHA.fullmatch(expected_final_sha256) is None
    ):
        raise RetainedDiagnosticChainRejected("invalid retained segment envelope")

    # Validate *all* metadata before handing any JSONL bytes to the verifier.
    # Never deserialize unknown private fields in this coordinator.
    current_sequence = expected_start_sequence
    current_anchor = retained_anchor_sha256
    total = 0
    total_bytes = 0
    snapshots: list[tuple[RetainedDiagnosticSegment, str, int, int, str, str]] = []
    for segment in segments:
        _protocol()
        start, count, anchor, tip, payload = (
            segment.first_sequence, segment.count, segment.anchor_sha256,
            segment.tip_sha256, segment.canonical_jsonl,
        )
        if (
            type(start) is not int
            or type(count) is not int
            or not 1 <= count <= _MAX_EVENTS
            or start != current_sequence
            or type(anchor) is not str or anchor != current_anchor
            or type(tip) is not str or _SHA.fullmatch(tip) is None
            or type(payload) is not str
            or not 1 <= len(payload) <= _MAX_BYTES
            or current_sequence > _MAX_SEQUENCE - count + 1
        ):
            raise RetainedDiagnosticChainRejected("diagnostic segment continuity invalid")
        total += count
        total_bytes += len(payload)
        if total > expected_count or total_bytes > _MAX_BYTES:
            raise RetainedDiagnosticChainRejected("diagnostic segment budget invalid")
        snapshots.append((segment, payload, start, count, anchor, tip))
        current_sequence += count
        current_anchor = tip
    if total != expected_count or current_anchor != expected_final_sha256:
        raise RetainedDiagnosticChainRejected("retained diagnostic series mismatch")

    # A verifier may invoke reentrant synthetic callbacks. Checking only the
    # current segment lets a callback rewrite an earlier, already-verified
    # segment while the coordinator returns a stale whole-series receipt.
    # Retain exact carrier identities, not merely equal-valued metadata.
    def stable_segments() -> None:
        _protocol()
        if len(segments) != len(snapshots) or any(
            segments[index] is not saved[0]
            or type(saved[0]) is not _SEGMENT_TYPE
            or any(
                now is not retained
                for now, retained in zip(
                    (
                        saved[0].canonical_jsonl, saved[0].first_sequence,
                        saved[0].count, saved[0].anchor_sha256,
                        saved[0].tip_sha256,
                    ),
                    saved[1:], strict=True,
                )
            )
            for index, saved in enumerate(snapshots)
        ):
            raise RetainedDiagnosticChainRejected(
                "diagnostic segment carrier changed during review"
            )

    stable_segments()
    for _segment, payload, start, count, anchor, tip in snapshots:
        stable_segments()
        try:
            evidence = verifier.verify_private_diagnostic_jsonl(
                payload, retained_anchor_sha256=anchor,
                expected_start_sequence=start, expected_count=count,
                expected_final_sha256=tip,
            )
        except verifier.PrivateDiagnosticVerificationRejected:
            raise RetainedDiagnosticChainRejected(
                "diagnostic segment verification failed"
            ) from None
        stable_segments()
        if (
            type(evidence) is not verifier.PrivateDiagnosticVerification
            or evidence.first_sequence != start
            or evidence.count != count
            or evidence.last_sequence != start + count - 1
            or evidence.final_sha256 != tip
            or any(
                getattr(evidence, name) is not False
                for name in _DENIALS
            )
        ):
            raise RetainedDiagnosticChainRejected(
                "diagnostic verification gained authority or changed"
            )
        stable_segments()

    stable_segments()
    result = RetainedDiagnosticChainReview(
        expected_start_sequence, current_sequence - 1, expected_count,
        len(segments), current_anchor,
    )
    stable_segments()
    # The final denied-authority properties are callback boundaries. A getter
    # may return False while rewriting an already checked result field, even
    # to an equal-valued but different object. Pin all original field objects
    # before the first denial and check them again after EVERY getter.
    result_fields = tuple(getattr(result, name) for name in _RESULT_FIELDS)

    def stable_result() -> None:
        _protocol()
        if (
            type(result) is not _RESULT_TYPE
            or any(
                getattr(result, name) is not original
                for name, original in zip(_RESULT_FIELDS, result_fields, strict=True)
            )
            or result.first_sequence != expected_start_sequence
            or result.last_sequence != current_sequence - 1
            or result.count != expected_count
            or result.segment_count != len(segments)
            or result.final_sha256 != current_anchor
        ):
            raise RetainedDiagnosticChainRejected(
                "diagnostic review result changed during authority checks"
            )

    stable_result()
    for name in _DENIALS:
        stable_segments()
        stable_result()
        if getattr(result, name) is not False:
            raise RetainedDiagnosticChainRejected("diagnostic review authority changed")
        stable_result()
        stable_segments()
    stable_result()
    stable_segments()
    return result
