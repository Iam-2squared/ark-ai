import json
from pathlib import Path

import pytest

from ark.observations import ObservationEnvelope, ObservationKind


DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def _envelope(**overrides):
    values = {
        "kind": ObservationKind.TRANSCRIPT,
        "source_id": "source",
        "adapter_id": "adapter-v1",
        "privacy_scope": "local:test",
        "ingested_at_ms": 1,
        "content_sha256": DIGEST_A,
        "parent_sha256": DIGEST_B,
    }
    values.update(overrides)
    return ObservationEnvelope(**values)


def test_fixture_identity_matches_frozen_vector():
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "observation_envelope_v1.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    envelope = ObservationEnvelope(
        kind=ObservationKind(fixture["kind"]),
        source_id=fixture["source_id"],
        adapter_id=fixture["adapter_id"],
        privacy_scope=fixture["privacy_scope"],
        ingested_at_ms=fixture["ingested_at_ms"],
        content_sha256=fixture["content_sha256"],
        parent_sha256=fixture["parent_sha256"],
        schema_version=fixture["schema_version"],
    )
    assert envelope.observation_id == fixture["expected_observation_id"]


def test_kind_requires_exact_enum():
    with pytest.raises(TypeError, match="exact ObservationKind"):
        _envelope(kind="transcript")


@pytest.mark.parametrize("field", ["source_id", "adapter_id", "privacy_scope"])
def test_provenance_text_rejects_subclasses(field):
    class TextAlias(str):
        pass

    with pytest.raises(ValueError, match="exact string"):
        _envelope(**{field: TextAlias("value")})


def test_timestamp_rejects_bool():
    with pytest.raises(ValueError, match="exact integer"):
        _envelope(ingested_at_ms=True)


@pytest.mark.parametrize("field", ["content_sha256", "parent_sha256"])
def test_digest_rejects_string_subclasses(field):
    class DigestAlias(str):
        pass

    with pytest.raises(ValueError, match="exact lowercase SHA-256"):
        _envelope(**{field: DigestAlias(DIGEST_A)})


def test_schema_version_rejects_bool():
    with pytest.raises(ValueError, match="exact integer 1"):
        _envelope(schema_version=True)


def test_identity_changes_when_bound_field_changes():
    base = _envelope()
    assert _envelope(source_id="other").observation_id != base.observation_id
    assert _envelope(adapter_id="other").observation_id != base.observation_id
    assert _envelope(privacy_scope="other").observation_id != base.observation_id
    assert _envelope(ingested_at_ms=2).observation_id != base.observation_id
    assert _envelope(content_sha256="c" * 64).observation_id != base.observation_id
    assert _envelope(parent_sha256=None).observation_id != base.observation_id


def test_envelope_contains_no_raw_media_or_action_authority():
    envelope = _envelope()
    assert not hasattr(envelope, "raw_bytes")
    assert not hasattr(envelope, "capability")
    assert not hasattr(envelope, "authorization")
    assert not hasattr(envelope, "token")
