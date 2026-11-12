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


_LINEAGE_WITNESS_TYPE = SyntheticObservationLineageWitness
_REUSE_RESULT_TYPE = SyntheticObservationReuseReview
_REUSE_DENIAL_NAMES = (
    "media_capture_authorized", "disclosure_authorized",
    "notification_authorized", "dispatch_authorized",
)
_ORIGINAL_REUSE_DENIALS = tuple(
    vars(_REUSE_RESULT_TYPE)[name] for name in _REUSE_DENIAL_NAMES
)

# A cached witness or envelope is caller-owned privacy metadata. Slotted
# fields and lookup hooks can be rebound at class level. Deny such replacements
# before reading the first cached scope or source identifier, and repeat across
# the two reentrant lineage callbacks. Leave result __init__ injectable for
# existing after-construction mutation regression tests.
_REUSE_SOURCE_TYPE = ObservationEnvelope
_REUSE_SOURCE_NAMES = (
    "kind", "source_id", "adapter_id", "privacy_scope", "ingested_at_ms",
    "content_sha256", "parent_sha256", "schema_version", "observation_id",
    "__getattribute__", "__getattr__",
)
_REUSE_CACHE_NAMES = (
    "privacy_scope", "checked_at_ms", "observation_count", "lineage_digest",
    "__getattribute__", "__getattr__",
)
_REUSE_SOURCE_ORIGINAL = tuple(
    vars(_REUSE_SOURCE_TYPE).get(name) for name in _REUSE_SOURCE_NAMES
)
_REUSE_CACHE_ORIGINAL = tuple(
    vars(_LINEAGE_WITNESS_TYPE).get(name) for name in _REUSE_CACHE_NAMES
)


