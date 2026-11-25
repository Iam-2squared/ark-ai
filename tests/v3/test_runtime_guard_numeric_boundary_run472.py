"""V3 free-only identity and trusted-budget shape checks.

No GPU import, training, provider contact, preflight, or Candidate creation.
"""

from __future__ import annotations

import pytest

from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    WallTimeBudget,
    verify_runtime_identity,
)


def _measured(vram=24.0):
    return RuntimeIdentity(
        os_or_image_digest="sha256:fixture",
        python="3.12",
        torch="2.fixture",
        transformers="4.fixture",
        peft="0.fixture",
        accelerate="1.fixture",
        cuda_runtime="12.fixture",
        device="Mock GPU",
        vram_gib=vram,
        driver="fixture-driver",
    )


def _snapshot():
    return {
        "environment": {
            "os_or_image_digest": "sha256:fixture",
            "python": "3.12",
            "torch": "2.fixture",
            "transformers": "4.fixture",
            "peft": "0.fixture",
            "accelerate": "1.fixture",
            "cuda_runtime": "12.fixture",
        },
        "hardware": {
            "device": "Mock GPU",
            "driver": "fixture-driver",
            "vram_gib": 24.0,
        },
    }


def test_regular_mock_runtime_identity_and_tolerance_remain_valid():
    _measured().validate()
    verify_runtime_identity(_snapshot(), _measured(), vram_tolerance_gib=0.0)


@pytest.mark.parametrize("value", (10**1000, float("inf"), float("nan")))
def test_measured_vram_invalid_number_rejected_before_runtime(value):
    with pytest.raises(RuntimeIdentityMismatch, match="VRAM"):
        _measured(value).validate()


@pytest.mark.parametrize("tolerance", (True, False, 10**1000, -1, float("nan")))
def test_vram_tolerance_must_be_finite_and_nonnegative(tolerance):
    with pytest.raises(ValueError, match="tolerance"):
        verify_runtime_identity(
            _snapshot(), _measured(), vram_tolerance_gib=tolerance,
        )


def test_valid_wall_budget_preserves_elapsed_and_backward_guards():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("before", now=115.0)
    with pytest.raises(RuntimeError, match="backwards"):
        budget.check("rollback", now=99.0)
    with pytest.raises(RuntimeError, match="timeout exceeded"):
        budget.check("late", now=161.0)


@pytest.mark.parametrize("start", (True, False, 10**1000, float("nan"), float("inf")))
def test_invalid_monotonic_start_fails_closed(start):
    with pytest.raises(ValueError, match="start"):
        WallTimeBudget(1.0, started=start)


@pytest.mark.parametrize("reading", (True, False, 10**1000, float("nan"), float("inf")))
def test_invalid_monotonic_reading_fails_closed(reading):
    budget = WallTimeBudget(1.0, started=100.0)
    with pytest.raises(RuntimeError, match="reading"):
        budget.check("before", now=reading)


def test_elapsed_overflow_fails_closed_even_for_finite_samples():
    budget = WallTimeBudget(1.0, started=-1e308)
    with pytest.raises(RuntimeError, match="elapsed"):
        budget.check("overflow", now=1e308)


def test_huge_timeout_minutes_still_rejected_before_runtime():
    with pytest.raises(ValueError, match="seconds overflow"):
        WallTimeBudget(1e308, started=0)
