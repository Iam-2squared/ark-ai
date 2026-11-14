"""Spawned Planner crash/recovery and competing-CAS tests on disposable SQLite.

No ToolBackend is called. A COMMIT without a returned receipt remains UNKNOWN;
no automatic retry, permission grant, actor identity or real action is inferred.
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
        PlanStep("root_a", ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep(
            "child_a", ToolCall("fixture", "offline", "local", {"n": 2}),
            ("root_a",),
        ),
        PlanStep("root_b", ToolCall("fixture", "offline", "local", {"n": 3})),
    )


def _lost_reply_writer(path: str) -> None:
    journal = SyntheticPlanJournal(Path(path), _steps())
    journal.append("root_a", StepState.RUNNING, expected_revision=0, at_ms=100)
    # Exit without returning the committed receipt to the supervising process.


def _competing_writer(path: str, retained, release, messages, name: str) -> None:
    try:
        journal = SyntheticPlanJournal(Path(path), _steps())
        messages.put((name, "ready", None))
        if not release.wait(30):
            raise RuntimeError("fixture release timed out")
        try:
            result = journal.append(
                "root_a", StepState.RUNNING,
                expected_revision=0, at_ms=100, retained=retained,
            )
        except PlanConflictError:
            messages.put((name, "stale", None))
        else:
            messages.put((name, "committed", result.tail.event_count))
    except Exception as exc:
        messages.put((name, "error", repr(exc)))


def _join_or_terminate(child) -> None:
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)


def test_spawned_postcommit_lost_reply_keeps_unknown_and_independent_progress(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-postcommit.sqlite"
    genesis = SyntheticPlanJournal(path, _steps()).recover().tail
    child = get_context("spawn").Process(
        target=_lost_reply_writer, args=(str(path),),
    )
    child.start()
    _join_or_terminate(child)
    assert child.exitcode == 0

    restarted = SyntheticPlanJournal(path, _steps())
    recovered = restarted.recover(retained=genesis)
    assert recovered.tail.event_count == 1
    assert recovered.ambiguous_running_steps == ("root_a",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError):
        restarted.append(
            "root_a", StepState.RUNNING, expected_revision=0,
            at_ms=101, retained=genesis,
        )
    with pytest.raises(PlanConflictError):
        restarted.append(
            "child_a", StepState.RUNNING, expected_revision=0,
            at_ms=101, retained=genesis,
        )
    independent = restarted.append(
        "root_b", StepState.RUNNING, expected_revision=0,
        at_ms=102, retained=genesis,
    )
    final = restarted.append(
        "root_b", StepState.SUCCEEDED, expected_revision=1,
        at_ms=103, retained=independent.tail,
    )
    cold = SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    assert cold == final
    assert cold.ambiguous_running_steps == ("root_a",)
    assert dict((step, state) for step, state, _ in cold.step_statuses) == {
        "child_a": "pending", "root_a": "running", "root_b": "succeeded",
    }
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False


def test_spawned_competing_same_step_has_one_committed_cas_winner(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-multiprocess-cas.sqlite"
    genesis = SyntheticPlanJournal(path, _steps()).recover().tail
    context = get_context("spawn")
    release = context.Event()
    messages = context.Queue()
    children = [
        context.Process(
            target=_competing_writer,
            args=(str(path), genesis, release, messages, name),
        )
        for name in ("writer-a", "writer-b")
    ]
    try:
        for child in children:
            child.start()
            assert messages.get(timeout=35)[1] == "ready"
        release.set()
        outcomes = [messages.get(timeout=35) for _ in children]
    except Empty as exc:
        pytest.fail(f"spawned Planner worker did not report state: {exc}")
    finally:
        release.set()
        for child in children:
            _join_or_terminate(child)
        messages.close()
        messages.join_thread()

    assert all(child.exitcode == 0 for child in children)
    assert sorted(outcome[1] for outcome in outcomes) == ["committed", "stale"]
    assert next(x[2] for x in outcomes if x[1] == "committed") == 1
    cold = SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    assert cold.tail.event_count == 1
    assert cold.ambiguous_running_steps == ("root_a",)
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError):
        SyntheticPlanJournal(path, _steps()).append(
            "root_a", StepState.RUNNING,
            expected_revision=0, at_ms=101, retained=genesis,
        )
