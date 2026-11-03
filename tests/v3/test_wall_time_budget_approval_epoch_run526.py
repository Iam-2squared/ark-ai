"""Local-only V3 wall-time approval epoch: no torch, GPU or paid service."""

from __future__ import annotations

import pytest

from ark.learning.runtime_guard import WallTimeBudget


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("started", 99.0),
        ("started", 101.0),
        ("started", 100),
        ("started", True),
        ("started", float("nan")),
        ("timeout_seconds", 3600.0),
        ("timeout_seconds", 0.0),
        ("timeout_seconds", 60),
        ("timeout_seconds", True),
        ("timeout_seconds", float("nan")),
    ),
)
def test_approved_wall_budget_cannot_be_extended_or_rebased(field, replacement):
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("before", now=105.0)
    setattr(budget, field, replacement)
    with pytest.raises(RuntimeError, match="budget changed"):
        budget.check("after-mutation", now=106.0)
    # A detected drift is terminal for this instance even if restored.
    setattr(budget, field, 100.0 if field == "started" else 60.0)
    with pytest.raises(RuntimeError, match="budget was changed"):
        budget.check("restored", now=107.0)


def test_untouched_epoch_retains_exact_boundary_behavior():
    budget = WallTimeBudget(1.0, started=100.0)
    budget.check("first", now=110.0)
    budget.check("at-limit", now=160.0)
    with pytest.raises(RuntimeError, match="timeout exceeded"):
        budget.check("over-limit", now=160.001)
    with pytest.raises(RuntimeError, match="already exceeded"):
        budget.check("second", now=159.0)


def test_readonly_field_inspection_does_not_change_approval():
    budget = WallTimeBudget(1, started=100)
    assert budget.started == 100.0
    assert budget.timeout_seconds == 60.0
    budget.check("inspected", now=105.0)
