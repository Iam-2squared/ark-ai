"""Preserve frozen v1 envelope identity while adapters block ambiguous NUL.

The v1 ObservationEnvelope can carry NUL-bearing synthetic labels, but the
opt-in fixture adapter must reject them before hashing caller-owned bytes.
No media device, network, or ToolBackend is accessed.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationEnvelope, ObservationKind


def _legacy_envelope(**overrides: object) -> ObservationEnvelope:
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
def test_frozen_v1_envelope_retains_nul_label_identity(field: str) -> None:
    # Do not tighten frozen v1 constructor semantics. The stricter adapter
    # ingress gate is separate and cannot rewrite historical envelope IDs.
    label = "synthetic" + chr(0) + "legacy"
    envelope = _legacy_envelope(**{field: label})
    result = envelope.observation_id
    assert result.startswith("obs_")
    assert len(result) == 68
    assert envelope.observation_id == result


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_new_adapter_does_not_hash_nul_label(field: str) -> None:
    values = {"source_id": "synthetic", "privacy_scope": "local-only"}
    values[field] = "synthetic" + chr(0) + "trailer"
    with pytest.raises(ValueError, match="NUL separator"):
        fixture_text_observation(
            "private synthetic text",
            kind=ObservationKind.TRANSCRIPT,
            ingested_at_ms=1234,
            **values,
        )


def test_frozen_v1_unicode_identity_remains_deterministic() -> None:
    record = _legacy_envelope(
        source_id="fixture-日本語",
        privacy_scope="local-試験",
    )
    first = record.observation_id
    assert first.startswith("obs_")
    assert len(first) == 68
    assert record.observation_id == first
