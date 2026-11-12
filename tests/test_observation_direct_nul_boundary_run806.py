"""Direct observation labels obey the same native-boundary rule as fixtures."""

from __future__ import annotations

import hashlib

import pytest

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
def test_direct_envelope_rejects_nul_label(label: str, value: str) -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        _envelope(**{label: value})


def test_unmodified_direct_envelope_identity_still_works() -> None:
    original = _envelope()
    assert original.observation_id.startswith("obs_")
    assert len(original.observation_id) == 68


@pytest.mark.parametrize("label", ["source_id", "adapter_id", "privacy_scope"])
def test_reflected_nul_mutation_rejected_on_identity_read(label: str) -> None:
    original = _envelope()
    object.__setattr__(original, label, "local\x00unsafe")
    with pytest.raises(ValueError, match="NUL separator"):
        _ = original.observation_id


def test_cached_observation_window_detects_reflected_nul_mutation() -> None:
    original = _envelope()
    window = ObservationWindowReview("private", 5, 10, (original,))
    object.__setattr__(original, "privacy_scope", "private\x00foreign")
    with pytest.raises(ValueError):
        window.assert_consistent()
