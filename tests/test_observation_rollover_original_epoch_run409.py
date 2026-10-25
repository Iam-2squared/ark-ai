"""Synthetic rollover retains its original window and history across callbacks.

No real sensor, notification, trusted clock or external execution is used.
"""

import hashlib

import pytest

import ark.observation_rollover_review as rollover
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window(now=110):
    scope = "local:private-window"
    return ObservationWindowReview(
        scope, now, 30,
        (
            ObservationEnvelope(
                ObservationKind.TEXT, "fixture-source", "fixture-adapter",
                scope, now - 1, hashlib.sha256(b"synthetic").hexdigest(),
            ),
        ),
    )


@pytest.mark.parametrize("mutation", ("generation", "equal-sha-clone"))
def test_first_consistency_check_cannot_rebase_retained_history(
    monkeypatch, mutation,
):
    retained = rollover.review_observation_rollover(_window(100))
    current = _window(110)
    original_consistency = ObservationWindowReview.assert_consistent
    calls = []

    def inspecting(self):
        original_consistency(self)
        if self is current and not calls:
            calls.append(True)
            if mutation == "generation":
                object.__setattr__(retained, "generation", 25)
            else:
                original = retained.chain_sha256
                clone = original.encode("ascii").decode("ascii")
                assert clone == original and clone is not original
                object.__setattr__(retained, "chain_sha256", clone)

    monkeypatch.setattr(ObservationWindowReview, "assert_consistent", inspecting)
    with pytest.raises(ValueError, match="retained observation witness changed"):
        rollover.review_observation_rollover(current, retained=retained)
    assert calls == [True]


@pytest.mark.parametrize("mutation", ("header", "equal-tuple-clone"))
def test_first_consistency_check_cannot_rebase_observation_window(
    monkeypatch, mutation,
):
    current = _window(110)
    original_consistency = ObservationWindowReview.assert_consistent
    calls = []

    def inspecting(self):
        original_consistency(self)
        if self is current and not calls:
            calls.append(True)
            if mutation == "header":
                object.__setattr__(current, "observed_at_ms", 111)
                scope = current.privacy_scope
                object.__setattr__(
                    current, "_header_epoch", (scope, 111, current.max_age_ms),
                )
                object.__setattr__(
                    current, "_header_carrier_epoch",
                    (scope, 111, current.max_age_ms),
                )
            else:
                cloned = tuple(list(current.envelopes))
                assert cloned == current.envelopes
                assert cloned is not current.envelopes
                object.__setattr__(current, "envelopes", cloned)
                object.__setattr__(current, "_carrier_epoch", cloned)

    monkeypatch.setattr(ObservationWindowReview, "assert_consistent", inspecting)
    with pytest.raises(ValueError, match="observation window changed"):
        rollover.review_observation_rollover(current)
    assert calls == [True]


def test_retained_history_mutated_during_payload_cannot_be_restored_by_hash(
    monkeypatch,
):
    retained = rollover.review_observation_rollover(_window(100))
    current = _window(110)
    payload = rollover._canonical_window_payload
    digest = rollover.hashlib.sha256
    original_generation = retained.generation
    calls = []

    def encoding(**kwargs):
        encoded = payload(**kwargs)
        object.__setattr__(retained, "generation", original_generation + 1)
        calls.append("mutated")
        return encoded

    def hashing(data):
        calls.append("restored")
        object.__setattr__(retained, "generation", original_generation)
        return digest(data)

    monkeypatch.setattr(rollover, "_canonical_window_payload", encoding)
    monkeypatch.setattr(rollover.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="retained observation witness changed"):
        rollover.review_observation_rollover(current, retained=retained)
    assert calls == ["mutated"]


def test_retained_hash_drift_cannot_be_restored_by_next_window_check(
    monkeypatch,
):
    retained = rollover.review_observation_rollover(_window(100))
    current = _window(110)
    digest = rollover.hashlib.sha256
    original_consistency = ObservationWindowReview.assert_consistent
    original_generation = retained.generation
    calls = []

    def hashing(data):
        value = digest(data)
        object.__setattr__(retained, "generation", original_generation + 1)
        calls.append("mutated")
        return value

    def consistency(self):
        original_consistency(self)
        if calls == ["mutated"]:
            calls.append("restored")
            object.__setattr__(retained, "generation", original_generation)

    monkeypatch.setattr(rollover.hashlib, "sha256", hashing)
    monkeypatch.setattr(ObservationWindowReview, "assert_consistent", consistency)
    with pytest.raises(ValueError, match="retained observation witness changed"):
        rollover.review_observation_rollover(current, retained=retained)
    assert calls == ["mutated"]


def test_clean_window_rollover_retains_deterministic_inert_identity():
    prior = rollover.review_observation_rollover(_window(100))
    current = _window(110)
    first = rollover.review_observation_rollover(current, retained=prior)
    second = rollover.review_observation_rollover(current, retained=prior)
    assert first == second
    assert first.generation == 2
    assert first.window_witness == current.witness
    assert first.privacy_scope == prior.privacy_scope
