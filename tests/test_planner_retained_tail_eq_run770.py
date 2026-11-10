"""Planner retained-prefix equality must use event fields, not __eq__.

This replay-only local SQLite fixture never provides a dispatch grant; a
RUNNING WRITE remains unknown after a crash even with an intact local tail.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
    SyntheticPlanTail,
)


@pytest.mark.parametrize("operation", ("recover", "append"))
@pytest.mark.parametrize("forged", (False, True))
def test_retained_plan_tail_comparison_avoids_rebound_equality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    operation: str, forged: bool,
) -> None:
    steps = (PlanStep(
        "step-one", ToolCall("fixture-reader", "fixture.read", "offline", {}),
    ),)
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", steps)
    genesis = journal.recover().tail
    retained = replace(
        genesis, event_hash=("pevt_" + "f" * 64) if forged else genesis.event_hash,
    )
    invoked: list[bool] = []

    def forbidden_eq(*_args: object, **_kwargs: object) -> bool:
        invoked.append(True)
        raise AssertionError("mutable SyntheticPlanTail.__eq__ executed")

    with monkeypatch.context() as patch:
        patch.setattr(SyntheticPlanTail, "__eq__", forbidden_eq)
        def run():
            if operation == "recover":
                return journal.recover(retained=retained)
            return journal.append(
                "step-one", StepState.RUNNING,
                expected_revision=0, at_ms=100, retained=retained,
            )
        if forged:
            with pytest.raises(
                SyntheticPlanJournalRejected, match="history changed",
            ):
                run()
        else:
            reviewed = run()
            assert reviewed.dispatch_authorized is False
            assert reviewed.automatic_replay_authorized is False

    assert invoked == []
    reopened = SyntheticPlanJournal(tmp_path / "plan.sqlite", steps)
    recovered = reopened.recover()
    assert recovered.tail.event_count == (
        1 if not forged and operation == "append" else 0
    )
    if recovered.tail.event_count:
        assert recovered.ambiguous_running_steps == ("step-one",)
        assert recovered.automatic_replay_authorized is False
