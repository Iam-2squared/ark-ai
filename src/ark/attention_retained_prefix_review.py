"""Read-only, restart-bound prefix review for detached proactive attention.

This is a synthetic history comparison, not a durable clock, an append
authorization, a notification entitlement, or proof of an external event.
A caller must retain the prior history digest independently for any value.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import proactive_attention_preview as attention

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-attention-prefix-v1\0"
_PREVIEW = attention.preview_proactive_attention
_POLICY = attention.AttentionBudgetPolicy
_MARKER = attention.SyntheticSurfaceMarker
_PREVIEW_RESULT = attention.AttentionBudgetPreview
_RESULT_DENIALS = (
    "notification_authorized", "action_authorized",
    "trusted_clock_verified", "consent_verified",
)
_ORIGINAL_PREVIEW_DENIALS = tuple(vars(_PREVIEW_RESULT)[k] for k in _RESULT_DENIALS)


class AttentionPrefixRejected(ValueError):
    """Previous/current synthetic attention histories cannot be reconciled."""


@dataclass(frozen=True, slots=True)
class AttentionPrefixReview:
    classification: str
    retained_count: int
    observed_count: int
    appended_count: int
    retained_history_sha256: str
    observed_history_sha256: str
    evidence_sha256: str

    @property
    def append_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def clock_authenticated(self) -> bool:
        return False


_RESULT = AttentionPrefixReview
_OUTPUT_DENIALS = (
    "append_authorized", "notification_authorized",
    "automatic_replay_authorized", "clock_authenticated",
)
_ORIGINAL_OUTPUT_DENIALS = tuple(vars(_RESULT)[k] for k in _OUTPUT_DENIALS)


def review_attention_retained_prefix(
    policy: attention.AttentionBudgetPolicy,
    retained: tuple[attention.SyntheticSurfaceMarker, ...],
    observed: tuple[attention.SyntheticSurfaceMarker, ...],
    *,
    retained_history_sha256: str,
    retained_now_ms: int,
    observed_now_ms: int,
) -> AttentionPrefixReview:
    """Check independently retained digest and exact append-only fixture history.

    Both readings are caller-provided. Equal hashes cannot establish historical
    authorship; a successful outcome is only a local REVIEW, never permission.
    """
    def original_authorities() -> None:
        if (
            attention.preview_proactive_attention is not _PREVIEW
            or attention.AttentionBudgetPolicy is not _POLICY
            or attention.SyntheticSurfaceMarker is not _MARKER
            or attention.AttentionBudgetPreview is not _PREVIEW_RESULT
            or any(vars(_PREVIEW_RESULT).get(k) is not v
                   for k, v in zip(_RESULT_DENIALS, _ORIGINAL_PREVIEW_DENIALS, strict=True))
            or AttentionPrefixReview is not _RESULT
            or any(vars(_RESULT).get(k) is not v
                   for k, v in zip(_OUTPUT_DENIALS, _ORIGINAL_OUTPUT_DENIALS, strict=True))
        ):
            raise AttentionPrefixRejected("attention prefix authority changed")

    original_authorities()
    if (
        type(policy) is not _POLICY
        or type(retained) is not tuple
        or type(observed) is not tuple
        or len(observed) > 256 or len(retained) > len(observed)
        or any(type(x) is not _MARKER for x in retained + observed)
        or type(retained_history_sha256) is not str
        or _SHA.fullmatch(retained_history_sha256) is None
        or type(retained_now_ms) is not int
        or type(observed_now_ms) is not int
        or not 0 <= retained_now_ms <= observed_now_ms <= 2**63 - 1
    ):
        raise AttentionPrefixRejected("invalid bounded attention prefix inputs")

    policy_epoch = (
        policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
        policy.rolling_window_ms, policy.max_surfaced_per_window,
        policy.suppress_unchanged,
    )
    snapshots = tuple((
        row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
        row.observation_sha256, row.surfaced_at_ms,
    ) for row in retained + observed)
    objects = retained + observed
    retained_count, observed_count = len(retained), len(observed)

    def stable() -> None:
        original_authorities()
        if (
            type(policy) is not _POLICY
            or any(a is not b for a, b in zip(
                (policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
                 policy.rolling_window_ms, policy.max_surfaced_per_window,
                 policy.suppress_unchanged), policy_epoch, strict=True,
            ))
            or type(retained) is not tuple or type(observed) is not tuple
            or len(retained) != retained_count or len(observed) != observed_count
            or any(
                type(row) is not _MARKER or row is not original
                or any(a is not b for a, b in zip(
                    (row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
                     row.observation_sha256, row.surfaced_at_ms), fields, strict=True,
                ))
                for row, original, fields in zip(
                    retained + observed, objects, snapshots, strict=True,
                )
            )
        ):
            raise AttentionPrefixRejected("attention prefix evidence changed")

    stable()
    if snapshots[:retained_count] != snapshots[retained_count:retained_count * 2]:
        raise AttentionPrefixRejected("attention history is not append-only")
    # This comparison is value-exact AND the source carriers are checked at every
    # callback. Distinct copies of identical immutable markers are permitted.
    try:
        prior = _PREVIEW(
            policy, retained,
            occurrence_sha256="0" * 64,
            observation_sha256="0" * 64,
            observed_now_ms=retained_now_ms,
        )
        stable()
        current = _PREVIEW(
            policy, observed,
            occurrence_sha256="0" * 64,
            observation_sha256="0" * 64,
            observed_now_ms=observed_now_ms,
        )
        stable()
    except attention.AttentionPreviewRejected as exc:
        raise AttentionPrefixRejected("attention source preview rejected") from exc

    if type(prior) is not _PREVIEW_RESULT or type(current) is not _PREVIEW_RESULT:
        raise AttentionPrefixRejected("retained attention preview carrier changed")
    # Detached frozen preview fields can still be rewritten reflectively after
    # the original delegate returns. Retain each individual scalar, not just
    # the object identity, across JSON/hash callbacks and final construction.
    preview_rows = (prior, current)
    preview_epochs = tuple((
        report.disposition, report.next_review_at_ms,
        report.surfaced_count_in_window, report.history_sha256,
        report.review_sha256,
    ) for report in preview_rows)

    def stable_previews() -> None:
        stable()
        for report, fields in zip(preview_rows, preview_epochs, strict=True):
            if (
                type(report) is not _PREVIEW_RESULT
                or any(now is not first for now, first in zip((
                    report.disposition, report.next_review_at_ms,
                    report.surfaced_count_in_window, report.history_sha256,
                    report.review_sha256,
                ), fields, strict=True))
                or any(getattr(report, name) is not False
                       for name in _RESULT_DENIALS)
            ):
                raise AttentionPrefixRejected("retained attention preview changed")

    stable_previews()
    if prior.history_sha256 != retained_history_sha256:
        raise AttentionPrefixRejected("retained attention digest mismatch")

    encoded = json.dumps(
        (retained_history_sha256, current.history_sha256,
         retained_count, observed_count, retained_now_ms, observed_now_ms),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    stable_previews()
    evidence = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable_previews()
    outcome = _RESULT(
        "UNCHANGED" if retained_count == observed_count else "APPEND_ONLY",
        retained_count, observed_count, observed_count - retained_count,
        retained_history_sha256, current.history_sha256, evidence,
    )
    result_fields = (
        outcome.classification, outcome.retained_count, outcome.observed_count,
        outcome.appended_count, outcome.retained_history_sha256,
        outcome.observed_history_sha256, outcome.evidence_sha256,
    )
    for name in _OUTPUT_DENIALS:
        if getattr(outcome, name) is not False:
            raise AttentionPrefixRejected("attention prefix gained authority")
        stable_previews()
        if type(outcome) is not _RESULT or any(
            a is not b for a, b in zip(
                (outcome.classification, outcome.retained_count,
                 outcome.observed_count, outcome.appended_count,
                 outcome.retained_history_sha256,
                 outcome.observed_history_sha256, outcome.evidence_sha256),
                result_fields, strict=True,
            )
        ):
            raise AttentionPrefixRejected("attention prefix result changed")
    return outcome
