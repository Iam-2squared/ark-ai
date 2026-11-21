"""Independent-process reservation CAS and restart proof for the inert plan journal."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (
        PlanStep("root", ToolCall("fixture", "offline", "test", {"n": 1})),
    )


_CHILD = """
import os
import sys
from pathlib import Path
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal
path = Path(sys.argv[1])
steps = (PlanStep("root", ToolCall("fixture", "offline", "test", {"n": 1})),)
journal = SyntheticPlanJournal(path, steps)
sys.stdin.readline()
try:
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=100)
    print("COMMITTED", flush=True)
except PlanConflictError:
    print("CONFLICT", flush=True)
if len(sys.argv) > 2 and sys.argv[2] == "hard-exit":
    os._exit(0)
"""


def _open_child(path: Path, *extra: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        (sys.executable, "-c", _CHILD, str(path), *extra),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_two_processes_first_open_and_cas_never_double_commit(tmp_path: Path):
    path = tmp_path / "fixture #1 %.sqlite"
    children = [_open_child(path), _open_child(path)]

    def release(child):
        stdout, stderr = child.communicate(input="start\n", timeout=20)
        assert child.returncode == 0, stderr
        return stdout.strip()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(release, children))
    assert sorted(outcomes) == ["COMMITTED", "CONFLICT"]
    journal = SyntheticPlanJournal(path, _steps())
    recovery = journal.recover()
    assert recovery.tail.event_count == 1
    assert recovery.ambiguous_running_steps == ("root",)
    assert recovery.automatic_replay_authorized is False


def test_abrupt_process_exit_after_commit_cannot_restart_write(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    child = _open_child(path, "hard-exit")
    stdout, stderr = child.communicate(input="start\n", timeout=20)
    assert child.returncode == 0, stderr
    assert "COMMITTED" in stdout

    reopened = SyntheticPlanJournal(path, _steps())
    snapshot = reopened.recover()
    assert snapshot.tail.event_count == 1
    assert snapshot.ambiguous_running_steps == ("root",)
    assert snapshot.dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
