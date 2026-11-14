"""Planner journal topology is fixed across a bounded recovery/append epoch.

The database is a disconnected replay fixture. RUNNING never grants a retry.
"""

from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _journal(path: Path) -> SyntheticPlanJournal:
    return SyntheticPlanJournal(
        path,
        (
            PlanStep("root", ToolCall("fixture", "write", "local", {"n": 1})),
        ),
    )


@pytest.mark.parametrize("operation", ["recover", "append"])
def test_equal_value_steps_tuple_replacement_is_rejected(
    tmp_path: Path, monkeypatch, operation: str,
):
    path = tmp_path / "plan.sqlite"
    journal = _journal(path)
    original = journal._replay
    steps = journal._steps

    def rebind_after_replay(conn):
        result = original(conn)
        journal._steps = tuple([*steps])
        assert journal._steps == steps and journal._steps is not steps
        return result

    monkeypatch.setattr(journal, "_replay", rebind_after_replay)
    with pytest.raises(SyntheticPlanJournalRejected, match="topology changed"):
        if operation == "recover":
            journal.recover()
        else:
            journal.append(
                "root", StepState.RUNNING, expected_revision=0, at_ms=10,
            )
    assert _journal(path).recover().tail.event_count == 0


@pytest.mark.parametrize("operation", ["recover", "append"])
def test_reflectively_changed_nested_action_is_rejected(
    tmp_path: Path, monkeypatch, operation: str,
):
    path = tmp_path / "plan.sqlite"
    journal = _journal(path)
    original = journal._replay
    step = journal._steps[0]
    original_call = step.call

    def mutate_after_replay(conn):
        result = original(conn)
        object.__setattr__(
            step, "call", ToolCall("fixture", "write", "local", {"n": 2}),
        )
        return result

    monkeypatch.setattr(journal, "_replay", mutate_after_replay)
    with pytest.raises(SyntheticPlanJournalRejected, match="topology changed"):
        if operation == "recover":
            journal.recover()
        else:
            journal.append(
                "root", StepState.RUNNING, expected_revision=0, at_ms=10,
            )
    object.__setattr__(step, "call", original_call)
    assert _journal(path).recover().tail.event_count == 0


def test_invalid_steps_carrier_is_rejected_before_open(tmp_path: Path):
    journal = _journal(tmp_path / "plan.sqlite")
    journal._steps = ("not a PlanStep",)
    with pytest.raises(SyntheticPlanJournalRejected, match="topology is invalid"):
        journal.recover()


def test_unchanged_topology_preserves_restart_unknown_semantics(tmp_path: Path):
    path = tmp_path / "plan.sqlite"
    journal = _journal(path)
    initial = journal.recover().tail
    receipt = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10,
        retained=initial,
    )
    restarted = _journal(path).recover(retained=receipt.tail)
    assert restarted.ambiguous_running_steps == ("root",)
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False
