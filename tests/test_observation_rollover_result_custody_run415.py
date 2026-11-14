"""Disconnected rollover construction cannot substitute observation evidence.

No camera, microphone, screen capture, external model, notification, or
physical action is enabled by a successful synthetic witness.
"""

import hashlib

import pytest

import ark.observation_rollover_review as rollover
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window(now: int):
    scope = "local:private-window"
    return ObservationWindowReview(
        scope, now, 30,
        (
            ObservationEnvelope(
                ObservationKind.TEXT, "fixture", "disconnected",
                scope, now - 1, hashlib.sha256(b"local").hexdigest(),
            ),
        ),
    )


def _clone(text: str) -> str:
    other = ("!" + text)[1:]
    assert other == text and other is not text
    return other


@pytest.mark.parametrize("tamper", ("result_digest", "window_scope", "prior_digest"))
def test_witness_constructor_callback_cannot_substitute_returned_epoch(
    monkeypatch, tamper: str,
):
    previous = rollover.review_observation_rollover(_window(100))
    current = _window(110)
    original = rollover.ObservationRolloverWitness.__post_init__

    def changed(self):
        original(self)
        if tamper == "result_digest":
            object.__setattr__(self, "chain_sha256", _clone(self.chain_sha256))
        elif tamper == "window_scope":
            object.__setattr__(current, "privacy_scope", _clone(current.privacy_scope))
        else:
            object.__setattr__(
                previous, "chain_sha256", _clone(previous.chain_sha256),
            )

    monkeypatch.setattr(rollover.ObservationRolloverWitness, "__post_init__", changed)
    with pytest.raises(ValueError, match="result changed|window changed|retained"):
        rollover.review_observation_rollover(current, retained=previous)


def test_normal_rollover_remains_deterministic_and_diagnostic_only():
    previous = rollover.review_observation_rollover(_window(100))
    current = _window(110)
    first = rollover.review_observation_rollover(current, retained=previous)
    second = rollover.review_observation_rollover(current, retained=previous)
    assert first == second
    assert first.generation == 2
    assert first.privacy_scope == previous.privacy_scope
    assert first.window_witness == current.witness
