"""Disconnected observation-window continuity for synthetic privacy-scoped inputs.

Retained local digests make a monotonic review trail, NOT source attestation,
consent, authenticated storage, a capture connector, or notification authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .observation_window_review import ObservationWindowReview

_GENESIS = hashlib.sha256(b"ark-observation-rollover-v1").digest()
_SHA256 = re.compile(r"[0-9a-f]{64}")
_WINDOW = re.compile(r"window_[0-9a-f]{64}")
_MAX_GENERATION = 2**63 - 1


@dataclass(frozen=True, slots=True)
class ObservationRolloverWitness:
    privacy_scope: str
    observed_at_ms: int
    window_witness: str
    generation: int
    chain_sha256: str

    def __post_init__(self) -> None:
        if type(self.privacy_scope) is not str or not self.privacy_scope.strip():
            raise ValueError("rollover privacy scope must be nonempty exact text")
        if (
            type(self.observed_at_ms) is not int
            or not 0 <= self.observed_at_ms <= _MAX_GENERATION
        ):
            raise ValueError("rollover observation time must be nonnegative SQLite-range")
        if type(self.window_witness) is not str or not _WINDOW.fullmatch(
            self.window_witness
        ):
            raise ValueError("rollover window identity must be canonical")
        if (
            type(self.generation) is not int
            or not 1 <= self.generation <= _MAX_GENERATION
        ):
            raise ValueError("rollover generation must be a valid positive integer")
        if type(self.chain_sha256) is not str or not _SHA256.fullmatch(
            self.chain_sha256
        ):
            raise ValueError("rollover chain identity must be canonical")


def _canonical_window_payload(
    *, privacy_scope: str, observed_at_ms: int, window_witness: str, generation: int
) -> bytes:
    return json.dumps(
        {
            "schema_version": 1,
            "privacy_scope": privacy_scope,
            "observed_at_ms": observed_at_ms,
            "window_witness": window_witness,
            "generation": generation,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def review_observation_rollover(
    current: ObservationWindowReview,
    *,
    retained: ObservationRolloverWitness | None = None,
    now_ms: int | None = None,
) -> ObservationRolloverWitness:
    """Validate one replay-safe local window transition without media access."""
    if type(current) is not ObservationWindowReview:
        raise TypeError("current must be an exact ObservationWindowReview")
    if retained is not None and type(retained) is not ObservationRolloverWitness:
        raise TypeError("retained must be an exact ObservationRolloverWitness")

    # Pin original carrier and prior history BEFORE the first consistency
    # callback. Otherwise an early callback could silently rebase a retained
    # witness to an alternate but individually valid rollover baseline.
    header_epoch = (
        current.privacy_scope, current.observed_at_ms, current.max_age_ms,
    )
    envelope_carrier = current.envelopes
    pinned_previous = None if retained is None else (
        retained.privacy_scope,
        retained.observed_at_ms,
        retained.window_witness,
        retained.generation,
        retained.chain_sha256,
    )

    def assert_outer_epoch() -> None:
        if (
            current.privacy_scope is not header_epoch[0]
            or (
                current.privacy_scope, current.observed_at_ms,
                current.max_age_ms,
            ) != header_epoch
            or current.envelopes is not envelope_carrier
        ):
            raise ValueError("observation window changed during rollover")
        if retained is not None and (
            (
                retained.privacy_scope, retained.observed_at_ms,
                retained.window_witness, retained.generation,
                retained.chain_sha256,
            ) != pinned_previous
            or retained.privacy_scope is not pinned_previous[0]
            or retained.window_witness is not pinned_previous[2]
            or retained.chain_sha256 is not pinned_previous[4]
        ):
            raise ValueError("retained observation witness changed")

    assert_outer_epoch()
    current.assert_consistent()
    assert_outer_epoch()
    if now_ms is not None:
        current.assert_fresh_at(now_ms)
        assert_outer_epoch()
    pinned_window = (
        current.privacy_scope, current.observed_at_ms, current.witness
    )
    assert_outer_epoch()
    if retained is not None:
        ObservationRolloverWitness(*pinned_previous)
        assert_outer_epoch()

    scope, timestamp, window_witness = pinned_window
    if pinned_previous is None:
        generation = 1
        previous_digest = _GENESIS
    else:
        previous_scope, previous_at, previous_window, previous_gen, previous_sha = (
            pinned_previous
        )
        if scope != previous_scope:
            raise ValueError("privacy scope changed across observation rollover")
        if timestamp < previous_at:
            raise ValueError("observation rollover clock moved backwards")
        if timestamp == previous_at:
            if window_witness != previous_window:
                raise ValueError("same-clock observation rollover is not idempotent")
            result = ObservationRolloverWitness(*pinned_previous)
            current.assert_consistent()
            assert_outer_epoch()
            if (current.privacy_scope, current.observed_at_ms, current.witness) != (
                pinned_window
            ):
                raise ValueError("observation window changed during rollover")
            if (
                retained.privacy_scope, retained.observed_at_ms,
                retained.window_witness, retained.generation, retained.chain_sha256,
            ) != pinned_previous:
                raise ValueError("retained observation witness changed")
            if now_ms is not None:
                current.assert_fresh_at(now_ms)
                assert_outer_epoch()
            assert_outer_epoch()
            return result
        if previous_gen >= _MAX_GENERATION:
            raise ValueError("observation rollover generation exhausted")
        generation = previous_gen + 1
        previous_digest = bytes.fromhex(previous_sha)

    encoded = _canonical_window_payload(
        privacy_scope=scope,
        observed_at_ms=timestamp,
        window_witness=window_witness,
        generation=generation,
    )
    assert_outer_epoch()
    new_sha = hashlib.sha256(previous_digest + b"\\n" + encoded).hexdigest()
    assert_outer_epoch()
    current.assert_consistent()
    assert_outer_epoch()
    if (current.privacy_scope, current.observed_at_ms, current.witness) != pinned_window:
        raise ValueError("observation window changed during rollover")
    if retained is not None and (
        retained.privacy_scope, retained.observed_at_ms,
        retained.window_witness, retained.generation, retained.chain_sha256,
    ) != pinned_previous:
        raise ValueError("retained observation witness changed")
    if now_ms is not None:
        current.assert_fresh_at(now_ms)
        assert_outer_epoch()
    assert_outer_epoch()
    result = ObservationRolloverWitness(scope, timestamp, window_witness, generation, new_sha)
    # A reflected-mutable dataclass constructor/post-init is a callback too.
    # Reject any source/history change or retargeted digest carrier that it
    # creates. Nothing here grants capture, consent or notification authority.
    assert_outer_epoch()
    current.assert_consistent()
    assert_outer_epoch()
    if (
        type(result) is not ObservationRolloverWitness
        or result.privacy_scope is not scope
        or result.observed_at_ms != timestamp
        or result.window_witness is not window_witness
        or result.generation != generation
        or result.chain_sha256 is not new_sha
    ):
        raise ValueError("observation rollover result changed during construction")
    assert_outer_epoch()
    return result
