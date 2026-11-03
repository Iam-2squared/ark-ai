"""Offline V3 time-budget checks reject repeated-clock and timeout replay.

These tests never load torch, call a GPU, create Candidate bytes, or contact
a paid provider; clock samples are caller-supplied synthetic values.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from ark.learning.runtime_guard import WallTimeBudget


class Coercible:
    def __float__(self):
        return 105.0


class FloatSubclass(float):
    pass


@pytest.mark.parametrize(
    "started",
    ("100", Decimal("100"), Coercible(), FloatSubclass(100.0), True),
)
def test_start_must_be_exact_numeric_carrier(started):
    with pytest.raises(ValueError, match="start"):
        WallTimeBudget(1.0, started=started)


@pytest.mark.parametrize(
    "reading",
    ("105", Decimal("105"), Coercible(), FloatSubclass(105.0), False),
)
def test_reading_must_be_exact_numeric_carrier(reading):
    budget = WallTimeBudget(1.0, started=100)
    with pytest.raises(RuntimeError, match="reading"):
        budget.check("synthetic", now=reading)
    budget.check("retry-with-exact-clock", now=105.0)


def test_clock_rollback_after_successful_reading_is_denied():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("first", now=110.0)
    with pytest.raises(RuntimeError, match="backwards"):
        budget.check("rewound", now=109.0)
    budget.check("advance", now=111.0)


def test_once_timeout_seen_budget_cannot_reenter_safe_window():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("first", now=150.0)
    with pytest.raises(RuntimeError, match="timeout exceeded"):
        budget.check("expired", now=161.0)
    with pytest.raises(RuntimeError, match="already exceeded"):
        budget.check("rewound-after-expiry", now=159.0)


def test_identical_successive_readings_remain_allowed():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("first", now=110.0)
    budget.check("same-sample", now=110.0)
    budget.check("later", now=150.0)
