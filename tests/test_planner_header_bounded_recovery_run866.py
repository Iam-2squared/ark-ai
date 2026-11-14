"""Planner cold recovery reads a bounded header; no execution or replay."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.planner_journal_review as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall


class _HeaderCursor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def fetchmany(self, limit):
        self.calls.append(limit)
        assert limit == 2
        return self.rows[:limit]

    def fetchall(self):
        raise AssertionError("unbounded Planner header hydration")


class _WrappedConnection:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def execute(self, sql, *args):
        if sql == journal_module._HEADER:
            return self.cursor
        return self.conn.execute(sql, *args)


@pytest.mark.parametrize("header_count", (0, 1, 2, 3))
def test_cold_recovery_bounded_header_cursor(tmp_path, header_count):
    path = tmp_path / "planner.sqlite"
    steps = (
        PlanStep(
            "root", ToolCall("fixture", "offline", "fixture-scope", {"n": 1}),
        ),
    )
    journal = journal_module.SyntheticPlanJournal(path, steps)
    started = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=9,
    )
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("BEGIN")
        header = conn.execute(journal_module._HEADER).fetchone()
        cursor = _HeaderCursor([header] * header_count)
        wrapped = _WrappedConnection(conn, cursor)
        if header_count == 1:
            _, tails = journal._replay(wrapped)
            assert tails[-1] == started.tail
        else:
            with pytest.raises(
                journal_module.SyntheticPlanJournalRejected,
                match="header missing or duplicated",
            ):
                journal._replay(wrapped)
        assert cursor.calls == [2]
        conn.rollback()
    recovered = journal.recover(retained=started.tail)
    assert recovered.ambiguous_running_steps == ("root",)
    assert recovered.automatic_replay_authorized is False
    assert recovered.dispatch_authorized is False
