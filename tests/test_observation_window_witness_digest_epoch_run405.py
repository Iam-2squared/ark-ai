"""A disconnected observation witness must remain bound during digest callbacks.

All observations are synthetic envelopes; no media/sensor access is performed.
"""

import hashlib

import pytest

import ark.observation_window_review as module
from ark.observations import ObservationEnvelope, ObservationKind


def _window():
    envelope = ObservationEnvelope(
        ObservationKind.TEXT, "fixture-src", "fixture-adapter",
        "local-private", 100, "a" * 64,
    )
    review = module.ObservationWindowReview(
        "local-private", 110, 100, (envelope,),
    )
    return review, envelope


@pytest.mark.parametrize(
    ("field", "new_value"),
    (
        ("source_id", "different-fixture-src"),
        ("content_sha256", "b" * 64),
    ),
)
def test_witness_refuses_mutation_during_final_json_encoding(
    monkeypatch, field, new_value,
):
    review, envelope = _window()
    original = module.json.dumps

    def serialization(payload, **kwargs):
        encoded = original(payload, **kwargs)
        if isinstance(payload, dict) and "observation_ids" in payload:
            object.__setattr__(envelope, field, new_value)
        return encoded

    monkeypatch.setattr(module.json, "dumps", serialization)
    with pytest.raises(ValueError, match="observation identity changed"):
        _ = review.witness


def test_witness_refuses_temporary_serialization_mutation_even_if_hash_restores(
    monkeypatch,
):
    review, envelope = _window()
    original_dumps = module.json.dumps
    original_hash = module.hashlib.sha256
    observed = []

    def serialization(payload, **kwargs):
        encoded = original_dumps(payload, **kwargs)
        if isinstance(payload, dict) and "observation_ids" in payload:
            object.__setattr__(envelope, "source_id", "short-lived-retarget")
            observed.append("mutate")
        return encoded

    def hashing(payload=b"", *args, **kwargs):
        if b'"observation_ids"' in payload:
            object.__setattr__(envelope, "source_id", "fixture-src")
            observed.append("restore")
        return original_hash(payload, *args, **kwargs)

    monkeypatch.setattr(module.json, "dumps", serialization)
    monkeypatch.setattr(module.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="observation identity changed"):
        _ = review.witness
    assert observed == ["mutate"]


def test_witness_refuses_mutation_during_final_sha256(monkeypatch):
    review, envelope = _window()
    original = module.hashlib.sha256

    def hashing(payload=b"", *args, **kwargs):
        digest = original(payload, *args, **kwargs)
        if b'"observation_ids"' in payload:
            object.__setattr__(envelope, "source_id", "retargeted-after-hash")
        return digest

    monkeypatch.setattr(module.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="observation identity changed"):
        _ = review.witness


def test_unmodified_witness_remains_deterministic():
    review, _ = _window()
    first = review.witness
    assert first == review.witness
    assert first.startswith("window_")
    assert len(first) == len("window_") + hashlib.sha256().digest_size * 2
