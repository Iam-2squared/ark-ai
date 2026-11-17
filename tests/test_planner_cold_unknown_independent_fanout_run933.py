"""Cold Planner recovery isolates uncertain root while other DAG work advances.

All steps are disconnected state transitions in a disposable SQLite journal.
A persisted RUNNING state is UNKNOWN after restart, never authorization to
dispatch or replay a real external WRITE. Other independent branches can
still commit a terminal result without modifying the uncertain root.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_CALL = ToolCall("fixture.inert", "fixture.write", "local", {"n": 1})
_STEPS = (
    PlanStep("uncertain", _CALL),
    PlanStep("peer", _CALL),
    PlanStep("peer_leaf", _CALL, ("peer",)),
    PlanStep("join", _CALL, ("uncertain", "peer")),
)


@pytest.mark.parametrize("root_first", (True, False))
@pytest.mark.parametrize(
    "peer_terminal",
    (StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED),
)
def test_cold_running_root_never_replayed_while_peer_completes(
    tmp_path, root_first: bool, peer_terminal: StepState,
) -> None:
    path = tmp_path / "planner-unknown-fanout.sqlite3"
    first = SyntheticPlanJournal(path, _STEPS)
    original_tail = first.recover().tail
    tick = 10

    def apply(journal, name, state, revision):
        nonlocal tick
        tip = journal.recover().tail
        result = journal.append(
            name, state, expected_revision=revision, at_ms=tick, retained=tip,
        )
        tick += 1
        assert result.tail.event_count == tip.event_count + 1
        assert result.dispatch_authorized is False
        assert result.automatic_replay_authorized is False
        return result

    if root_first:
        apply(first, "uncertain", StepState.RUNNING, 0)
    else:
        apply(first, "peer", StepState.RUNNING, 0)
        apply(first, "peer", peer_terminal, 1)
        apply(first, "uncertain", StepState.RUNNING, 0)

    cold = SyntheticPlanJournal(path, _STEPS)
    recovered = cold.recover(retained=original_tail)
    assert recovered.ambiguous_running_steps == ("uncertain",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    # Restart cannot rewrite the unknown root to PENDING or automatically
    # start a child whose prerequisite has never been proven successful.
    before = recovered.tail
    with pytest.raises(PlanConflictError):
        cold.append(
            "uncertain", StepState.RUNNING,
            expected_revision=1, at_ms=tick, retained=before,
        )
    with pytest.raises(PlanConflictError):
        cold.append(
            "join", StepState.RUNNING,
            expected_revision=0, at_ms=tick, retained=before,
        )
    assert cold.recover().tail == before

    if root_first:
        apply(cold, "peer", StepState.RUNNING, 0)
        apply(cold, "peer", peer_terminal, 1)

    if peer_terminal is StepState.SUCCEEDED:
        apply(cold, "peer_leaf", StepState.RUNNING, 0)
        apply(cold, "peer_leaf", StepState.SUCCEEDED, 1)
    else:
        # FAILED/CANCELLED blocks both descendants without a synthetic
        # journal event for each derived BLOCKED state.
        with pytest.raises(PlanConflictError):
            cold.append(
                "peer_leaf", StepState.RUNNING,
                expected_revision=1, at_ms=tick,
            )

    after = SyntheticPlanJournal(path, _STEPS).recover(
        retained=original_tail
    )
    statuses = {
        name: (state, revision)
        for name, state, revision in after.step_statuses
    }
    assert statuses["uncertain"] == ("running", 1)
    assert after.ambiguous_running_steps == ("uncertain",)
    assert statuses["peer"] == (peer_terminal.value, 2)
    if peer_terminal is StepState.SUCCEEDED:
        assert statuses["peer_leaf"] == ("succeeded", 2)
        assert statuses["join"] == ("pending", 0)
    else:
        assert statuses["peer_leaf"] == ("blocked", 1)
        assert statuses["join"] == ("blocked", 1)
    assert after.dispatch_authorized is False
    assert after.automatic_replay_authorized is False
