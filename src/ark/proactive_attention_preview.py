"""Detached proactive attention-budget preview; no notification or dispatch.

All scope IDs, clock readings and markers are caller-provided fixtures. The
history digest detects local changes only when independently retained; it is
not trusted-clock evidence, an external delivery receipt, or a permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_MS = 2**63 - 1
_DOMAIN = b"ARK-detached-proactive-attention-v1\0"
_MAX_MARKERS = 256


class AttentionPreviewRejected(ValueError):
    """An untrusted notice history/policy is malformed or has drifted."""


@dataclass(frozen=True, slots=True)
class AttentionBudgetPolicy:
    scope_sha256: str
    trigger_sha256: str
    cooldown_ms: int
    rolling_window_ms: int
    max_surfaced_per_window: int
    suppress_unchanged: bool


@dataclass(frozen=True, slots=True)
class SyntheticSurfaceMarker:
    scope_sha256: str
    trigger_sha256: str
    occurrence_sha256: str
    observation_sha256: str
    surfaced_at_ms: int


@dataclass(frozen=True, slots=True)
class AttentionBudgetPreview:
    disposition: str
    next_review_at_ms: int | None
    surfaced_count_in_window: int
    history_sha256: str
    review_sha256: str

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


_RESULT_TYPE = AttentionBudgetPreview
_DENIAL_NAMES = (
    "notification_authorized", "action_authorized",
    "trusted_clock_verified", "consent_verified",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT_TYPE)[key] for key in _DENIAL_NAMES)


def _assert_original_denials() -> None:
    if (
        AttentionBudgetPreview is not _RESULT_TYPE
        or any(
            vars(_RESULT_TYPE).get(key) is not expected
            for key, expected in zip(_DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise AttentionPreviewRejected("attention authority definition changed")


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _ms(value: object) -> bool:
    return type(value) is int and 0 <= value <= _MAX_MS


def preview_proactive_attention(
    policy: AttentionBudgetPolicy,
    history: tuple[SyntheticSurfaceMarker, ...],
    *,
    occurrence_sha256: str,
    observation_sha256: str,
    observed_now_ms: int,
) -> AttentionBudgetPreview:
    """Evaluate bounded synthetic attention only, without notifying anyone.

    History is ordered by strictly increasing surfaced-at timestamps. The
    rolling window is (now - window, now], with an exclusive lower boundary.
    A candidate marked REVIEW_ONLY still needs real notification consent,
    clock provenance, retention and delivery policy elsewhere.
    """
    _assert_original_denials()
    if (
        type(policy) is not AttentionBudgetPolicy
        or type(history) is not tuple or len(history) > _MAX_MARKERS
        or any(type(row) is not SyntheticSurfaceMarker for row in history)
        or not _sha(occurrence_sha256) or not _sha(observation_sha256)
        or not _ms(observed_now_ms)
    ):
        raise AttentionPreviewRejected("exact bounded synthetic attention inputs required")

    policy_fields = (
        policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
        policy.rolling_window_ms, policy.max_surfaced_per_window,
        policy.suppress_unchanged,
    )
    rows = tuple((
        row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
        row.observation_sha256, row.surfaced_at_ms,
    ) for row in history)
    originals = tuple(history)
    input_fields = (occurrence_sha256, observation_sha256, observed_now_ms)

    def stable() -> None:
        _assert_original_denials()
        if (
            type(policy) is not AttentionBudgetPolicy
            or any(now is not first for now, first in zip(
                (policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
                 policy.rolling_window_ms, policy.max_surfaced_per_window,
                 policy.suppress_unchanged), policy_fields, strict=True,
            ))
            or type(history) is not tuple
            or len(history) != len(originals)
            or any(
                row is not original
                or any(now is not first for now, first in zip(
                    (row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
                     row.observation_sha256, row.surfaced_at_ms),
                    fields, strict=True,
                ))
                for row, original, fields in zip(
                    history, originals, rows, strict=True,
                )
            )
            or any(now is not first for now, first in zip(
                (occurrence_sha256, observation_sha256, observed_now_ms),
                input_fields, strict=True,
            ))
        ):
            raise AttentionPreviewRejected("synthetic attention evidence changed")

    stable()
    scope, trigger, cooldown, window, limit, suppress = policy_fields
    if (
        not _sha(scope) or not _sha(trigger)
        or not _ms(cooldown) or cooldown < 1
        or not _ms(window) or window < 1
        or type(limit) is not int or not 1 <= limit <= _MAX_MARKERS
        or type(suppress) is not bool
    ):
        raise AttentionPreviewRejected("invalid bounded attention policy")

    previous_ms = -1
    seen: set[str] = set()
    for marker_scope, marker_trigger, occurrence, observation, at in rows:
        stable()
        if (
            marker_scope != scope or marker_trigger != trigger
            or not _sha(marker_scope) or not _sha(marker_trigger)
            or not _sha(occurrence) or not _sha(observation)
            or not _ms(at) or at <= previous_ms
            or at > observed_now_ms or occurrence in seen
        ):
            raise AttentionPreviewRejected("synthetic attention history incoherent")
        seen.add(occurrence)
        previous_ms = at
    stable()
    active = tuple(
        at for _, _, _, _, at in rows if at > observed_now_ms - window
    )
    if occurrence_sha256 in seen:
        disposition, next_at = "ALREADY_RECORDED", None
    elif suppress and rows and rows[-1][3] == observation_sha256:
        disposition, next_at = "UNCHANGED_SUPPRESSED", None
    elif rows and observed_now_ms - previous_ms < cooldown:
        disposition, next_at = "COOLDOWN_HOLD", previous_ms + cooldown
    elif len(active) >= limit:
        disposition, next_at = "WINDOW_BUDGET_HOLD", active[0] + window
    else:
        disposition, next_at = "REVIEW_ONLY", None
    if next_at is not None and not _ms(next_at):
        raise AttentionPreviewRejected("next attention review clock unrepresentable")
    payload = (policy_fields, rows)
    encoded = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    stable()
    history_digest = hashlib.sha256(_DOMAIN + b"history\0" + encoded).hexdigest()
    stable()
    review_bytes = json.dumps(
        (history_digest, input_fields, disposition, next_at, len(active)),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    stable()
    review_digest = hashlib.sha256(_DOMAIN + b"review\0" + review_bytes).hexdigest()
    stable()
    result = _RESULT_TYPE(
        disposition, next_at, len(active), history_digest, review_digest,
    )
    carriers = (
        result.disposition, result.next_review_at_ms,
        result.surfaced_count_in_window, result.history_sha256,
        result.review_sha256,
    )

    def stable_result() -> None:
        stable()
        if (
            type(result) is not _RESULT_TYPE
            or any(now is not first for now, first in zip(
                (result.disposition, result.next_review_at_ms,
                 result.surfaced_count_in_window, result.history_sha256,
                 result.review_sha256), carriers, strict=True,
            ))
        ):
            raise AttentionPreviewRejected("attention preview result changed")

    stable_result()
    for name in _DENIAL_NAMES:
        if getattr(result, name) is not False:
            raise AttentionPreviewRejected("attention preview gained authority")
        stable_result()
    return result
