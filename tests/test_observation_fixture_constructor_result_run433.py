"""Disconnection-safe fixture construction must not mint retargeted evidence."""

import hashlib

import pytest

import ark.observation_fixture_adapters as adapters
from ark.observations import ObservationEnvelope, ObservationKind


def _produce(binary):
    if binary:
        return adapters.fixture_binary_observation(
            b"offline-test-bytes",
            kind=ObservationKind.SCREEN,
            source_id="local-screen-fixture",
            privacy_scope="owner:private",
            ingested_at_ms=123,
            parent_sha256="a" * 64,
        )
    return adapters.fixture_text_observation(
        "offline-test-text",
        kind=ObservationKind.TEXT,
        source_id="local-text-fixture",
        privacy_scope="owner:private",
        ingested_at_ms=123,
        parent_sha256="a" * 64,
    )


@pytest.mark.parametrize("binary", [False, True])
def test_fixture_constructor_unchanged_retains_digest_and_scope(binary):
    witness = _produce(binary)
    expected = b"offline-test-bytes" if binary else b"offline-test-text"
    assert witness.content_sha256 == hashlib.sha256(expected).hexdigest()
    assert witness.privacy_scope == "owner:private"
    assert witness.parent_sha256 == "a" * 64
    assert witness.schema_version == 1
    assert witness.observation_id.startswith("obs_")
    assert not hasattr(witness, "raw_bytes")
    assert not hasattr(witness, "text")


@pytest.mark.parametrize("binary", [False, True])
@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("kind", ObservationKind.TRANSCRIPT),
        ("source_id", "substituted-source"),
        ("adapter_id", "fixture:forged:v1"),
        ("privacy_scope", "owner:other"),
        ("ingested_at_ms", 124),
        ("content_sha256", "b" * 64),
        ("parent_sha256", "c" * 64),
        ("schema_version", 2),
    ],
)
def test_fixture_rejects_post_validation_field_retarget(
    binary, field, replacement, monkeypatch,
):
    previous = ObservationEnvelope.__post_init__

    def retarget(self):
        previous(self)
        object.__setattr__(self, field, replacement)

    monkeypatch.setattr(ObservationEnvelope, "__post_init__", retarget)
    with pytest.raises(ValueError, match="changed during construction"):
        _produce(binary)


@pytest.mark.parametrize("binary", [False, True])
@pytest.mark.parametrize("field", ["source_id", "privacy_scope", "content_sha256"])
def test_fixture_rejects_equal_value_carrier_replacement(
    binary, field, monkeypatch,
):
    previous = ObservationEnvelope.__post_init__

    def retarget(self):
        previous(self)
        original = getattr(self, field)
        replacement = "".join([original[: len(original) // 2],
                               original[len(original) // 2 :]])
        assert replacement == original
        assert replacement is not original
        object.__setattr__(self, field, replacement)

    monkeypatch.setattr(ObservationEnvelope, "__post_init__", retarget)
    with pytest.raises(ValueError, match="changed during construction"):
        _produce(binary)


@pytest.mark.parametrize("binary", [False, True])
def test_fixture_rejects_non_envelope_constructor_result(binary, monkeypatch):
    monkeypatch.setattr(adapters, "ObservationEnvelope", lambda **_kwargs: {})
    with pytest.raises(ValueError, match="non-envelope"):
        _produce(binary)
