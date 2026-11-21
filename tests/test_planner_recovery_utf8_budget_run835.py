"""Planner recovery recheck refuses malformed detached IDs before digest/IO.

Review-specific resource limits do not modify frozen PlanStep contracts or
turn a detached plan into a trusted command, replay grant, or live executor.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_planner_epoch_recheck as module
from ark.agency.planner_journal_review import (
    SyntheticPlanRecovery,
    SyntheticPlanTail,
)


def _tail() -> SyntheticPlanTail:
    return SyntheticPlanTail(
        "plan_" + "a" * 64, 0, "pevt_" + "b" * 64,
        "pstate_" + "c" * 64, -1,
    )


@pytest.mark.parametrize(("bad_id", "placement"), (
    ("x" * 257, "status"),
    ("あ" * 86, "status"),
    ("\ud800", "status"),
    ("valid\x00id", "status"),
    ("   ", "status"),
    ("x" * 257, "running"),
    ("\ud800", "running"),
))
def test_recovered_id_rejected_before_hash_or_journal_read(
    bad_id: str, placement: str,
) -> None:
    statuses = (
        ((bad_id, "pending", 0),)
        if placement == "status" else (("normal", "pending", 0),)
    )
    running = (bad_id,) if placement == "running" else ()
    recovered = SyntheticPlanRecovery(_tail(), statuses, running)
    with pytest.raises(
        module.PlannerEpochRecheckRejected, match="Planner image malformed",
    ):
        module._recovery_image(recovered)


def test_utf8_byte_budget_does_not_change_frozen_plan_contracts() -> None:
    assert module._valid_recovered_step_id("あ" * 85)
    assert module._valid_recovered_step_id("x" * 256)
    assert not module._valid_recovered_step_id("あ" * 86)
    assert not module._valid_recovered_step_id("x" * 257)


def test_rebound_local_id_validator_denied_before_recovery_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(module, "_valid_recovered_step_id", lambda _: True)
        with pytest.raises(
            module.PlannerEpochRecheckRejected, match="reader epoch changed",
        ):
            module._recovery_image(SyntheticPlanRecovery(_tail(), (), ()))
