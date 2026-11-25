"""V3 numeric and unit-conversion guards are validation-only and fail closed."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.execution import ExecutionBlocked, _require_positive_number
from ark.learning.preflight import PreflightEvidence, verify_preflight_measurements
from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    WallTimeBudget,
    verify_runtime_identity,
)


def _runtime(vram=24.0):
    return RuntimeIdentity(
        os_or_image_digest="image@sha256:abc",
        python="3.12.10",
        torch="2.6.0+cu124",
        transformers="4.51.0",
        peft="0.15.2",
        accelerate="1.6.0",
        cuda_runtime="12.4",
        device="synthetic-GPU",
        vram_gib=vram,
        driver="570.00",
    )


def _snapshot(vram=24.0, minutes=60.0):
    runtime = _runtime(vram)
    return {
        "environment": {
            name: getattr(runtime, name)
            for name in (
                "os_or_image_digest", "python", "torch", "transformers",
                "peft", "accelerate", "cuda_runtime",
            )
        },
        "hardware": {"device": runtime.device, "vram_gib": vram, "driver": runtime.driver},
        "tokenizer": {"chat_template_probe_sha256": "a" * 64},
        "budget": {"wall_clock_timeout_minutes": minutes},
    }


def _evidence(vram=24.0):
    return PreflightEvidence(
        device="synthetic-GPU",
        vram_gib=vram,
        base_loaded=True,
        tokenizer_probe_sha256="a" * 64,
        forward_backward_ok=True,
        optimizer_step_ok=True,
        peak_vram_mib=1024.0,
        peak_reserved_vram_mib=2048.0,
        wall_seconds=1.0,
    )


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("hardware.vram_gib", 1e308),
        ("budget.wall_clock_timeout_minutes", 1e308),
        ("budget.max_cost_jpy", 10**400),
        ("hardware.vram_gib", 10**400),
    ],
)
def test_snapshot_number_or_derived_unit_overflow_rejected(field, bad):
    with pytest.raises(ExecutionBlocked, match="finite positive numeric"):
        _require_positive_number(bad, field)


def test_finite_frozen_snapshot_numbers_remain_valid():
    for value, field in (
        (24.0, "hardware.vram_gib"),
        (60, "budget.wall_clock_timeout_minutes"),
        (1000, "budget.max_cost_jpy"),
    ):
        _require_positive_number(value, field)


@pytest.mark.parametrize("bad", [1e308, 10**400])
def test_wall_budget_rejects_overflow_before_any_timer_read(bad):
    with pytest.raises(ValueError, match="wall-clock"):
        WallTimeBudget(bad, started=0)


@pytest.mark.parametrize("bad", [10**400, True])
def test_preflight_evidence_rejects_noncanonical_numeric_carrier(bad):
    with pytest.raises(ValueError, match="finite positive preflight"):
        replace(_evidence(), peak_reserved_vram_mib=bad).validate()


def test_measured_runtime_rejects_unrepresentable_large_vram_integer():
    with pytest.raises(RuntimeIdentityMismatch, match="measured GPU VRAM"):
        verify_runtime_identity(_snapshot(), _runtime(10**400))


def test_frozen_snapshot_rejects_unrepresentable_large_vram_integer():
    with pytest.raises(RuntimeIdentityMismatch, match="frozen GPU VRAM"):
        verify_runtime_identity(_snapshot(vram=10**400), _runtime())


def test_preflight_rejects_infinite_derived_capacity_from_finite_gib():
    with pytest.raises(ValueError, match="capacity conversion overflow"):
        verify_preflight_measurements(
            _snapshot(vram=1e308), _evidence(vram=1e308), _runtime(vram=1e308),
        )


def test_preflight_rejects_infinite_derived_wall_seconds():
    with pytest.raises(ValueError, match="budget conversion overflow"):
        verify_preflight_measurements(
            _snapshot(minutes=1e308), _evidence(), _runtime(),
        )


def test_normal_synthetic_preflight_stays_validation_only():
    verify_preflight_measurements(_snapshot(), _evidence(), _runtime())
