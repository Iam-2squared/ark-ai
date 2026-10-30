"""Validation-only V3 Candidate metric numeric boundaries; no model execution."""

from __future__ import annotations

import math

import pytest

from ark.learning.run_manifest import (
    CandidateRunManifestError,
    _require_finite_number,
)


class FloatCarrier(float):
    def __float__(self):
        raise AssertionError("untrusted float conversion must not run")


class IntCarrier(int):
    def __float__(self):
        raise AssertionError("untrusted int conversion must not run")


@pytest.mark.parametrize("value", [
    10**400,
    -(10**400),
    True,
    False,
    "1.0",
    float("inf"),
    float("-inf"),
    float("nan"),
    FloatCarrier(1.5),
    IntCarrier(12),
    object(),
])
def test_v3_candidate_metric_validation_rejects_unsafe_numbers(value):
    with pytest.raises(CandidateRunManifestError, match="training metrics loss"):
        _require_finite_number({"loss": value}, "loss")


@pytest.mark.parametrize("value", [0, 0.0, -1, -0.01])
def test_v3_candidate_metric_positive_constraint(value):
    with pytest.raises(CandidateRunManifestError, match="finite positive"):
        _require_finite_number({"loss": value}, "loss")


@pytest.mark.parametrize("value", [0, 0.0, 1, 1.5, 10**100])
def test_v3_candidate_metric_valid_finite_numbers(value):
    result = _require_finite_number(
        {"loss": value}, "loss", allow_zero=True,
    )
    assert math.isfinite(result)
    assert result == float(value)


def test_v3_candidate_metric_non_finite_zero_denied():
    with pytest.raises(CandidateRunManifestError, match="finite non-negative"):
        _require_finite_number(
            {"loss": float("nan")}, "loss", allow_zero=True,
        )
