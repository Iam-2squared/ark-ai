"""Synthetic Planner append must preserve retained history through snapshot callbacks.

A matching local SQLite tail cannot certify a trusted external writer, and a
RUNNING result never licenses replay of an uncertain external WRITE.
"""

import pytest

import ark.agency.planner_journal_review as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("topology_digest", "plan_" + "0" * 64),
        ("event_hash", "pevt_" + "0" * 64),
        ("status_digest", "pstate_" + "0" * 64),
    ),
)
def test_append_snapshot_callback_cannot_rebase_retained_history_before_commit(
    tmp_path, monkeypatch, field, replacement,
):
    step = PlanStep(
        "fixture-step",
        ToolCall("fixture-tool", "fixture-capability", "fixture-scope"),
    )
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", (step,))
    retained = journal.recover().tail
    original = getattr(retained, field)
    real_snapshot = journal_module._snapshot
    calls = 0

    def reflected_snapshot(graph, tail):
        nonlocal calls
        result = real_snapshot(graph, tail)
        calls += 1
        # This callback runs after the append's previous retained-tail check,
        # after the event/header INSERTs, but before transaction COMMIT.
        object.__setattr__(retained, field, replacement)
        return result

    monkeypatch.setattr(journal_module, "_snapshot", reflected_snapshot)
    with pytest.raises(
        SyntheticPlanJournalRejected,
        match="retained synthetic plan witness changed during append",
    ):
        journal.append(
            "fixture-step", StepState.RUNNING,
            expected_revision=0, at_ms=42, retained=retained,
        )
    assert calls == 1

    # Both the plan event and its cached header must roll back atomically.
    object.__setattr__(retained, field, original)
    monkeypatch.setattr(journal_module, "_snapshot", real_snapshot)
    restored = journal.recover(retained=retained)
    assert restored.tail.event_count == 0
    assert restored.ambiguous_running_steps == ()
    assert restored.step_statuses == (("fixture-step", "pending", 0),)

    replay = journal.append(
        "fixture-step", StepState.RUNNING,
        expected_revision=0, at_ms=42, retained=retained,
    )
    assert replay.tail.event_count == 1
    assert replay.ambiguous_running_steps == ("fixture-step",)
    assert replay.automatic_replay_authorized is False
    assert replay.dispatch_authorized is False
