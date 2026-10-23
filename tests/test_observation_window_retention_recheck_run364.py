"""Synthetic cached-observation retention checks; no media or clock authority."""

import hashlib

import pytest

from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window():
    envelope = ObservationEnvelope(
        ObservationKind.TEXT,
        "synthetic-source",
        "offline-adapter",
        "fixture:private",
        100,
        hashlib.sha256(b"synthetic").hexdigest(),
    )
    return ObservationWindowReview("fixture:private", 110, 20, (envelope,))


def test_retention_boundary_is_inclusive_without_witness_change():
    window = _window()
    witness = window.witness
    window.assert_fresh_at(110)
    window.assert_fresh_at(120)
    assert window.witness == witness


def test_cached_window_expires_without_rewrite_or_notification():
    window = _window()
    with pytest.raises(ValueError, match="age budget"):
        window.assert_fresh_at(121)
    assert window.observed_at_ms == 110


def test_retention_check_rejects_clock_rollback():
    with pytest.raises(ValueError, match="backwards"):
        _window().assert_fresh_at(109)


@pytest.mark.parametrize("invalid", (True, 10.5, -1, 2**63))
def test_retention_check_requires_exact_bounded_timestamp(invalid):
    with pytest.raises(ValueError, match="exact SQLite-range"):
        _window().assert_fresh_at(invalid)


def test_reflected_envelope_change_is_not_accepted_as_new_retention_epoch():
    window = _window()
    object.__setattr__(window.envelopes[0], "ingested_at_ms", 101)
    with pytest.raises(ValueError, match="identity changed"):
        window.assert_fresh_at(120)


def test_reflected_header_extension_cannot_widen_retention():
    window = _window()
    object.__setattr__(window, "max_age_ms", 1000)
    with pytest.raises(ValueError, match="header changed"):
        window.assert_fresh_at(121)
