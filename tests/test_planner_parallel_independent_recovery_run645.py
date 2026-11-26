"""Independent Planner branches may advance while another is ambiguous.

All transitions are synthetic SQLite fixtures. RUNNING after restart must be
reported as UNKNOWN, never dispatched, retried or treated as authorization.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (
        PlanStep("root_a", ToolCall("fixture", "offline", "local", {"n": "a"})),
        PlanStep(
            "child_a", ToolCall("fixture", "offline", "local", {"n": "child"}),
            ("root_a",),
        ),
        PlanStep("root_b", ToolCall("fixture", "offline", "local", {"n": "b"})),
    )


@pytest.mark.parametrize("failure", (StepState.FAILED, StepState.CANCELLED))
def test_independent_start_race_then_terminal_failure_survives_restart(
    tmp_path, failure,
):
    path = tmp_path / "independent-roots.sqlite"
    steps = _steps()
    first = SyntheticPlanJournal(path, steps)
    second = SyntheticPlanJournal(path, steps)
    genesis = first.recover().tail
    barrier = Barrier(2)

    def start(args):
        journal, step_id = args
        barrier.wait(timeout=10)
        return journal.append(
            step_id, StepState.RUNNING, expected_revision=0,
            at_ms=100, retained=genesis,
        )

    with ThreadPoolExecutor(max_workers=2) as workers:
        starts = list(workers.map(
            start, ((first, "root_a"), (second, "root_b")),
        ))
    assert sorted(result.tail.event_count for result in starts) == [1, 2]
    before_terminal = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert before_terminal.tail.event_count == 2
    assert before_terminal.ambiguous_running_steps == ("root_a", "root_b")

    failed = first.append(
        "root_a", failure, expected_revision=1,
        at_ms=101, retained=genesis,
    )
    assert failed.tail.event_count == 3
    restarted = SyntheticPlanJournal(path, steps)
    with sqlite3.connect(path) as conn:
        before = tuple(conn.iterdump())
    recovered = restarted.recover(retained=before_terminal.tail)
    assert recovered == failed
    assert recovered.ambiguous_running_steps == ("root_b",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    states = {name: (state, revision) for name, state, revision in recovered.step_statuses}
    assert states == {
        "root_a": (failure.value, 2),
        "root_b": ("running", 1),
        "child_a": ("blocked", 1),
    }
    with sqlite3.connect(path) as conn:
        assert tuple(conn.iterdump()) == before

    with pytest.raises(PlanConflictError):
        restarted.append(
            "root_a", StepState.SUCCEEDED, expected_revision=1,
            at_ms=102, retained=genesis,
        )
    assert restarted.recover(retained=genesis) == recovered


def test_child_unavailable_while_parent_running_but_other_root_unchanged(tmp_path):
    path = tmp_path / "unresolved-parent.sqlite"
    steps = _steps()
    a = SyntheticPlanJournal(path, steps)
    b = SyntheticPlanJournal(path, steps)
    genesis = a.recover().tail
    a.append(
        "root_a", StepState.RUNNING, expected_revision=0,
        at_ms=200, retained=genesis,
    )
    b_started = b.append(
        "root_b", StepState.RUNNING, expected_revision=0,
        at_ms=201, retained=genesis,
    )
    with pytest.raises(PlanConflictError, match="dependencies"):
        a.append(
            "child_a", StepState.RUNNING, expected_revision=0,
            at_ms=202, retained=genesis,
        )
    assert SyntheticPlanJournal(path, steps).recover() == b_started
    a.append(
        "root_a", StepState.SUCCEEDED, expected_revision=1,
        at_ms=203, retained=genesis,
    )
    child = b.append(
        "child_a", StepState.RUNNING, expected_revision=0,
        at_ms=204, retained=genesis,
    )
    restarted = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert restarted == child
    assert restarted.ambiguous_running_steps == ("child_a", "root_b")
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False
