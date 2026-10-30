"""Synthetic V3 identity rechecks reject required field deletion.

No GPU discovery, training, provider calls or Candidate generation occurs.
"""

from __future__ import annotations

import pytest

from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    verify_runtime_identity,
)


def _actual():
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


@pytest.mark.parametrize("group,key", (
    ("environment", "os_or_image_digest"),
    ("environment", "python"),
    ("environment", "cuda_runtime"),
    ("hardware", "device"),
    ("hardware", "driver"),
    ("hardware", "vram_gib"),
))
def test_disappearing_frozen_snapshot_identity_fails_closed(
    monkeypatch, group, key,
):
    snapshot = _snapshot()
    original = RuntimeIdentity.validate

    def after_validation(self):
        original(self)
        del snapshot[group][key]

    monkeypatch.setattr(RuntimeIdentity, "validate", after_validation)
    with pytest.raises(RuntimeIdentityMismatch, match="epoch changed"):
        verify_runtime_identity(snapshot, _actual())


@pytest.mark.parametrize("field", ("python", "driver", "vram_gib"))
def test_disappearing_measured_identity_fails_closed(monkeypatch, field):
    actual = _actual()
    original = RuntimeIdentity.validate

    def after_validation(self):
        original(self)
        object.__delattr__(self, field)

    monkeypatch.setattr(RuntimeIdentity, "validate", after_validation)
    with pytest.raises(RuntimeIdentityMismatch, match="epoch changed"):
        verify_runtime_identity(_snapshot(), actual)


def test_unmodified_identity_still_matches():
    verify_runtime_identity(_snapshot(), _actual(), vram_tolerance_gib=0)
