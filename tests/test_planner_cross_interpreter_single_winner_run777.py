"""Cold-process Planner CAS: only one terminal/running path can be journaled.

Two interpreters race on one prepared journal and retained genesis. A crashed
RUNNING step remains UNKNOWN/manual-only, not a dispatched tool or retry.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)

_FIRST = "step_" + "1" * 16
_DEPENDENT = "step_" + "2" * 16
_CHILD = """
import sys
from pathlib import Path
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal, SyntheticPlanJournalRejected,
)
first = "step_" + "1" * 16
dependent = "step_" + "2" * 16
steps = (
    PlanStep(first, ToolCall("mock", "fixture.write", "local", {"x": 1})),
    PlanStep(dependent, ToolCall("mock", "fixture.read", "local"), (first,)),
)
journal = SyntheticPlanJournal(Path(sys.argv[1]), steps)
retained = journal.recover().tail
assert retained.event_count == 0
print("ready", flush=True)
if sys.stdin.readline().strip() != "go":
    raise RuntimeError("fixture barrier not released")
try:
    result = journal.append(
        first, StepState(sys.argv[2]), expected_revision=0,
        at_ms=100, retained=retained,
    )
except (SyntheticPlanJournalRejected, PlanConflictError):
    print("rejected", flush=True)
else:
    print("committed", sys.argv[2], result.tail.event_count, flush=True)
"""


@pytest.mark.parametrize(
    "states",
    (("RUNNING", "CANCELLED"), ("CANCELLED", "RUNNING")),
)
def test_two_interpreters_cannot_replay_a_competing_planner_transition(
    tmp_path: Path, states: tuple[str, str],
) -> None:
    path = tmp_path / "journal.sqlite"
    steps = (
        PlanStep(_FIRST, ToolCall("mock", "fixture.write", "local", {"x": 1})),
        PlanStep(
            _DEPENDENT, ToolCall("mock", "fixture.read", "local"), (_FIRST,),
        ),
    )
    journal = SyntheticPlanJournal(path, steps)
    genesis = journal.recover().tail
    children: list[subprocess.Popen[str]] = []
    outcomes: list[str] = []
    try:
        # Both startup/replay phases finish before competing for one SQLite
        # BEGIN IMMEDIATE and the same independently held genesis.
        for state in states:
            child = subprocess.Popen(
                [sys.executable, "-c", _CHILD, str(path), state.lower()],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True,
            )
            children.append(child)
            assert child.stdout is not None
            assert child.stdout.readline().strip() == "ready"
        for child in children:
            assert child.stdin is not None
            child.stdin.write("go\n")
            child.stdin.flush()
        for child in children:
            stdout, stderr = child.communicate(timeout=35)
            assert child.returncode == 0, (stdout, stderr)
            outcomes.append(stdout.strip())
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=15)

    winners = [value for value in outcomes if value.startswith("committed ")]
    assert len(winners) == 1, outcomes
    assert outcomes.count("rejected") == 1, outcomes
    _, winning_state, count = winners[0].split()
    assert count == "1"
    cold = SyntheticPlanJournal(path, steps)
    recovered = cold.recover(retained=genesis)
    assert recovered.tail.event_count == 1
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    statuses = {name: (state, rev) for name, state, rev
                in recovered.step_statuses}
    assert statuses[_FIRST] == (winning_state, 1)
    if winning_state == "running":
        assert recovered.ambiguous_running_steps == (_FIRST,)
        assert statuses[_DEPENDENT] == ("pending", 0)
    else:
        assert winning_state == "cancelled"
        assert recovered.ambiguous_running_steps == ()
        assert statuses[_DEPENDENT] == ("blocked", 1)
    with pytest.raises((SyntheticPlanJournalRejected, PlanConflictError)):
        cold.append(
            _FIRST, StepState.RUNNING, expected_revision=0,
            at_ms=101, retained=genesis,
        )
    assert cold.recover(retained=genesis).tail == recovered.tail
