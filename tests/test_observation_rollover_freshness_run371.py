"""Opt-in rechecking of synthetic observation retention at rollover use time."""

import hashlib

import pytest

from ark.observation_rollover_review import review_observation_rollover
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window(observed_at_ms=110):
    envelope = ObservationEnvelope(
        ObservationKind.TEXT,
        "fixture-source",
        "fixture-adapter",
        "fixture:private",
        100,
        hashlib.sha256(b"fixture-observation").hexdigest(),
    )
    return ObservationWindowReview(
        "fixture:private", observed_at_ms, 20, (envelope,)
    )


def test_opt_in_rollover_accepts_inclusive_retention_boundary():
    current = _window()
    witness = review_observation_rollover(current, now_ms=120)
    assert witness.generation == 1
    assert witness.window_witness == current.witness
    assert review_observation_rollover(
        current, retained=witness, now_ms=120
    ) == witness


def test_opt_in_rollover_rejects_expired_cached_window():
    with pytest.raises(ValueError, match="age budget"):
        review_observation_rollover(_window(), now_ms=121)


def test_opt_in_same_clock_idempotency_never_bypasses_expiry():
    current = _window()
    witness = review_observation_rollover(current, now_ms=120)
    with pytest.raises(ValueError, match="age budget"):
        review_observation_rollover(current, retained=witness, now_ms=121)


def test_opt_in_rollover_rejects_clock_rollback():
    with pytest.raises(ValueError, match="backwards"):
        review_observation_rollover(_window(), now_ms=109)


@pytest.mark.parametrize("invalid", [True, -1, 2**63, 10.5, "120"])
def test_opt_in_rollover_requires_exact_valid_time(invalid):
    with pytest.raises(ValueError, match="exact SQLite-range"):
        review_observation_rollover(_window(), now_ms=invalid)


def test_opt_in_rollover_rejects_reflected_cached_window_change():
    current = _window()
    object.__setattr__(current.envelopes[0], "ingested_at_ms", 101)
    with pytest.raises(ValueError, match="identity changed"):
        review_observation_rollover(current, now_ms=120)


def test_original_no_clock_review_remains_disconnected_and_compatible():
    current = _window()
    first = review_observation_rollover(current)
    second = review_observation_rollover(current, retained=first)
    assert second == first
