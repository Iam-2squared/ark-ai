"""A terminal diamond must not absorb an independent in-flight Planner step.

Two synthetic SQLite handles interleave RUNNING transitions. Stopping one
root blocks only its descendants; the unrelated in-flight step remains
UNKNOWN after restart until its own explicit terminal journal event.
No backend invocation, real action or automatic WRITE replay is permitted.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    def step(name, parents=()):
        return PlanStep(
            name,
            ToolCall("offline-read", "read", "local-only", {"fixture": name}),
            parents,
        )

    return (
        step("root"),
        step("left", ("root",)),
        step("right", ("root",)),
        step("join", ("left", "right")),
        step("unrelated"),
    )


@pytest.mark.parametrize("root_end", (StepState.FAILED, StepState.CANCELLED))
@pytest.mark.parametrize("unrelated_end", (StepState.SUCCEEDED, StepState.FAILED))
def test_overlapping_running_steps_are_isolated_across_terminal_restart(
    tmp_path, root_end, unrelated_end,
):
    path = tmp_path / "shared-plan.sqlite"
    steps = _steps()
    first = SyntheticPlanJournal(path, steps)
    second = SyntheticPlanJournal(path, steps)
    genesis = first.recover().tail

    first.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10,
        retained=genesis,
    )
    both_running = second.append(
        "unrelated", StepState.RUNNING, expected_revision=0, at_ms=11,
        retained=genesis,
    )
    assert both_running.ambiguous_running_steps == ("root", "unrelated")

    stopped = first.append(
        "root", root_end, expected_revision=1, at_ms=12,
        retained=genesis,
    )
    cold = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert cold == stopped
    states = {name: (state, rev) for name, state, rev in cold.step_statuses}
    assert states["root"] == (root_end.value, 2)
    assert states["unrelated"] == ("running", 1)
    for name in ("left", "right", "join"):
        assert states[name] == ("blocked", 1)
    assert cold.ambiguous_running_steps == ("unrelated",)
    assert cold.tail.event_count == 3
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False

    # Restart never turns an existing RUNNING step into a second RUNNING.
    with pytest.raises(PlanConflictError):
        second.append(
            "unrelated", StepState.RUNNING, expected_revision=1, at_ms=13,
            retained=genesis,
        )
    assert SyntheticPlanJournal(path, steps).recover(retained=genesis) == cold

    completed = second.append(
        "unrelated", unrelated_end, expected_revision=1, at_ms=14,
        retained=genesis,
    )
    assert completed.tail.event_count == 4
    assert completed.ambiguous_running_steps == ()
    for reader in (first, second, SyntheticPlanJournal(path, steps)):
        current = reader.recover(retained=genesis)
        assert current == completed
        states = {name: (state, rev) for name, state, rev in current.step_statuses}
        assert states["unrelated"] == (unrelated_end.value, 2)
        assert states["root"] == (root_end.value, 2)
        for name in ("left", "right", "join"):
            assert states[name] == ("blocked", 1)
        assert current.dispatch_authorized is False
        assert current.automatic_replay_authorized is False
