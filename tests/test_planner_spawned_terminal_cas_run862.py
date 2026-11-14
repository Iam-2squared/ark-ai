"""Independent-process terminal CAS: exactly one SQLite journal outcome wins.

Fixture-only Planner, no ToolBackend dispatch. A terminal journal state is not
proof of any external action, trusted approval, authenticated actor or clock.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from queue import Empty

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep(
            "dependent", ToolCall("fixture", "offline", "local", {"n": 2}),
            ("root",),
        ),
        PlanStep("independent", ToolCall("fixture", "offline", "local", {"n": 3})),
    )


def _attempt(path: str, terminal: StepState, retained, release, messages) -> None:
    try:
        journal = SyntheticPlanJournal(Path(path), _steps())
        messages.put(("ready", terminal.value, None))
        if not release.wait(30):
            raise RuntimeError("synthetic terminal barrier timeout")
        try:
            result = journal.append(
                "root", terminal, expected_revision=1, at_ms=101,
                retained=retained,
            )
        except PlanConflictError:
            messages.put(("stale", terminal.value, None))
        else:
            messages.put(("committed", terminal.value, result.tail.event_count))
    except Exception as exc:
        messages.put(("error", terminal.value, repr(exc)))


@pytest.mark.parametrize("denial", (StepState.FAILED, StepState.CANCELLED))
def test_independent_processes_cannot_split_terminal_cascade(
    tmp_path: Path, denial: StepState,
) -> None:
    path = tmp_path / "terminal-cas.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    genesis = journal.recover().tail
    running = journal.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    context = get_context("spawn")
    release = context.Event()
    messages = context.Queue()
    children = [
        context.Process(
            target=_attempt, args=(str(path), terminal, running.tail, release, messages),
        )
        for terminal in (denial, StepState.SUCCEEDED)
    ]
    try:
        for child in children:
            child.start()
        try:
            ready = [messages.get(timeout=35) for _ in children]
            assert len(ready) == 2
            assert all(message[0] == "ready" for message in ready), ready
            release.set()
            outcomes = [messages.get(timeout=35) for _ in children]
        except Empty as exc:
            pytest.fail(f"synthetic Planner worker did not report: {exc}")
    finally:
        release.set()
        for child in children:
            child.join(timeout=35)
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)
        messages.close()
        messages.join_thread()

    assert all(child.exitcode == 0 for child in children)
    assert sorted(outcome[0] for outcome in outcomes) == ["committed", "stale"]
    winner = next(outcome for outcome in outcomes if outcome[0] == "committed")
    assert winner[2] == 2
    recovered = SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    assert recovered.tail.event_count == 2
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    states = {step: (status, revision) for step, status, revision in recovered.step_statuses}
    assert states["root"] == (winner[1], 2)
    assert states["independent"] == ("pending", 0)
    assert states["dependent"] == (
        ("pending", 0) if winner[1] == StepState.SUCCEEDED.value
        else ("blocked", 1)
    )
    assert SyntheticPlanJournal(path, _steps()).recover(retained=genesis) == recovered
