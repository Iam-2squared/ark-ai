"""Disconnected coverage-to-attention review. No ASR, notices, or tools.

Joining caller-supplied SHA claims does not authenticate the sensor, transcript,
clock, user identity or retained review. A low-coverage gate can only HOLD,
never upgrade a deny-only upstream attention review to an authorization.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import offline_transcript_coverage as coverage_module
from . import proactive_attention_preview as attention_module

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-coverage-attention-v1\0"
_COVERAGE = coverage_module.OfflineTranscriptCoverage
_ATTENTION = attention_module.AttentionBudgetPreview
_POLICY = attention_module.AttentionBudgetPolicy
_MARKER = attention_module.SyntheticSurfaceMarker
_PREVIEW = attention_module.preview_proactive_attention
_COVERAGE_DENIAL_NAMES = coverage_module._DENIALS
_ATTENTION_DENIAL_NAMES = attention_module._DENIAL_NAMES
_COVERAGE_DENIALS = tuple(vars(_COVERAGE)[x] for x in _COVERAGE_DENIAL_NAMES)
_ATTENTION_DENIALS = tuple(vars(_ATTENTION)[x] for x in _ATTENTION_DENIAL_NAMES)
_COVERAGE_FIELDS = (
    "observation_sha256", "transcript_fingerprint", "audio_frames",
    "covered_frames", "leading_gap_frames", "interior_gap_frames",
    "trailing_gap_frames", "coverage_ppm", "uncovered_run_count",
    "longest_uncovered_run_frames", "coverage_sha256",
)
_ATTENTION_FIELDS = (
    "disposition", "next_review_at_ms", "surfaced_count_in_window",
    "history_sha256", "review_sha256",
)


class DetachedCoverageAttentionRejected(ValueError):
    """An untrusted detached join is malformed, unauthenticated, or altered."""


@dataclass(frozen=True, slots=True)
class DetachedCoverageAttention:
    disposition: str
    coverage_ppm: int
    required_coverage_ppm: int
    observation_sha256: str
    attention_review_sha256: str
    receipt_sha256: str

    @property
    def sensor_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT = DetachedCoverageAttention
_RESULT_DENIALS = (
    "sensor_authenticated", "consent_verified",
    "notification_authorized", "tool_execution_authorized",
)
_PINNED_RESULT_DENIALS = tuple(vars(_RESULT)[x] for x in _RESULT_DENIALS)


def review_detached_coverage_attention(
    coverage: coverage_module.OfflineTranscriptCoverage,
    policy: attention_module.AttentionBudgetPolicy,
    history: tuple[attention_module.SyntheticSurfaceMarker, ...],
    *,
    retained_coverage_sha256: str,
    occurrence_sha256: str,
    observed_now_ms: int,
    required_coverage_ppm: int,
) -> DetachedCoverageAttention:
    """Bind two synthetic receipts and apply a one-way low-coverage veto."""
    def originals() -> None:
        if (
            coverage_module.OfflineTranscriptCoverage is not _COVERAGE
            or attention_module.AttentionBudgetPreview is not _ATTENTION
            or attention_module.AttentionBudgetPolicy is not _POLICY
            or attention_module.SyntheticSurfaceMarker is not _MARKER
            or attention_module.preview_proactive_attention is not _PREVIEW
            or DetachedCoverageAttention is not _RESULT
            or any(vars(_COVERAGE).get(n) is not d for n, d in zip(
                _COVERAGE_DENIAL_NAMES, _COVERAGE_DENIALS, strict=True,
            ))
            or any(vars(_ATTENTION).get(n) is not d for n, d in zip(
                _ATTENTION_DENIAL_NAMES, _ATTENTION_DENIALS, strict=True,
            ))
            or any(vars(_RESULT).get(n) is not d for n, d in zip(
                _RESULT_DENIALS, _PINNED_RESULT_DENIALS, strict=True,
            ))
        ):
            raise DetachedCoverageAttentionRejected("detached join authority changed")

    originals()
    if (
        type(coverage) is not _COVERAGE
        or type(policy) is not _POLICY
        or type(history) is not tuple or len(history) > 256
        or any(type(x) is not _MARKER for x in history)
        or type(retained_coverage_sha256) is not str
        or _SHA.fullmatch(retained_coverage_sha256) is None
        or type(occurrence_sha256) is not str
        or _SHA.fullmatch(occurrence_sha256) is None
        or type(observed_now_ms) is not int
        or not 0 <= observed_now_ms <= 2**63 - 1
        or type(required_coverage_ppm) is not int
        or not 0 <= required_coverage_ppm <= 1_000_000
    ):
        raise DetachedCoverageAttentionRejected("invalid detached attention inputs")

    carrier = tuple(getattr(coverage, x) for x in _COVERAGE_FIELDS)
    policy_fields = (
        policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
        policy.rolling_window_ms, policy.max_surfaced_per_window,
        policy.suppress_unchanged,
    )
    markers = tuple((
        row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
        row.observation_sha256, row.surfaced_at_ms,
    ) for row in history)
    objects = tuple(history)

    def stable() -> None:
        originals()
        if (
            type(coverage) is not _COVERAGE
            or any(getattr(coverage, x) is not v for x, v in zip(
                _COVERAGE_FIELDS, carrier, strict=True,
            ))
            or type(policy) is not _POLICY
            or any(a is not b for a, b in zip(
                (policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
                 policy.rolling_window_ms, policy.max_surfaced_per_window,
                 policy.suppress_unchanged), policy_fields, strict=True,
            ))
            or type(history) is not tuple or len(history) != len(objects)
            or any(type(row) is not _MARKER or row is not before
                   or any(a is not b for a, b in zip(
                       (row.scope_sha256, row.trigger_sha256,
                        row.occurrence_sha256, row.observation_sha256,
                        row.surfaced_at_ms), data, strict=True,
                   )) for row, before, data in zip(
                       history, objects, markers, strict=True,
                   ))
        ):
            raise DetachedCoverageAttentionRejected("detached join evidence changed")

    stable()
    (observation, transcript, total, covered, lead, middle,
     tail, ppm, runs, longest, digest) = carrier
    if (
        not all(type(x) is str and _SHA.fullmatch(x) is not None
                for x in (observation, transcript, digest))
        or digest != retained_coverage_sha256
        or any(type(x) is not int for x in
               (total, covered, lead, middle, tail, ppm, runs, longest))
        or not 0 < total <= 2**63 - 1
        or not 0 <= covered <= total
        or min(lead, middle, tail, runs, longest) < 0
        or covered + lead + middle + tail != total
        or not 0 <= longest <= total
        or not 0 <= runs <= 65
        or ppm != covered * 1_000_000 // total
    ):
        raise DetachedCoverageAttentionRejected("invalid retained coverage accounting")

    for name in _COVERAGE_DENIAL_NAMES:
        if getattr(coverage, name) is not False:
            raise DetachedCoverageAttentionRejected("coverage gained authority")
        stable()
    try:
        report = _PREVIEW(
            policy, history, occurrence_sha256=occurrence_sha256,
            observation_sha256=observation, observed_now_ms=observed_now_ms,
        )
    except attention_module.AttentionPreviewRejected as exc:
        raise DetachedCoverageAttentionRejected("attention preview rejected") from exc
    stable()
    if type(report) is not _ATTENTION:
        raise DetachedCoverageAttentionRejected("attention report type changed")
    fields = tuple(getattr(report, name) for name in _ATTENTION_FIELDS)
    for name in _ATTENTION_DENIAL_NAMES:
        if getattr(report, name) is not False:
            raise DetachedCoverageAttentionRejected("attention gained authority")
        stable()
        if any(getattr(report, n) is not v for n, v in zip(
            _ATTENTION_FIELDS, fields, strict=True,
        )):
            raise DetachedCoverageAttentionRejected("attention report changed")

    # A duplicate occurrence remains classified as duplicate; a weak coverage
    # receipt can only make an otherwise eligible review more restrictive.
    disposition = fields[0]
    if disposition == "REVIEW_ONLY" and ppm < required_coverage_ppm:
        disposition = "INSUFFICIENT_COVERAGE_HOLD"
    payload = (
        digest, observation, occurrence_sha256, observed_now_ms,
        required_coverage_ppm, fields[4], disposition,
    )
    stable()
    evidence_sha = hashlib.sha256(
        _DOMAIN + json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        .encode("ascii")
    ).hexdigest()
    stable()
    result = _RESULT(
        disposition, ppm, required_coverage_ppm, observation, fields[4], evidence_sha,
    )
    output = (
        result.disposition, result.coverage_ppm, result.required_coverage_ppm,
        result.observation_sha256, result.attention_review_sha256,
        result.receipt_sha256,
    )
    for name in _RESULT_DENIALS:
        if getattr(result, name) is not False:
            raise DetachedCoverageAttentionRejected("join gained authority")
        stable()
        if type(result) is not _RESULT or any(a is not b for a, b in zip(
            (result.disposition, result.coverage_ppm,
             result.required_coverage_ppm, result.observation_sha256,
             result.attention_review_sha256, result.receipt_sha256),
            output, strict=True,
        )):
            raise DetachedCoverageAttentionRejected("join result changed")
    return result
