"""Compatibility regression: frozen direct NUL identity versus fixture veto.

Frozen direct ObservationEnvelope v1 encodes NUL unambiguously into JSON and
must retain that behavior. Only opt-in fixture adapters reject native NUL.
No media acquisition, dispatch or real private data is involved.
"""

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
def test_frozen_direct_v1_retains_nul_as_distinct_json_identity(field: str) -> None:
    nul = _envelope(**{field: "clean\x00hidden"})
    plain = _envelope(**{field: "cleanhidden"})
    assert nul.observation_id != plain.observation_id
    assert nul.observation_id.startswith("obs_")


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_reflected_nul_change_remains_distinct_in_frozen_identity(field: str) -> None:
    observation = _envelope()
    before = observation.observation_id
    object.__setattr__(observation, field, "clean\x00hidden")
    assert observation.observation_id != before


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


def test_optin_disconnected_fixture_rejects_nul_without_changing_v1() -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        fixture_text_observation(
            "synthetic only",
            kind=ObservationKind.TEXT,
            source_id="offline\x00untrusted",
            privacy_scope="offline:private",
            ingested_at_ms=100,
        )
