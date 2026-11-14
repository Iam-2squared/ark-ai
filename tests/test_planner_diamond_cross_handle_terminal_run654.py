"""Two-handle Planner diamond remains coherent after competing branch endings.

Durable SQLite journal only; no real tool execution, trusted clock, approval,
external result, or automatic replay is inferred from recovered RUNNING.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    def step(name, *depends):
        return PlanStep(
            name, ToolCall("fixture", "offline", "local", {"step": name}),
            depends,
        )

    return (
        step("root_a"),
        step("root_b"),
        step("join", "root_a", "root_b"),
        step("tail", "join"),
        step("independent"),
    )


def _states(recovery):
    return {
        name: (state, revision)
        for name, state, revision in recovery.step_statuses
    }


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
def test_diamond_terminal_cascade_survives_other_root_success(
    tmp_path, terminal,
):
    path = tmp_path / "diamond-branch.sqlite"
    steps = _steps()
    a = SyntheticPlanJournal(path, steps)
    b = SyntheticPlanJournal(path, steps)
    genesis = a.recover().tail
    gate = Barrier(2)

    def start(args):
        journal, name = args
        gate.wait(timeout=10)
        return journal.append(
            name, StepState.RUNNING, expected_revision=0,
            at_ms=100, retained=genesis,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        started = tuple(pool.map(
            start, ((a, "root_a"), (b, "root_b")),
        ))
    assert sorted(x.tail.event_count for x in started) == [1, 2]
    assert SyntheticPlanJournal(path, steps).recover(
        retained=genesis,
    ).ambiguous_running_steps == ("root_a", "root_b")

    denied = a.append(
        "root_a", terminal, expected_revision=1,
        at_ms=101, retained=genesis,
    )
    assert denied.tail.event_count == 3
    assert _states(denied)["join"] == ("blocked", 1)
    assert _states(denied)["tail"] == ("blocked", 1)

    completed = b.append(
        "root_b", StepState.SUCCEEDED, expected_revision=1,
        at_ms=102, retained=genesis,
    )
    assert completed.tail.event_count == 4
    assert completed.ambiguous_running_steps == ()
    assert _states(completed) == {
        "root_a": (terminal.value, 2),
        "root_b": ("succeeded", 2),
        "join": ("blocked", 1),
        "tail": ("blocked", 1),
        "independent": ("pending", 0),
    }

    restarted = SyntheticPlanJournal(path, steps)
    assert restarted.recover(retained=genesis) == completed
    assert completed.dispatch_authorized is False
    assert completed.automatic_replay_authorized is False

    with pytest.raises(PlanConflictError):
        restarted.append(
            "join", StepState.RUNNING, expected_revision=0,
            at_ms=103, retained=genesis,
        )
    with pytest.raises(PlanConflictError):
        restarted.append(
            "root_a", StepState.SUCCEEDED, expected_revision=1,
            at_ms=104, retained=genesis,
        )
    assert SyntheticPlanJournal(path, steps).recover(
        retained=genesis,
    ) == completed

    independent = restarted.append(
        "independent", StepState.RUNNING, expected_revision=0,
        at_ms=105, retained=genesis,
    )
    assert _states(independent)["join"] == ("blocked", 1)
    assert independent.ambiguous_running_steps == ("independent",)
    assert independent.dispatch_authorized is False
    assert independent.automatic_replay_authorized is False


def test_diamond_join_requires_both_durably_succeeded_roots(tmp_path):
    path = tmp_path / "diamond-both-succeeded.sqlite"
    steps = _steps()
    a = SyntheticPlanJournal(path, steps)
    b = SyntheticPlanJournal(path, steps)
    genesis = a.recover().tail

    a.append(
        "root_a", StepState.RUNNING, expected_revision=0,
        at_ms=10, retained=genesis,
    )
    a.append(
        "root_a", StepState.SUCCEEDED, expected_revision=1,
        at_ms=11, retained=genesis,
    )
    b.append(
        "root_b", StepState.RUNNING, expected_revision=0,
        at_ms=12, retained=genesis,
    )
    mid = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert _states(mid)["join"] == ("pending", 0)
    assert mid.ambiguous_running_steps == ("root_b",)
    with pytest.raises(PlanConflictError, match="dependencies"):
        b.append(
            "join", StepState.RUNNING, expected_revision=0,
            at_ms=13, retained=genesis,
        )

    b.append(
        "root_b", StepState.SUCCEEDED, expected_revision=1,
        at_ms=14, retained=genesis,
    )
    joined = a.append(
        "join", StepState.RUNNING, expected_revision=0,
        at_ms=15, retained=genesis,
    )
    reopened = SyntheticPlanJournal(path, steps)
    assert reopened.recover(retained=genesis) == joined
    assert joined.ambiguous_running_steps == ("join",)
    assert _states(joined)["tail"] == ("pending", 0)
    assert joined.dispatch_authorized is False
    assert joined.automatic_replay_authorized is False

    with pytest.raises(PlanConflictError):
        reopened.append(
            "join", StepState.RUNNING, expected_revision=0,
            at_ms=16, retained=genesis,
        )
    assert SyntheticPlanJournal(path, steps).recover(
        retained=genesis,
    ) == joined