def _require_original_reuse_inputs() -> None:
    if (
        ObservationEnvelope is not _REUSE_SOURCE_TYPE
        # The exported witness name is not authoritative: callers retaining
        # the exact imported class still pass when a global alias is rebound.
        # Inspect the original type's descriptors below, not its public alias.
        or any(
            vars(_REUSE_SOURCE_TYPE).get(name) is not original
            for name, original in zip(
                _REUSE_SOURCE_NAMES, _REUSE_SOURCE_ORIGINAL, strict=True,
            )
        )
        or any(
            vars(_LINEAGE_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _REUSE_CACHE_NAMES, _REUSE_CACHE_ORIGINAL, strict=True,
            )
        )
    ):
        raise SyntheticObservationReuseRejected(
            "observation reuse input descriptor changed"
        )



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
    _require_original_reuse_inputs()
    if (
        type(cached) is not _LINEAGE_WITNESS_TYPE
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
    # A frozen witness still allows reflective replacement with an
    # equal-valued but different string object during either lineage pass.
    if (
        cached.privacy_scope != privacy_scope
        or now_ms < cached.checked_at_ms
        or now_ms - cached.checked_at_ms > max_review_age_ms
    ):
        raise SyntheticObservationReuseRejected(
            "observation witness scope, clock or retention window changed"
        )
    # Pin ORIGINAL carriers before any observation_id callback is evaluated.
    # Equal-valued envelope identities alone do not detect carrier swaps.
    field_names = (
        "kind", "source_id", "adapter_id", "privacy_scope",
        "ingested_at_ms", "content_sha256", "parent_sha256",
        "schema_version",
    )
    try:
        source_epoch = tuple(
            (item, tuple(getattr(item, name) for name in field_names))
            for item in envelopes
        )
        envelope_epoch = tuple(
            (item, item.observation_id) for item in envelopes
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise SyntheticObservationReuseRejected("invalid observation envelope") from exc
    def assert_epoch() -> None:
        _require_original_reuse_inputs()
        # A change between the historical and current lineage reviews must
        # not be hidden by restoring the original carrier on a later callback.
        try:
            stable = (
                type(cached.privacy_scope) is str
                and type(cached.checked_at_ms) is int
                and type(cached.observation_count) is int
                and type(cached.lineage_digest) is str
                and all(
                    getattr(cached, name) is original
                    for name, original in zip(
                        ("privacy_scope", "checked_at_ms", "observation_count",
                         "lineage_digest"), cached_epoch, strict=True,
                    )
                )
                and len(envelopes) == len(source_epoch)
                and all(
                    supplied is original
                    and all(
                        getattr(supplied, name) is value
                        for name, value in zip(field_names, values, strict=True)
                    )
                    for supplied, (original, values) in zip(
                        envelopes, source_epoch, strict=True,
                    )
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

    historical = review_synthetic_observation_lineage(
        envelopes, privacy_scope=privacy_scope,
        now_ms=cached.checked_at_ms,
        max_age_ms=max_observation_age_ms,
    )
    assert_epoch()
    if type(historical) is not _LINEAGE_WITNESS_TYPE or historical != cached:
        raise SyntheticObservationReuseRejected(
            "historical observation lineage differs from retained witness"
        )
    historical_epoch = (
        historical.privacy_scope, historical.checked_at_ms,
        historical.observation_count, historical.lineage_digest,
    )
    current = review_synthetic_observation_lineage(
        envelopes, privacy_scope=privacy_scope,
        now_ms=now_ms, max_age_ms=max_observation_age_ms,
    )
    # Recheck both intermediate witnesses after the later callback, then
    # again after result construction. No forged/currently stale lineage
    # carrier may be silently substituted for a verified fresh witness.
    assert_epoch()
    if (
        type(current) is not _LINEAGE_WITNESS_TYPE
        or current.privacy_scope != privacy_scope
        or current.checked_at_ms != now_ms
        or current.observation_count != len(envelopes)
    ):
        raise SyntheticObservationReuseRejected(
            "current observation lineage result differs from reviewed inputs"
        )
    current_epoch = (
        current.privacy_scope, current.checked_at_ms,
        current.observation_count, current.lineage_digest,
    )

    def assert_witnesses() -> None:
        if (
            any(getattr(historical, name) is not original
                for name, original in zip(
                    ("privacy_scope", "checked_at_ms", "observation_count",
                     "lineage_digest"), historical_epoch, strict=True,
                ))
            or any(getattr(current, name) is not original
                   for name, original in zip(
                       ("privacy_scope", "checked_at_ms", "observation_count",
                        "lineage_digest"), current_epoch, strict=True,
                   ))
        ):
            raise SyntheticObservationReuseRejected(
                "observation lineage witness changed during result construction"
            )

    assert_witnesses()
    result = SyntheticObservationReuseReview(
        cached_epoch[3], current_epoch[3], current_epoch[2], now_ms,
    )
    assert_epoch()
    assert_witnesses()
    def assert_result_epoch() -> None:
        if (
            type(result) is not _REUSE_RESULT_TYPE
            or result.previous_lineage_digest is not cached_epoch[3]
            or result.current_lineage_digest is not current_epoch[3]
            or result.observation_count is not current_epoch[2]
            or result.checked_at_ms is not now_ms
        ):
            raise SyntheticObservationReuseRejected(
                "observation reuse result changed during construction or denial"
            )

    assert_result_epoch()
    # Diagnostic observation freshness is NEVER consent to capture media,
    # disclose Personal Context, notify, or execute an external ToolBackend.
    # Each property is a callback boundary even when it returns False.
    if (
        result.media_capture_authorized is not False
        or result.disclosure_authorized is not False
        or result.notification_authorized is not False
        or result.dispatch_authorized is not False
    ):
        raise SyntheticObservationReuseRejected(
            "observation reuse result acquired authority"
        )
    assert_epoch()
    assert_witnesses()
    assert_result_epoch()
    # Re-read denial flags in case the first getters replaced a later one;
    # after the final getter, inspect every originally pinned carrier again.
    if (
        result.media_capture_authorized is not False
        or result.disclosure_authorized is not False
        or result.notification_authorized is not False
        or result.dispatch_authorized is not False
    ):
        raise SyntheticObservationReuseRejected(
            "observation reuse result acquired authority"
        )
    assert_epoch()
    assert_witnesses()
    assert_result_epoch()
    # A substituted getter that returns False still changes the inert
    # receipt's authority contract. Verify original class descriptors after
    # the existing callback mutation checks so earlier failures retain their
    # explicit input/result diagnostics.
    if any(
        vars(_REUSE_RESULT_TYPE).get(name) is not original
        for name, original in zip(
            _REUSE_DENIAL_NAMES, _ORIGINAL_REUSE_DENIALS, strict=True,
        )
    ):
        raise SyntheticObservationReuseRejected(
            "observation reuse authority descriptor changed"
        )
    return result
