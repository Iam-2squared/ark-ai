"""Read-only freshness recheck of previously reviewed observation lineage.

Both the cached witness and its clocks/source digests are unauthenticated
local fixture data. A match is not consent, media-capture provenance, external
disclosure authority, notification authority or ToolBackend permission.
"""

from __future__ import annotations

from dataclasses import dataclass

from .observation_lineage_review import (
    SyntheticObservationLineageWitness,
    review_synthetic_observation_lineage,
)
from .observations import ObservationEnvelope

_MAX = 2**63 - 1


class SyntheticObservationReuseRejected(RuntimeError):
    """A cached offline observation lineage cannot be safely reused."""


@dataclass(frozen=True, slots=True)
class SyntheticObservationReuseReview:
    previous_lineage_digest: str
    current_lineage_digest: str
    observation_count: int
    checked_at_ms: int

    @property
    def media_capture_authorized(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


def review_synthetic_observation_reuse(
    cached: SyntheticObservationLineageWitness,
    envelopes: tuple[ObservationEnvelope, ...],
    *,
    privacy_scope: str,
    now_ms: int,
    max_observation_age_ms: int,
    max_review_age_ms: int,
) -> SyntheticObservationReuseReview:
    """Revalidate cached lineage at capture time and again at a later time.

    Recomputing at the *original* time catches a forged cached witness or
    historical input mismatch; recomputing at `now_ms` catches expiry. The
    two reads are not globally atomic and can race after this review.
    """
    if (
        type(cached) is not SyntheticObservationLineageWitness
        or type(envelopes) is not tuple
        or type(privacy_scope) is not str or not privacy_scope.strip()
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        or type(max_observation_age_ms) is not int
        or not 0 <= max_observation_age_ms <= _MAX
        or type(max_review_age_ms) is not int
        or not 0 <= max_review_age_ms <= _MAX
        or type(cached.checked_at_ms) is not int
        or not 0 <= cached.checked_at_ms <= _MAX
        or type(cached.privacy_scope) is not str
        or type(cached.observation_count) is not int
        or type(cached.lineage_digest) is not str
    ):
        raise SyntheticObservationReuseRejected("exact observation reuse inputs required")
    cached_epoch = (
        cached.privacy_scope, cached.checked_at_ms,
        cached.observation_count, cached.lineage_digest,
    )
    if (
        cached.privacy_scope != privacy_scope
        or now_ms < cached.checked_at_ms
        or now_ms - cached.checked_at_ms > max_review_age_ms
    ):
        raise SyntheticObservationReuseRejected(
            "observation witness scope, clock or retention window changed"
        )
    # Bind canonical values, not references to reflectively mutable envelopes.
    try:
        envelope_epoch = tuple(
            (item, item.observation_id) for item in envelopes
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise SyntheticObservationReuseRejected("invalid observation envelope") from exc
    historical = review_synthetic_observation_lineage(
        envelopes, privacy_scope=privacy_scope,
        now_ms=cached.checked_at_ms,
        max_age_ms=max_observation_age_ms,
    )
    if historical != cached:
        raise SyntheticObservationReuseRejected(
            "historical observation lineage differs from retained witness"
        )
    current = review_synthetic_observation_lineage(
        envelopes, privacy_scope=privacy_scope,
        now_ms=now_ms, max_age_ms=max_observation_age_ms,
    )
    # A reflected edit after the final lineage check must not be accepted.
    try:
        stable = (
            cached_epoch == (
                cached.privacy_scope, cached.checked_at_ms,
                cached.observation_count, cached.lineage_digest,
            )
            and len(envelopes) == len(envelope_epoch)
            and all(
                supplied is original and supplied.observation_id == identity
                for supplied, (original, identity) in zip(
                    envelopes, envelope_epoch, strict=True,
                )
            )
        )
    except (AttributeError, TypeError, ValueError):
        stable = False
    if not stable:
        raise SyntheticObservationReuseRejected(
            "cached observation or source changed during review"
        )
    return SyntheticObservationReuseReview(
        cached.lineage_digest, current.lineage_digest,
        current.observation_count, now_ms,
    )
