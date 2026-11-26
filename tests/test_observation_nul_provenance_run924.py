"""Preserve frozen direct NUL-safe JSON identity; adapter remains stricter.

The v1 ObservationEnvelope contract accepts NUL in labels and escapes it
canonically inside JSON identity hashing. This file is a synthetic regression;
it does not grant capture, export, consent or real backend execution.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
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
@pytest.mark.parametrize("value", ("safe\x00suffix", "\x00"))
def test_frozen_direct_nul_label_keeps_distinct_json_identity(
    field: str, value: str,
) -> None:
    original = _envelope()
    kwargs = {
        "kind": original.kind,
        "source_id": original.source_id,
        "adapter_id": original.adapter_id,
        "privacy_scope": original.privacy_scope,
        "ingested_at_ms": original.ingested_at_ms,
        "content_sha256": original.content_sha256,
    }
    kwargs[field] = value
    with_nul = ObservationEnvelope(**kwargs)
    kwargs[field] = value.replace("\x00", "") or "clean"
    without_nul = ObservationEnvelope(**kwargs)
    assert with_nul.observation_id.startswith("obs_")
    assert len(with_nul.observation_id) == 68
    assert with_nul.observation_id != without_nul.observation_id


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_reflected_nul_remains_bound_to_legacy_hash_identity(field: str) -> None:
    envelope = _envelope()
    before = envelope.observation_id
    object.__setattr__(envelope, field, "local\x00foreign")
    assert envelope.observation_id != before
    assert envelope.observation_id == envelope.observation_id


def test_stricter_fixture_admission_still_rejects_nul_before_hashing() -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        fixture_text_observation(
            "synthetic content",
            kind=ObservationKind.TEXT,
            source_id="local\x00foreign",
            privacy_scope="local-only",
            ingested_at_ms=123,
        )
