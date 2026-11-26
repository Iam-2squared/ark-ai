"""Run1444: PlannerJournal transition CAS across independent processes.

Only synthetic PlanGraph state and disposable local SQLite are used. A
recovered RUNNING step remains ambiguous and grants no replay or dispatch.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalConflictError,
)

_PLAN_ID = "planner-process-cas-run1444"
_PRIVATE = "raw-private-tool-argument-run1444"


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.root",
        "fixture.read",
        "synthetic:private",
        {"private_fixture": _PRIVATE},
    )
    return (
        PlanStep("root", call),
        PlanStep("independent", call),
    )


def _transition_worker(database: str, ready, release, results) -> None:
    journal = PlannerJournal(Path(database))
    recovered = journal.recover(_PLAN_ID, _steps())
    if recovered.sequence != 0:
        raise AssertionError("worker did not observe the genesis frontier")
    ready.put("ready")
    if not release.wait(timeout=45):
        raise RuntimeError("PlannerJournal race release timed out")
    try:
        transition = journal.transition(
            _PLAN_ID,
            recovered.graph,
            "root",
            StepState.RUNNING,
            expected_revision=0,
            expected_sequence=0,
        )
    except PlannerJournalConflictError:
        results.put(("conflict", None))
    else:
        results.put(("success", transition.receipt.sequence))


def test_two_processes_racing_same_planner_revision_commit_once_run1444(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-process-cas-run1444.sqlite3"
    steps = _steps()
    PlannerJournal(path).create_plan(_PLAN_ID, PlanGraph(steps))

    context = get_context("spawn")
    ready = context.Queue()
    results = context.Queue()
    release = context.Event()
    processes = [
        context.Process(
            target=_transition_worker,
            args=(str(path), ready, release, results),
        )
        for _ in range(2)
    ]
    try:
        for process in processes:
            process.start()
        assert [ready.get(timeout=60) for _ in processes] == ["ready", "ready"]
        release.set()
        outcomes = [results.get(timeout=60) for _ in processes]
        for process in processes:
            process.join(timeout=60)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                pytest.fail("PlannerJournal CAS worker did not terminate")
            assert process.exitcode == 0
    finally:
        release.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

    assert sorted(kind for kind, _ in outcomes) == ["conflict", "success"]
    assert [sequence for kind, sequence in outcomes if kind == "success"] == [1]
    assert [value for kind, value in outcomes if kind == "conflict"] == [None]

    cold = PlannerJournal(path)
    recovered = cold.recover(_PLAN_ID, steps)
    statuses = recovered.graph.statuses()
    assert statuses["root"].state is StepState.RUNNING
    assert statuses["root"].revision == 1
    assert statuses["independent"].state is StepState.PENDING
    assert statuses["independent"].revision == 0
    assert recovered.sequence == 1
    assert recovered.ambiguous_running_step_ids == ("root",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute(
            "SELECT sequence,step_id,from_state,to_state,expected_revision "
            "FROM planner_journal_events ORDER BY sequence"
        ).fetchall() == [(1, "root", "pending", "running", 0)]
        assert connection.execute(
            "SELECT last_sequence FROM planner_journal_meta WHERE plan_id=?",
            (_PLAN_ID,),
        ).fetchone() == (1,)

    persisted = b"".join(
        item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
    )
    assert _PRIVATE.encode("utf-8") not in persisted
