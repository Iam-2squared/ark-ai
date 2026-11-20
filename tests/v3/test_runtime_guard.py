import math

import pytest

import ark.learning.runtime_guard as runtime_guard
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


def test_wall_time_budget_rejects_nonfinite_values():
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="finite positive wall-clock"):
            WallTimeBudget(value)

    with pytest.raises(ValueError, match="finite wall-clock start"):
        WallTimeBudget(1.0, started=math.nan)

    budget = WallTimeBudget(1.0, started=100.0)
    with pytest.raises(RuntimeError, match="finite wall-clock reading"):
        budget.check("training", now=math.inf)



@pytest.mark.parametrize("bad_vram", [float("nan"), float("inf"), float("-inf"), True, 0])
def test_measured_runtime_vram_must_be_finite_positive(bad_vram):
    with pytest.raises(RuntimeIdentityMismatch, match="measured GPU VRAM"):
        verify_runtime_identity(snapshot(), actual(vram_gib=bad_vram))


def test_frozen_runtime_vram_must_be_finite_positive():
    frozen = snapshot()
    frozen["hardware"]["vram_gib"] = float("nan")
    with pytest.raises(RuntimeIdentityMismatch, match="frozen GPU VRAM"):
        verify_runtime_identity(frozen, actual())


def test_runtime_text_identity_must_not_coerce_non_strings():
    with pytest.raises(RuntimeIdentityMismatch, match="python"):
        verify_runtime_identity(snapshot(), actual(python=312))


@pytest.mark.parametrize("bad_tolerance", [float("nan"), float("inf"), -0.1, True])
def test_vram_tolerance_must_be_finite_non_negative(bad_tolerance):
    with pytest.raises(ValueError, match="finite non-negative VRAM tolerance"):
        verify_runtime_identity(snapshot(), actual(), vram_tolerance_gib=bad_tolerance)


@pytest.mark.parametrize(
    "phase",
    ("", "   ", "x" * 129, "bad\x00phase", "line\nbreak", "\ud800", "é" * 65),
    ids=(
        "empty", "blank", "codepoint-budget", "nul", "control",
        "invalid-utf8", "utf8-byte-budget",
    ),
)
def test_invalid_phase_label_is_denied_without_rewinding_clock_cursor(phase):
    budget = WallTimeBudget(1.0, started=100.0)
    with pytest.raises(RuntimeError, match="phase"):
        budget.check(phase, now=110.0)
    # Invalid diagnostic input still consumes the monotonic sample; it cannot
    # be used to hide a later clock rollback or retry an earlier phase.
    with pytest.raises(RuntimeError, match="backwards"):
        budget.check("valid-phase", now=109.0)
    budget.check("valid-phase", now=111.0)


def test_hostile_phase_formatters_never_run_and_cannot_hide_timeout():
    class HostilePhase:
        def __str__(self):
            raise AssertionError("phase __str__ callback ran")

        def __format__(self, _spec):
            raise AssertionError("phase __format__ callback ran")

    budget = WallTimeBudget(1.0, started=100.0)
    with pytest.raises(RuntimeError, match="phase"):
        budget.check(HostilePhase(), now=110.0)
    with pytest.raises(RuntimeError, match="timeout exceeded"):
        budget.check(HostilePhase(), now=161.0)
    assert budget._timed_out is True
    with pytest.raises(RuntimeError, match="already exceeded"):
        budget.check("valid-phase", now=159.0)


def test_phase_budget_rebinding_denies_label_but_still_advances_clock(monkeypatch):
    budget = WallTimeBudget(1.0, started=100.0)
    monkeypatch.setattr(runtime_guard, "_MAX_WALL_TIME_PHASE_BYTES", 129)
    with pytest.raises(RuntimeError, match="phase"):
        budget.check("valid-phase", now=110.0)
    with pytest.raises(RuntimeError, match="backwards"):
        budget.check("valid-phase", now=109.0)


def test_exact_utf8_phase_byte_boundary_is_accepted():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("é" * 64, now=110.0)
