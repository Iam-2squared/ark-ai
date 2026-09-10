import pytest

from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    WallTimeBudget,
    verify_runtime_identity,
)


def snapshot():
    return {
        "environment": {
            "os_or_image_digest": "sha256:image",
            "python": "3.12.10",
            "torch": "2.6.0+cu124",
            "transformers": "4.51.0",
            "peft": "0.15.2",
            "accelerate": "1.6.0",
            "cuda_runtime": "12.4",
        },
        "hardware": {
            "device": "NVIDIA GPU",
            "vram_gib": 24.0,
            "driver": "570.00",
        },
    }


def actual(**overrides):
    values = {
        "os_or_image_digest": "sha256:image",
        "python": "3.12.10",
        "torch": "2.6.0+cu124",
        "transformers": "4.51.0",
        "peft": "0.15.2",
        "accelerate": "1.6.0",
        "cuda_runtime": "12.4",
        "device": "NVIDIA GPU",
        "vram_gib": 24.0,
        "driver": "570.00",
    }
    values.update(overrides)
    return RuntimeIdentity(**values)


def test_exact_runtime_identity_passes():
    verify_runtime_identity(snapshot(), actual())


def test_package_version_mismatch_blocks():
    with pytest.raises(RuntimeIdentityMismatch, match="transformers"):
        verify_runtime_identity(snapshot(), actual(transformers="4.52.0"))


def test_gpu_device_mismatch_blocks():
    with pytest.raises(RuntimeIdentityMismatch, match="GPU device identity"):
        verify_runtime_identity(snapshot(), actual(device="Different GPU"))


def test_gpu_vram_has_small_measurement_tolerance_only():
    verify_runtime_identity(snapshot(), actual(vram_gib=23.97))
    with pytest.raises(RuntimeIdentityMismatch, match="VRAM identity mismatch"):
        verify_runtime_identity(snapshot(), actual(vram_gib=23.8))


def test_driver_mismatch_blocks():
    with pytest.raises(RuntimeIdentityMismatch, match="driver identity"):
        verify_runtime_identity(snapshot(), actual(driver="571.00"))


def test_wall_time_budget_blocks_after_limit():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("setup", now=159.9)
    with pytest.raises(RuntimeError, match="timeout exceeded"):
        budget.check("training", now=160.1)


def test_wall_time_budget_rejects_nonpositive_values():
    with pytest.raises(ValueError, match="positive wall-clock"):
        WallTimeBudget(0)
