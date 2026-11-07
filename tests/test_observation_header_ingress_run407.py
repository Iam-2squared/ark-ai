"""Observation ingress cannot rebase original privacy/time window semantics.

Only deterministic synthetic envelopes are used; no microphone, camera,
screen capture, notification or user authorization is exercised.
"""

import hashlib

import pytest

from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window():
    sample = ObservationEnvelope(
        ObservationKind.TEXT, "source", "mock-adapter", "local:private",
        100, hashlib.sha256(b"local sample").hexdigest(),
    )
    return ObservationWindowReview("local:private", 110, 20, (sample,))


@pytest.mark.parametrize(
    ("name", "replacement"),
    [
        ("observed_at_ms", 111),
        ("max_age_ms", 21),
    ],
)
def test_first_envelope_callback_cannot_rebase_review_header(
    monkeypatch, name, replacement,
):
    original = ObservationWindowReview._check_envelope
    calls = []

    def mutate(self, envelope):
        identity = original(self, envelope)
        object.__setattr__(self, name, replacement)
        calls.append(True)
        return identity

    monkeypatch.setattr(ObservationWindowReview, "_check_envelope", mutate)
    with pytest.raises(ValueError, match="header changed during hydration"):
        _window()
    assert calls == [True]


def test_first_header_validation_cannot_rebase_read_time(monkeypatch):
    original = ObservationWindowReview._validate_header

    def mutate(self):
        original(self)
        object.__setattr__(self, "observed_at_ms", 111)

    monkeypatch.setattr(ObservationWindowReview, "_validate_header", mutate)
    with pytest.raises(ValueError, match="input changed during initial validation"):
        _window()


def test_first_header_validation_cannot_replace_same_value_tuple(monkeypatch):
    original = ObservationWindowReview._validate_header

    def mutate(self):
        original(self)
        clone = tuple(list(self.envelopes))
        assert clone is not self.envelopes and clone == self.envelopes
        object.__setattr__(self, "envelopes", clone)

    monkeypatch.setattr(ObservationWindowReview, "_validate_header", mutate)
    with pytest.raises(ValueError, match="input changed during initial validation"):
        _window()


def test_equal_privacy_scope_carrier_swap_during_hydration_rejected(monkeypatch):
    original = ObservationWindowReview._check_envelope

    def mutate(self, envelope):
        identity = original(self, envelope)
        clone = self.privacy_scope.encode().decode()
        assert clone == self.privacy_scope and clone is not self.privacy_scope
        object.__setattr__(self, "privacy_scope", clone)
        return identity

    monkeypatch.setattr(ObservationWindowReview, "_check_envelope", mutate)
    with pytest.raises(ValueError, match="header changed during hydration"):
        _window()


def test_equal_privacy_scope_carrier_swap_after_hydration_rejected():
    window = _window()
    witness = window.witness
    clone = window.privacy_scope.encode().decode()
    assert clone == window.privacy_scope and clone is not window.privacy_scope
    object.__setattr__(window, "privacy_scope", clone)
    with pytest.raises(ValueError, match="header changed after construction"):
        window.assert_consistent()
    assert witness.startswith("window_")


def test_unchanged_window_still_has_content_minimized_witness():
    window = _window()
    initial = window.witness
    window.assert_consistent()
    window.assert_fresh_at(111)
    assert window.witness == initial
    assert initial == _window().witness
    assert "local sample" not in repr(window)
    assert not hasattr(window, "dispatch_authorized")
