"""Run1456: terminal Planner COMMIT survives exit with a pinned WAL reader.

Synthetic PlanGraph values and disposable local SQLite only. A recovered
terminal failure remains non-dispatchable; no automatic replay is authorized.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalConflictError,
)

_PLAN_ID = "planner-terminal-wal-reader-run1456"
_PRIVATE = "raw-sensitive-planner-terminal-wal-reader-run1456"


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.root",
        "fixture.read",
        "synthetic:private",
        {"private_fixture": _PRIVATE},
    )
    return (
        PlanStep("root", call),
        PlanStep("dependent", call, ("root",)),
        PlanStep("independent", call),
    )


def _snapshot(connection: sqlite3.Connection):
    meta = connection.execute(
        "SELECT last_sequence,last_event_hash FROM planner_journal_meta "
        "WHERE plan_id=?",
        (_PLAN_ID,),
    ).fetchone()
    events = connection.execute(
        "SELECT sequence,step_id,from_state,to_state,expected_revision "
        "FROM planner_journal_events WHERE plan_id=? ORDER BY sequence",
        (_PLAN_ID,),
    ).fetchall()
    return meta, events


def _hard_exit_after_terminal_commit(database: str) -> None:
    path = Path(database)
    steps = _steps()
    journal = PlannerJournal(path)
    graph = journal.recover(_PLAN_ID, steps).graph
    native_connect = journal._connect

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, statement: str, *args):
            result = self.connection.execute(statement, *args)
            if statement == "COMMIT":
                # The terminal event and metadata frontier are committed.
                # Exit before connection cleanup or a transition receipt.
                os._exit(75)
            return result

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    journal._connect = lambda: ExitAfterCommit(native_connect())
    journal.transition(
        _PLAN_ID,
        graph,
        "root",
        StepState.FAILED,
        expected_revision=1,
        expected_sequence=1,
    )
    os._exit(76)


def test_terminal_commit_survives_hard_exit_and_pinned_wal_reader(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-terminal-wal-reader-hard-exit.sqlite3"
    steps = _steps()
    initial = PlanGraph(steps)
    journal = PlannerJournal(path)
    journal.create_plan(_PLAN_ID, initial)
    running = journal.transition(
        _PLAN_ID,
        initial,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    assert running.receipt.sequence == 1

    # The journal does not switch SQLite into WAL mode itself. Establish WAL
    # explicitly before pinning a reader so the test exercises WAL retention,
    # not DELETE-journal writer blocking.
    with closing(sqlite3.connect(path, timeout=10)) as setup:
        journal_mode = setup.execute("PRAGMA journal_mode=WAL").fetchone()
    assert journal_mode == ("wal",)

    keeper = sqlite3.connect(path, timeout=10, isolation_level=None)
    keeper_open = True
    try:
        keeper.execute("PRAGMA query_only=ON")
        keeper.execute("BEGIN")
        before = (
            (1, running.receipt.event_hash),
            [(1, "root", "pending", "running", 0)],
        )
        assert _snapshot(keeper) == before

        process = multiprocessing.get_context("spawn").Process(
            target=_hard_exit_after_terminal_commit,
            args=(str(path),),
        )
        process.start()
        process.join(timeout=35)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            pytest.fail("Planner terminal COMMIT hard-exit fixture did not terminate")
        assert process.exitcode == 75

        # The old read snapshot remains stable while the terminal COMMIT is
        # present in WAL but its writer has exited without cleanup/receipt.
        assert _snapshot(keeper) == before
        with closing(sqlite3.connect(path, timeout=0.2)) as checkpoint:
            blocked = checkpoint.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()
        keeper_open = False

        cold = PlannerJournal(path)
        recovered = cold.recover(_PLAN_ID, steps)
        statuses = recovered.graph.statuses()
        assert statuses["root"].state is StepState.FAILED
        assert statuses["root"].revision == 2
        assert statuses["dependent"].state is StepState.BLOCKED
        assert statuses["dependent"].revision == 1
        assert statuses["independent"].state is StepState.PENDING
        assert statuses["independent"].revision == 0
        assert recovered.sequence == 2
        assert recovered.ambiguous_running_step_ids == ()
        assert recovered.dispatch_authorized is False
        assert recovered.automatic_replay_authorized is False

        with pytest.raises(PlannerJournalConflictError):
            cold.transition(
                _PLAN_ID,
                running.graph,
                "root",
                StepState.SUCCEEDED,
                expected_revision=1,
                expected_sequence=1,
            )
        reread = cold.recover(_PLAN_ID, steps)
        assert reread.sequence == 2
        assert reread.graph.statuses()["root"].state is StepState.FAILED
        assert reread.graph.statuses()["dependent"].state is StepState.BLOCKED
        assert reread.dispatch_authorized is False
        assert reread.automatic_replay_authorized is False

        with closing(sqlite3.connect(path, timeout=10)) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            assert connection.execute(
                "SELECT sequence,step_id,from_state,to_state,expected_revision "
                "FROM planner_journal_events WHERE plan_id=? ORDER BY sequence",
                (_PLAN_ID,),
            ).fetchall() == [
                (1, "root", "pending", "running", 0),
                (2, "root", "running", "failed", 1),
            ]
            assert connection.execute(
                "SELECT last_sequence FROM planner_journal_meta WHERE plan_id=?",
                (_PLAN_ID,),
            ).fetchone() == (2,)
            checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            assert checkpoint is not None
            assert checkpoint[0] == 0
            assert checkpoint[1] == checkpoint[2]

        persisted = b"".join(
            item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
        )
        assert _PRIVATE.encode("utf-8") not in persisted
    finally:
        if keeper_open:
            if keeper.in_transaction:
                keeper.rollback()
            keeper.close()
