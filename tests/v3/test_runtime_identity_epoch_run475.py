"""Pre-paid-compute V3 runtime identity is bound across validation callbacks.

All identities are synthetic; no torch import, GPU, provider or Candidate action.
"""

from __future__ import annotations

import pytest

from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    verify_runtime_identity,
)


def _identity():
    return RuntimeIdentity(
        "sha256:fixture", "3.12", "torch-x", "transformers-x",
        "peft-x", "accelerate-x", "cuda-x", "GPU fixture", 24.0,
        "driver-x",
    )


def _snapshot():
    return {
        "environment": {
            "os_or_image_digest": "sha256:fixture",
            "python": "3.12",
            "torch": "torch-x",
            "transformers": "transformers-x",
            "peft": "peft-x",
            "accelerate": "accelerate-x",
            "cuda_runtime": "cuda-x",
        },
        "hardware": {
            "device": "GPU fixture",
            "driver": "driver-x",
            "vram_gib": 24.0,
        },
    }


def test_matching_snapshot_and_unrelated_metadata_remain_allowed():
    snapshot = _snapshot()
    snapshot["environment"]["extra"] = "review-only"
    snapshot["hardware"]["extra"] = "fixture"
    verify_runtime_identity(snapshot, _identity(), vram_tolerance_gib=0)


@pytest.mark.parametrize(
    "group,key",
    (
        ("environment", "os_or_image_digest"),
        ("environment", "python"),
        ("environment", "cuda_runtime"),
        ("hardware", "device"),
        ("hardware", "driver"),
        ("hardware", "vram_gib"),
    ),
)
def test_missing_frozen_identity_fields_fail_with_gate_error(group, key):
    snapshot = _snapshot()
    del snapshot[group][key]
    with pytest.raises(RuntimeIdentityMismatch, match="incomplete frozen"):
        verify_runtime_identity(snapshot, _identity())


@pytest.mark.parametrize("equal_value", [False, True])
def test_validation_callback_cannot_swap_frozen_environment(
    monkeypatch, equal_value,
):
    snapshot = _snapshot()
    original = RuntimeIdentity.validate

    def mutate(self):
        old = snapshot["environment"]["python"]
        swapped = old.encode().decode() if equal_value else "3.13"
        assert swapped is not old
        snapshot["environment"]["python"] = swapped
        return original(self)

    monkeypatch.setattr(RuntimeIdentity, "validate", mutate)
    with pytest.raises(RuntimeIdentityMismatch, match="epoch changed"):
        verify_runtime_identity(snapshot, _identity())


def test_validation_callback_cannot_replace_nested_snapshot_dict(monkeypatch):
    snapshot = _snapshot()
    original = RuntimeIdentity.validate

    def mutate(self):
        snapshot["hardware"] = dict(snapshot["hardware"])
        return original(self)

    monkeypatch.setattr(RuntimeIdentity, "validate", mutate)
    with pytest.raises(RuntimeIdentityMismatch, match="epoch changed"):
        verify_runtime_identity(snapshot, _identity())


@pytest.mark.parametrize("field", ["python", "driver", "vram_gib"])
def test_measured_identity_cannot_change_inside_validator(monkeypatch, field):
    snapshot = _snapshot()
    actual = _identity()
    original = RuntimeIdentity.validate

    def mutate(self):
        previous = getattr(self, field)
        replacement = (
            previous.encode().decode() if isinstance(previous, str)
            else 24.5
        )
        object.__setattr__(self, field, replacement)
        return original(self)

    monkeypatch.setattr(RuntimeIdentity, "validate", mutate)
    with pytest.raises(RuntimeIdentityMismatch, match="epoch changed"):
        verify_runtime_identity(snapshot, actual)
