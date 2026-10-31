"""Local-only V3 pre-paid-compute runtime identity spoofing regressions.

No GPU, network call, Candidate, preflight or model weights are used.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    verify_runtime_identity,
)


class ForgivingText(str):
    """A string subclass that can falsely compare equal to any real identity."""

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = str.__hash__


class ForgedMeasuredRuntime(RuntimeIdentity):
    def validate(self):
        return None


class ForgedSnapshotMap(dict):
    pass


def _runtime():
    return RuntimeIdentity(
        "sha256:fixture", "3.12", "torch-x", "transformers-x",
        "peft-x", "accelerate-x", "cuda-x", "GPU fixture", 24.0, "driver-x",
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


@pytest.mark.parametrize(
    "field",
    (
        "os_or_image_digest", "python", "torch", "transformers",
        "peft", "accelerate", "cuda_runtime", "device", "driver",
    ),
)
def test_measured_identity_string_subclass_is_not_authority(field):
    measured = replace(_runtime(), **{field: ForgivingText("wrong")})
    with pytest.raises(RuntimeIdentityMismatch, match="measured runtime identity"):
        verify_runtime_identity(_snapshot(), measured)


@pytest.mark.parametrize("field", (
    "os_or_image_digest", "python", "torch", "transformers",
    "peft", "accelerate", "cuda_runtime",
))
def test_frozen_environment_string_subclass_is_rejected(field):
    snapshot = _snapshot()
    snapshot["environment"][field] = ForgivingText("wrong")
    with pytest.raises(RuntimeIdentityMismatch, match="frozen runtime identity"):
        verify_runtime_identity(snapshot, _runtime())


@pytest.mark.parametrize("field", ("device", "driver"))
def test_frozen_hardware_string_subclass_cannot_fake_equality(field):
    snapshot = _snapshot()
    snapshot["hardware"][field] = ForgivingText("different")
    with pytest.raises(RuntimeIdentityMismatch, match="frozen GPU"):
        verify_runtime_identity(snapshot, _runtime())


def test_measured_runtime_subclass_cannot_override_validation():
    ordinary = _runtime()
    forged = ForgedMeasuredRuntime(
        ordinary.os_or_image_digest, ordinary.python, ordinary.torch,
        ordinary.transformers, ordinary.peft, ordinary.accelerate,
        ordinary.cuda_runtime, "OTHER GPU", ordinary.vram_gib, ordinary.driver,
    )
    with pytest.raises(RuntimeIdentityMismatch, match="exact measured"):
        verify_runtime_identity(_snapshot(), forged)


@pytest.mark.parametrize("level", ("root", "environment", "hardware"))
def test_snapshot_dict_subclasses_cannot_override_getitem(level):
    snapshot = _snapshot()
    if level == "root":
        snapshot = ForgedSnapshotMap(snapshot)
    else:
        snapshot[level] = ForgedSnapshotMap(snapshot[level])
    with pytest.raises(RuntimeIdentityMismatch, match="identity container"):
        verify_runtime_identity(snapshot, _runtime())


def test_exact_valid_runtime_identity_still_matches():
    verify_runtime_identity(_snapshot(), _runtime(), vram_tolerance_gib=0.0)
