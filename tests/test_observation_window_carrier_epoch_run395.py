"""A same-item observation tuple replacement is not the original review epoch."""

import hashlib

import pytest

from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _items():
    return (
        ObservationEnvelope(
            ObservationKind.TEXT, "source", "adapter", "scope:private",
            100, hashlib.sha256(b"first").hexdigest(),
        ),
        ObservationEnvelope(
            ObservationKind.TRANSCRIPT, "source", "adapter", "scope:private",
            105, hashlib.sha256(b"second").hexdigest(),
        ),
    )


def _window():
    return ObservationWindowReview("scope:private", 110, 20, _items())


@pytest.mark.parametrize("entrypoint", ("assert_consistent", "assert_fresh_at", "witness"))
def test_equal_value_rebound_tuple_is_not_original_observation_epoch(entrypoint):
    window = _window()
    initial = window.envelopes
    copied = tuple(list(initial))
    assert copied == initial
    assert copied is not initial
    assert all(a is b for a, b in zip(copied, initial, strict=True))
    object.__setattr__(window, "envelopes", copied)
    with pytest.raises(ValueError, match="tuple changed"):
        if entrypoint == "assert_consistent":
            window.assert_consistent()
        elif entrypoint == "assert_fresh_at":
            window.assert_fresh_at(111)
        else:
            _ = window.witness


def test_reentrant_tuple_swap_during_initial_hydration_is_rejected(monkeypatch):
    original = ObservationWindowReview._check_envelope
    calls = 0

    def replace_after_first(self, envelope):
        nonlocal calls
        identity = original(self, envelope)
        calls += 1
        if calls == 1:
            object.__setattr__(
                self, "envelopes", tuple(list(self.envelopes)),
            )
        return identity

    monkeypatch.setattr(
        ObservationWindowReview, "_check_envelope", replace_after_first,
    )
    with pytest.raises(ValueError, match="tuple changed"):
        _window()
    assert calls == 2


def test_unchanged_observation_window_stays_content_minimized_and_inert():
    window = _window()
    first = window.witness
    window.assert_consistent()
    window.assert_fresh_at(115)
    assert window.witness == first
    assert first.startswith("window_")
    for forbidden in ("authorization", "dispatch", "backend", "raw_media"):
        assert not hasattr(window, forbidden)
