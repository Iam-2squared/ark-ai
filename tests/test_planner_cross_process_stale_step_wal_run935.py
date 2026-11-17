"""Independent Planner processes may append only valid step-CAS transitions.

A shared retained prefix is not authority to overwrite an already transitioned
step. Both processes are synthetic state-only journals; no tool backend runs.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_CALL = ToolCall("fixture.offline", "fixture.write", "private", {"id": 1})
_STEPS = (
    PlanStep("left", _CALL),
    PlanStep("right", _CALL),
    PlanStep("join", _CALL, ("left", "right")),
)

_CHILD = r"""
import pathlib
import sys
import time

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail

path = pathlib.Path(sys.argv[1])
ready = pathlib.Path(sys.argv[2])
go = pathlib.Path(sys.argv[3])
step_id = sys.argv[4]
genesis = SyntheticPlanTail(
    sys.argv[5], int(sys.argv[6]), sys.argv[7], sys.argv[8], int(sys.argv[9]),
)
call = ToolCall("fixture.offline", "fixture.write", "private", {"id": 1})
steps = (
    PlanStep("left", call),
    PlanStep("right", call),
    PlanStep("join", call, ("left", "right")),
)
store = SyntheticPlanJournal(path, steps)
ready.touch()
deadline = time.monotonic() + 25
while not go.exists():
    if time.monotonic() >= deadline:
        sys.exit("planner start barrier timed out")
    time.sleep(0.02)
try:
    result = store.append(
        step_id, StepState.RUNNING, expected_revision=0, at_ms=10,
        retained=genesis,
    )
except PlanConflictError:
    print("STALE", flush=True)
else:
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    print("SUCCESS", flush=True)
"""


@pytest.mark.parametrize("competition", ("same-step", "disjoint"))
def test_independent_process_step_cas_preserves_cold_unknown_fence(
    tmp_path, competition,
):
    path = tmp_path / "planner-processes.sqlite3"
    initial = SyntheticPlanJournal(path, _STEPS).recover().tail
    start = tmp_path / "release"
    step_ids = ("left", "left") if competition == "same-step" else ("left", "right")
    children = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path),
                str(tmp_path / f"ready-{index}"), str(start), step,
                initial.topology_digest, str(initial.event_count),
                initial.event_hash, initial.status_digest, str(initial.last_at_ms),
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for index, step in enumerate(step_ids)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all((tmp_path / f"ready-{i}").exists() for i in range(2)):
            if any(child.poll() is not None for child in children):
                raise AssertionError("planner child exited before barrier")
            if time.monotonic() >= deadline:
                raise AssertionError("planner children missed barrier")
            time.sleep(0.02)
        start.touch()
        responses = [child.communicate(timeout=35) for child in children]
    finally:
        start.touch()
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate()
    assert all(child.returncode == 0 for child in children), responses
    expected = (
        ["STALE", "SUCCESS"] if competition == "same-step"
        else ["SUCCESS", "SUCCESS"]
    )
    assert sorted(out.strip() for out, _err in responses) == expected

    cold = SyntheticPlanJournal(path, _STEPS).recover(retained=initial)
    statuses = {
        name: (state, revision) for name, state, revision in cold.step_statuses
    }
    assert statuses["left"] == ("running", 1)
    if competition == "same-step":
        assert statuses["right"] == ("pending", 0)
        assert cold.tail.event_count == 1
        assert cold.ambiguous_running_steps == ("left",)
    else:
        assert statuses["right"] == ("running", 1)
        assert cold.tail.event_count == 2
        assert set(cold.ambiguous_running_steps) == {"left", "right"}
    assert statuses["join"] == ("pending", 0)
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False
