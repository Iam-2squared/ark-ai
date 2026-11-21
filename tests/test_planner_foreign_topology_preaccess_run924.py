"""Planner journal rejects foreign topology before step getters or SQLite.

Only disposable synthetic plan graphs are used. RUNNING on recovery is
ambiguous and does not authorize automatic execution or external tools.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _journal(tmp_path):
    step = PlanStep("read", ToolCall("fixture.read", "fixture.read", "local"))
    return SyntheticPlanJournal(tmp_path / "plan.sqlite", (step,)), step


@pytest.mark.parametrize("corruption", ("foreign_step", "tuple_subclass", "oversized"))
def test_reflected_topology_rejected_before_step_property_or_sqlite(
    tmp_path, corruption: str,
) -> None:
    journal, step = _journal(tmp_path)
    touched = []

    class ForeignStep:
        @property
        def step_id(self):
            touched.append("foreign-getter")
            raise AssertionError("untrusted step getter was invoked")

    class ForeignTuple(tuple):
        def __len__(self):
            touched.append("foreign-len")
            raise AssertionError("untrusted tuple length was invoked")

    if corruption == "foreign_step":
        journal._steps = (ForeignStep(),)
    elif corruption == "tuple_subclass":
        journal._steps = ForeignTuple((step,))
    else:
        journal._steps = (step,) * 4097

    def never_open(*_args, **_kwargs):
        touched.append("sqlite-connect")
        raise AssertionError("invalid topology reached SQLite")

    journal._connect = never_open
    with pytest.raises(SyntheticPlanJournalRejected, match="topology is invalid"):
        journal.append("read", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert touched == []


def test_normal_disconnected_plan_append_retains_unknown_without_dispatch(tmp_path) -> None:
    journal, _step = _journal(tmp_path)
    report = journal.append("read", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert report.ambiguous_running_steps == ("read",)
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    restarted = journal.recover()
    assert restarted.ambiguous_running_steps == ("read",)
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False
