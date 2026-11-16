"""Disconnected observation metadata must reject NUL-ambiguous identity labels.

Synthetic envelopes only: no microphone, screen, network, user profile or
real ToolBackend access. These cases certify neither consent nor provenance.
"""

from __future__ import annotations

import pytest

from ark.observations import ObservationEnvelope, ObservationKind


def _envelope() -> ObservationEnvelope:
    return ObservationEnvelope(
        ObservationKind.TEXT,
        "synthetic-source",
        "fixture-adapter",
        "local-only",
        123,
        "a" * 64,
    )


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
@pytest.mark.parametrize("value", ("safe\\x00suffix", "\\x00"))
def test_nul_identifier_rejected_before_observation_identity(field: str, value: str) -> None:
    original = _envelope()
    kwargs = {
        "kind": original.kind,
        "source_id": original.source_id,
        "adapter_id": original.adapter_id,
        "privacy_scope": original.privacy_scope,
        "ingested_at_ms": original.ingested_at_ms,
        "content_sha256": original.content_sha256,
    }
    kwargs[field] = value.replace("\\x00", "\x00")
    with pytest.raises(ValueError, match="NUL separator"):
        ObservationEnvelope(**kwargs)


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_reflected_nul_mutation_cannot_acquire_observation_id(field: str) -> None:
    envelope = _envelope()
    object.__setattr__(envelope, field, "local\x00forged")
    with pytest.raises(ValueError, match="NUL separator"):
        _ = envelope.observation_id


def test_bounded_synthetic_observation_identity_remains_deterministic() -> None:
    a, b = _envelope(), _envelope()
    assert a.observation_id == b.observation_id
    assert a.observation_id.startswith("obs_")
    assert len(a.observation_id) == 68
