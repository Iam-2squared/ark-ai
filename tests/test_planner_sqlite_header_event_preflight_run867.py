"""Planner SQL prehydration denial under synthetic corrupt persisted values."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.planner_journal_review as planner
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _seed(tmp_path):
    path = tmp_path / "plan.sqlite"
    steps = (PlanStep("root", ToolCall("mock", "offline", "scope", {"n": 1})),)
    journal = planner.SyntheticPlanJournal(path, steps)
    started = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=19,
    )
    return path, journal, started.tail


class _DenyHydration:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, *args):
        if sql in (planner._HEADER, planner._EVENTS):
            raise AssertionError("persisted Planner header/event hydrated")
        return self.conn.execute(sql, *args)


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("topology_digest", "x" * 300_000),
        ("initial_status_digest", "x" * 72),
        ("tail_hash", sqlite3.Binary(b"synthetic-blob")),
        ("status_digest", "x" * 72),
        ("event_count", sqlite3.Binary(b"synthetic-blob")),
        ("last_at_ms", sqlite3.Binary(b"synthetic-blob")),
    ),
)
def test_header_sql_preflight_rejects_before_hydration(
    tmp_path, column, value,
):
    path, journal, _tail = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_plan_header SET {column}=? WHERE id=1",
            (value,),
        )
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("BEGIN")
        with pytest.raises(
            planner.SyntheticPlanJournalRejected, match="header hydration admission"
        ):
            journal._replay(_DenyHydration(conn))
        conn.rollback()


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("step_id", "x" * 200_000),
        ("from_state", "x" * 17),
        ("to_state", sqlite3.Binary(b"synthetic-blob")),
        ("post_status_digest", "x" * 72),
        ("previous_hash", sqlite3.Binary(b"synthetic-blob")),
        ("event_hash", "x" * 70),
        ("occurred_at_ms", sqlite3.Binary(b"synthetic-blob")),
    ),
)
def test_event_sql_preflight_rejects_before_hydration(
    tmp_path, column, value,
):
    path, journal, _tail = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_plan_events SET {column}=? WHERE seq=1",
            (value,),
        )
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("BEGIN")
        with pytest.raises(
            planner.SyntheticPlanJournalRejected, match="event hydration admission"
        ):
            journal._replay(_DenyHydration(conn))
        conn.rollback()


def test_original_planner_recovery_retains_manual_only_unknown(tmp_path):
    _path, journal, tail = _seed(tmp_path)
    recovered = journal.recover(retained=tail)
    assert recovered.ambiguous_running_steps == ("root",)
    assert recovered.automatic_replay_authorized is False
    assert recovered.dispatch_authorized is False
