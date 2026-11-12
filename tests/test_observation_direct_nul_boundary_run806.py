"""Preserve frozen direct envelope NUL identity; deny adapter framing.

The historical v1 envelope uses deterministic JSON framing, which safely
distinguishes embedded NUL. Disconnected fixture adapters and chain reviews
keep their stricter ingress policy without changing frozen v1 behavior.
No sensor, network, backend or human permission is exercised.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(**changes: object) -> ObservationEnvelope:
    values = {
        "kind": ObservationKind.TEXT,
        "source_id": "local-source",
        "adapter_id": "fixture",
        "privacy_scope": "private",
        "ingested_at_ms": 5,
        "content_sha256": hashlib.sha256(b"fixture").hexdigest(),
    }
    values.update(changes)
    return ObservationEnvelope(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("label", ["source_id", "adapter_id", "privacy_scope"])
@pytest.mark.parametrize("value", ["\x00", "prefix\x00suffix", "\x00suffix"])
def test_frozen_direct_envelope_retains_nul_json_identity(
    label: str, value: str,
) -> None:
    # The v1 public envelope is intentionally not the strict adapter boundary.
    with_nul = _envelope(**{label: value})
    without_nul = _envelope(**{label: value.replace("\x00", "")})
    identity = with_nul.observation_id
    assert identity.startswith("obs_")
    assert len(identity) == 68
    assert with_nul.observation_id == identity
    assert identity != without_nul.observation_id


@pytest.mark.parametrize("label", ["source_id", "privacy_scope"])
@pytest.mark.parametrize("value", ["\x00", "prefix\x00suffix", "\x00suffix"])
def test_stricter_fixture_adapter_still_denies_nul_before_hashing(
    label: str, value: str,
) -> None:
    fields = {"source_id": "local-source", "privacy_scope": "private"}
    fields[label] = value
    with pytest.raises(ValueError, match="NUL separator"):
        fixture_text_observation(
            "synthetic only", kind=ObservationKind.TEXT,
            ingested_at_ms=5, **fields,
        )


def test_unmodified_direct_envelope_identity_still_works() -> None:
    original = _envelope()
    assert original.observation_id.startswith("obs_")
    assert len(original.observation_id) == 68


@pytest.mark.parametrize("label", ["source_id", "adapter_id", "privacy_scope"])
def test_reflected_nul_mutation_changes_legacy_hash_identity(label: str) -> None:
    original = _envelope()
    first = original.observation_id
    object.__setattr__(original, label, "local\x00unsafe")
    second = original.observation_id
    assert second != first
    assert second == original.observation_id


def test_cached_observation_window_detects_reflected_nul_mutation() -> None:
    original = _envelope()
    window = ObservationWindowReview("private", 5, 10, (original,))
    object.__setattr__(original, "privacy_scope", "private\x00foreign")
    with pytest.raises(ValueError):
        window.assert_consistent()
