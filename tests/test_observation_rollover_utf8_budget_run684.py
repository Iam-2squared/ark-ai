"""Retained observation scope identifiers have a strict UTF-8 byte budget.

All envelopes and clocks are synthetic; no microphone, camera, network,
notification or automatic action is connected by the rollover witness.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observation_rollover_review import (
    ObservationRolloverWitness,
    review_observation_rollover,
)
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


@pytest.mark.parametrize(
    ("scope", "allowed"),
    (
        ("a" * 1024, True),
        ("a" * 1025, False),
        ("🚀" * 256, True),
        ("🚀" * 257, False),
        ("bad" + chr(0xD800), False),
        ("   ", False),
    ),
)
def test_direct_retained_witness_enforces_byte_limit_and_unicode(scope, allowed):
    def construct():
        return ObservationRolloverWitness(
            scope, 100, "window_" + "a" * 64, 1, "b" * 64,
        )

    if allowed:
        witness = construct()
        assert witness.privacy_scope == scope
        assert len(witness.privacy_scope.encode("utf-8")) <= 1024
    else:
        with pytest.raises(ValueError, match="scope"):
            construct()


def test_max_byte_scope_rolls_over_without_expanding_observation_authority():
    scope = "🚀" * 256

    def window(at_ms: int) -> ObservationWindowReview:
        envelope = ObservationEnvelope(
            ObservationKind.TEXT, "synthetic-source", "fixture-adapter",
            scope, at_ms - 1, hashlib.sha256(b"synthetic-only").hexdigest(),
        )
        return ObservationWindowReview(scope, at_ms, 20, (envelope,))

    first = review_observation_rollover(window(100))
    second = review_observation_rollover(window(110), retained=first)
    assert first.generation == 1
    assert second.generation == 2
    assert second.privacy_scope == scope
    assert second.chain_sha256 != first.chain_sha256
    assert not hasattr(second, "dispatch_authorized")
    assert not hasattr(second, "notification_authorized")
