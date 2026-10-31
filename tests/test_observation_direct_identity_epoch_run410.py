"""Observation identity is bounded and stable across direct hash boundaries.

No camera, microphone, screen data, notification or backend is accessed.
"""

import hashlib

import pytest

from ark import observations
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture(**overrides):
    details = {
        "kind": ObservationKind.TRANSCRIPT,
        "source_id": "source",
        "adapter_id": "adapter",
        "privacy_scope": "local",
        "ingested_at_ms": 1,
        "content_sha256": "a" * 64,
        "parent_sha256": None,
    }
    details.update(overrides)
    return ObservationEnvelope(**details)


@pytest.mark.parametrize("field", ["source_id", "adapter_id", "privacy_scope"])
def test_provenance_identifiers_are_bounded(field):
    with pytest.raises(ValueError, match="identifier budget"):
        _fixture(**{field: "x" * 1025})
    assert _fixture(**{field: "x" * 1024}).observation_id.startswith("obs_")


def test_provenance_identifiers_reject_surrogate_text():
    with pytest.raises(ValueError, match="UTF-8"):
        _fixture(source_id="unpaired\ud800")


def test_json_callback_cannot_replace_equal_carrier(tmp_path, monkeypatch):
    del tmp_path
    envelope = _fixture(source_id="a" * 300)
    original = observations.json.dumps

    def swap(*args, **kwargs):
        encoded = original(*args, **kwargs)
        object.__setattr__(envelope, "source_id", "".join(["a" * 150, "a" * 150]))
        return encoded

    monkeypatch.setattr(observations.json, "dumps", swap)
    with pytest.raises(ValueError, match="identity changed"):
        _ = envelope.observation_id


def test_json_callback_cannot_change_privacy_scope(monkeypatch):
    envelope = _fixture()
    original = observations.json.dumps

    def swap(*args, **kwargs):
        encoded = original(*args, **kwargs)
        object.__setattr__(envelope, "privacy_scope", "other")
        return encoded

    monkeypatch.setattr(observations.json, "dumps", swap)
    with pytest.raises(ValueError, match="identity changed"):
        _ = envelope.observation_id


def test_hash_callback_cannot_change_timestamp(monkeypatch):
    envelope = _fixture()
    original = hashlib.sha256

    def swap(*args, **kwargs):
        object.__setattr__(envelope, "ingested_at_ms", 2)
        return original(*args, **kwargs)

    monkeypatch.setattr(observations.hashlib, "sha256", swap)
    with pytest.raises(ValueError, match="identity changed"):
        _ = envelope.observation_id


def test_reflected_invalid_kind_rejected_before_hashing():
    envelope = _fixture()
    object.__setattr__(envelope, "kind", "transcript")
    with pytest.raises(TypeError, match="ObservationKind"):
        _ = envelope.observation_id


def test_stable_observation_identity_remains_deterministic():
    a = _fixture(source_id="sample")
    b = _fixture(source_id="sample")
    assert a.observation_id == b.observation_id
    assert a.observation_id.startswith("obs_")
