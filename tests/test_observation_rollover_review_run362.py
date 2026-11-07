"""Synthetic window-rollover continuity: no live capture or notification."""

import hashlib

import pytest

import ark.observation_rollover_review as review
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture(now=100, *, scope="fixture:private", payload=b"synthetic"):
    envelope = ObservationEnvelope(
        ObservationKind.TEXT,
        "synthetic-source",
        "synthetic-adapter",
        scope,
        now - 1,
        hashlib.sha256(payload).hexdigest(),
    )
    return ObservationWindowReview(scope, now, 20, (envelope,))


def test_first_window_witness_is_content_free_and_deterministic():
    first = review.review_observation_rollover(_fixture())
    second = review.review_observation_rollover(_fixture())
    assert first == second
    assert first.generation == 1
    assert len(first.chain_sha256) == 64
    assert "synthetic" not in repr(first)


def test_monotone_transition_and_equal_time_idempotency():
    first_window = _fixture()
    first = review.review_observation_rollover(first_window)
    assert review.review_observation_rollover(first_window, retained=first) == first
    second = review.review_observation_rollover(
        _fixture(now=110, payload=b"synthetic-2"), retained=first
    )
    assert second.generation == 2
    assert second.chain_sha256 != first.chain_sha256
    assert second.privacy_scope == first.privacy_scope


def test_clock_rollback_is_rejected():
    first = review.review_observation_rollover(_fixture(now=110))
    with pytest.raises(ValueError, match="backwards"):
        review.review_observation_rollover(_fixture(now=105), retained=first)


def test_equal_clock_but_different_window_is_not_idempotent():
    first = review.review_observation_rollover(_fixture())
    with pytest.raises(ValueError, match="idempotent"):
        review.review_observation_rollover(
            _fixture(payload=b"different"), retained=first
        )


def test_scope_crossover_is_rejected():
    first = review.review_observation_rollover(_fixture())
    with pytest.raises(ValueError, match="scope changed"):
        review.review_observation_rollover(
            _fixture(now=110, scope="other:private"), retained=first
        )


def test_invalid_retained_revision_is_rejected_before_hashing():
    first = review.review_observation_rollover(_fixture())
    object.__setattr__(first, "generation", 0)
    with pytest.raises(ValueError, match="generation"):
        review.review_observation_rollover(_fixture(now=110), retained=first)


def test_retained_witness_reflection_mid_review_is_detected(monkeypatch):
    first = review.review_observation_rollover(_fixture())
    original = review._canonical_window_payload

    def mutate(**kwargs):
        object.__setattr__(first, "generation", 999)
        return original(**kwargs)

    monkeypatch.setattr(review, "_canonical_window_payload", mutate)
    with pytest.raises(ValueError, match="retained observation witness changed"):
        review.review_observation_rollover(_fixture(now=110), retained=first)


def test_window_identity_reflection_mid_review_is_detected(monkeypatch):
    current = _fixture()
    original = review._canonical_window_payload

    def mutate(**kwargs):
        object.__setattr__(current.envelopes[0], "content_sha256", "f" * 64)
        return original(**kwargs)

    monkeypatch.setattr(review, "_canonical_window_payload", mutate)
    with pytest.raises(ValueError, match="observation identity changed"):
        review.review_observation_rollover(current)


def test_invalid_current_type_is_rejected():
    with pytest.raises(TypeError, match="exact ObservationWindowReview"):
        review.review_observation_rollover(object())


def test_rollover_witness_has_no_execution_or_consent_authority():
    witness = review.review_observation_rollover(_fixture())
    for name in ("authorization", "grant", "tool_call", "backend", "consent"):
        assert not hasattr(witness, name)
