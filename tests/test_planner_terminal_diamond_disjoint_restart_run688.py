"""A failed or cancelled branch cannot poison an independent Planner branch.

The same synthetic SQLite journal carries a diamond and a disjoint root.
Different connections may append only state transitions with the expected
revision; terminal BLOCKED descendants are not runnable after restart.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    def step(key, dependencies=()):
        return PlanStep(
            key, ToolCall(
                "offline-read", "read", "local-only", {"fixture": key},
            ), dependencies,
        )

    return (
        step("root"),
        step("left", ("root",)),
        step("right", ("root",)),
        step("join", ("left", "right")),
        step("independent"),
    )


@pytest.mark.parametrize("root_terminal", (StepState.FAILED, StepState.CANCELLED))
@pytest.mark.parametrize("other_terminal", (StepState.SUCCEEDED, StepState.FAILED))
def test_terminal_cascade_preserves_disjoint_work_and_no_stale_replay(
    tmp_path, root_terminal, other_terminal,
):
    steps = _steps()
    path = tmp_path / "shared-plan.sqlite"
    writer = SyntheticPlanJournal(path, steps)
    racer = SyntheticPlanJournal(path, steps)
    genesis = writer.recover().tail

    running = writer.append(
        "root", StepState.RUNNING,
        expected_revision=0, at_ms=10, retained=genesis,
    )
    assert running.tail.event_count == 1
    stopped = racer.append(
        "root", root_terminal,
        expected_revision=1, at_ms=11, retained=genesis,
    )
    assert stopped.tail.event_count == 2
    initial_status = dict(
        (name, (state, revision)) for name, state, revision
        in stopped.step_statuses
    )
    assert initial_status["root"] == (root_terminal.value, 2)
    assert initial_status["independent"] == ("pending", 0)
    for descendant in ("left", "right", "join"):
        assert initial_status[descendant] == ("blocked", 1)

    # Even an entirely different connection cannot resurrect one of the
    # blocked branch's steps or reuse its former revision zero.
    with pytest.raises(PlanConflictError):
        writer.append(
            "left", StepState.RUNNING, expected_revision=0,
            at_ms=12, retained=genesis,
        )

    next_running = writer.append(
        "independent", StepState.RUNNING,
        expected_revision=0, at_ms=13, retained=genesis,
    )
    assert next_running.tail.event_count == 3
    final = racer.append(
        "independent", other_terminal,
        expected_revision=1, at_ms=14, retained=genesis,
    )
    assert final.tail.event_count == 4

    for reader in (writer, racer, SyntheticPlanJournal(path, steps)):
        recovered = reader.recover(retained=genesis)
        assert recovered == final
        states = dict(
            (name, (state, revision)) for name, state, revision
            in recovered.step_statuses
        )
        assert states["root"] == (root_terminal.value, 2)
        assert states["independent"] == (other_terminal.value, 2)
        for descendant in ("left", "right", "join"):
            assert states[descendant] == ("blocked", 1)
        assert recovered.ambiguous_running_steps == ()
        assert recovered.dispatch_authorized is False
        assert recovered.automatic_replay_authorized is False

    with pytest.raises(PlanConflictError):
        writer.append(
            "independent", StepState.SUCCEEDED,
            expected_revision=1, at_ms=15, retained=genesis,
        )
    assert SyntheticPlanJournal(path, steps).recover(retained=genesis) == final
