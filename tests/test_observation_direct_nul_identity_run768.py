"""Direct observation carriers reject NUL identities like fixture adapters.

Synthetic data only; no device, private media, ToolBackend or network read.
"""

from __future__ import annotations

import pytest

from ark.observations import ObservationEnvelope, ObservationKind


def _valid_envelope(**overrides: object) -> ObservationEnvelope:
    values: dict[str, object] = {
        "kind": ObservationKind.TRANSCRIPT,
        "source_id": "synthetic-source",
        "adapter_id": "fixture:transcript:v1",
        "privacy_scope": "local-only",
        "ingested_at_ms": 1234,
        "content_sha256": "a" * 64,
    }
    values.update(overrides)
    return ObservationEnvelope(**values)


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_direct_envelope_rejects_nul_identity_at_construction(
    field: str,
) -> None:
    # A direct caller does not pass through fixture adapter preflight.
    with pytest.raises(ValueError, match="NUL separator"):
        _valid_envelope(**{field: "safe\\x00hidden".replace("\\x00", "\x00")})


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_reflectively_mutated_direct_envelope_cannot_hash_nul_identity(
    field: str,
) -> None:
    record = _valid_envelope()
    object.__setattr__(record, field, "safe" + chr(0) + "hidden")
    with pytest.raises(ValueError, match="NUL separator"):
        _ = record.observation_id


def test_non_ascii_valid_identity_remains_deterministic() -> None:
    record = _valid_envelope(
        source_id="fixture-日本語",
        privacy_scope="local-試験",
    )
    first = record.observation_id
    assert first.startswith("obs_")
    assert len(first) == 68
    assert record.observation_id == first
