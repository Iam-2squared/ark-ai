"""Direct observation ingress must match privacy-safe fixture NUL admission."""

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(**overrides: object) -> ObservationEnvelope:
    fields = {
        "kind": ObservationKind.TEXT,
        "source_id": "offline:source",
        "adapter_id": "fixture:text:v1",
        "privacy_scope": "offline:private",
        "ingested_at_ms": 100,
        "content_sha256": "a" * 64,
    }
    fields.update(overrides)
    return ObservationEnvelope(**fields)


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_direct_observation_rejects_native_nul_identity(field: str) -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        _envelope(**{field: "clean\x00hidden"})


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_reflected_nul_is_rejected_before_direct_identity_hash(field: str) -> None:
    observation = _envelope()
    object.__setattr__(observation, field, "clean\x00hidden")
    with pytest.raises(ValueError, match="NUL separator"):
        _ = observation.observation_id


def test_valid_multibyte_provenance_remains_deterministic_without_raw_media() -> None:
    fields = {
        "source_id": "端末内の観測",
        "adapter_id": "fixture:text:v1",
        "privacy_scope": "非公開:検証",
    }
    a, b = _envelope(**fields), _envelope(**fields)
    assert a.observation_id == b.observation_id
    assert a.observation_id.startswith("obs_")
    assert not hasattr(a, "raw_bytes")
    assert not hasattr(a, "authorization")


def test_existing_disconnected_fixture_enforces_same_nul_boundary() -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        fixture_text_observation(
            "synthetic only",
            kind=ObservationKind.TEXT,
            source_id="offline\x00untrusted",
            privacy_scope="offline:private",
            ingested_at_ms=100,
        )
