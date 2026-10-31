"""Post-validator fixture mutation must never be returned as source custody."""

import hashlib

import pytest

import ark.observation_fixture_adapters as adapters
from ark.observations import ObservationKind


def _fixture(binary):
    if binary:
        return adapters.fixture_binary_observation(
            b"\x89PNG disconnected fixture", kind=ObservationKind.IMAGE,
            source_id="source", privacy_scope="local:original",
            ingested_at_ms=12,
        )
    return adapters.fixture_text_observation(
        "disconnected transcript", kind=ObservationKind.TRANSCRIPT,
        source_id="source", privacy_scope="local:original",
        ingested_at_ms=12,
    )


@pytest.mark.parametrize("binary", [False, True])
@pytest.mark.parametrize("name,value", [
    ("source_id", "source:retargeted"),
    ("privacy_scope", "local:unrestricted"),
    ("ingested_at_ms", 13),
    ("content_sha256", "f" * 64),
    ("schema_version", 2),
])
def test_independent_validator_cannot_retarget_output(
    monkeypatch, binary, name, value,
):
    original = adapters._VALIDATE_ENVELOPE

    def mutating_validator(envelope):
        original(envelope)
        object.__setattr__(envelope, name, value)

    monkeypatch.setattr(adapters, "_VALIDATE_ENVELOPE", mutating_validator)
    with pytest.raises(ValueError, match="changed during validation"):
        _fixture(binary)


@pytest.mark.parametrize("binary", [False, True])
def test_unchanged_validator_retains_exact_fixture_identity(binary):
    observed = _fixture(binary)
    assert observed.source_id == "source"
    assert observed.privacy_scope == "local:original"
    assert observed.ingested_at_ms == 12
    if binary:
        assert observed.content_sha256 == hashlib.sha256(
            b"\x89PNG disconnected fixture"
        ).hexdigest()
    else:
        assert observed.content_sha256 == hashlib.sha256(
            b"disconnected transcript"
        ).hexdigest()
    assert observed.schema_version == 1
