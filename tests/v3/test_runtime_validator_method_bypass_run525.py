"""An overridden public runtime validator cannot bypass V3 exact VRAM guards.

Only constructed synthetic identities; no torch imports, GPU or external compute.
"""

import pytest

from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    verify_runtime_identity,
)


def _identity(vram):
    return RuntimeIdentity(
        "local:fixture", "3.12", "torch-fixture", "transformers-fixture",
        "peft-fixture", "accelerate-fixture", "cuda-fixture",
        "GPU fixture", vram, "driver-fixture",
    )


def _snapshot(vram):
    return {
        "environment": {
            "os_or_image_digest": "local:fixture",
            "python": "3.12",
            "torch": "torch-fixture",
            "transformers": "transformers-fixture",
            "peft": "peft-fixture",
            "accelerate": "accelerate-fixture",
            "cuda_runtime": "cuda-fixture",
        },
        "hardware": {
            "device": "GPU fixture",
            "driver": "driver-fixture",
            "vram_gib": vram,
        },
    }


@pytest.mark.parametrize(("measured", "expected"), (
    (0, 0.02),
    (-0.01, 0.01),
    (True, 1.02),
    (False, 0.01),
    ("0.02", 0.02),
))
def test_noop_public_validator_cannot_approve_invalid_measured_vram(
    monkeypatch, measured, expected,
):
    calls = []

    def no_op(self):
        calls.append(self)
        return None

    monkeypatch.setattr(RuntimeIdentity, "validate", no_op)
    actual = _identity(measured)
    with pytest.raises(RuntimeIdentityMismatch, match="measured GPU VRAM"):
        verify_runtime_identity(_snapshot(expected), actual)
    assert calls == [actual]


def test_pinned_validator_still_allows_matching_synthetic_identity(monkeypatch):
    calls = []

    def no_op(self):
        calls.append(self)
        return None

    monkeypatch.setattr(RuntimeIdentity, "validate", no_op)
    actual = _identity(24.0)
    verify_runtime_identity(_snapshot(24.0), actual)
    assert calls == [actual]
