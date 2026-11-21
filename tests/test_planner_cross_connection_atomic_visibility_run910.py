"""Cross-connection Planner journal snapshot isolation during local CAS append.

All plans and timestamps are synthetic. This checks only SQLite row/header
atomicity and local UNKNOWN state; it cannot establish live tool outcomes.
"""

from __future__ import annotations

from ark.agency import PlanStep, StepState, ToolCall
from ark.agency import planner_journal_review as planner_module
from ark.agency.planner_journal_review import SyntheticPlanJournal


def test_other_planner_handle_never_observes_precommit_event_header_pair(
    tmp_path, monkeypatch,
):
    path = tmp_path / "planner-atomic.sqlite3"
    step = PlanStep(
        "write", ToolCall("inert", "fixture.write", "local", {"n": 1}),
    )
    writer = SyntheticPlanJournal(path, (step,))
    reader = SyntheticPlanJournal(path, (step,))
    before = reader.recover()
    assert before.tail.event_count == 0
    assert before.ambiguous_running_steps == ()
    seen = []
    original = planner_module._checked_snapshot

    def observe_before_commit(graph, tail):
        # The nested reader also calls _checked_snapshot. Let it use the
        # original reviewer for the initial zero-event snapshot; otherwise
        # the fault-injection hook would recursively read itself.
        if tail.event_count == 0:
            return original(graph, tail)
        # The writer already inserted both its event and header update in an
        # open BEGIN IMMEDIATE transaction. A distinct read-only connection
        # must see the old committed prefix, not either tentative new row.
        snapshot = reader.recover()
        assert snapshot.tail == before.tail
        assert snapshot.step_statuses == before.step_statuses
        assert snapshot.ambiguous_running_steps == ()
        seen.append(tail.event_count)
        return original(graph, tail)

    with monkeypatch.context() as patch:
        patch.setattr(planner_module, "_checked_snapshot", observe_before_commit)
        committed = writer.append(
            "write", StepState.RUNNING, expected_revision=0,
            at_ms=10, retained=before.tail,
        )

    assert seen == [1]
    assert committed.tail.event_count == 1
    recovered = SyntheticPlanJournal(path, (step,)).recover(
        retained=before.tail,
    )
    assert recovered.tail == committed.tail
    assert recovered.ambiguous_running_steps == ("write",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
