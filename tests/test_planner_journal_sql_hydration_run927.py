"""Bounded SQLite admission before synthetic Planner replay materializes rows.

All fixtures are disposable, local, and denial-only. No recovered state
permits dispatch or retry of an ambiguous WRITE after a lost receipt.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _prepared(tmp_path):
    path = tmp_path / "plan.sqlite"
    step = PlanStep(
        "root", ToolCall("disconnected", "fixture.write", "local", {"n": 1}),
    )
    journal = SyntheticPlanJournal(path, (step,))
    retained = journal.recover().tail
    journal.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=7, retained=retained,
    )
    return path, journal


@pytest.mark.parametrize(
    ("column", "payload"),
    (
        ("step_id", "s" * 10_000),
        ("from_state", "a" * 10_000),
        ("to_state", "a" * 10_000),
        ("post_status_digest", "h" * 10_000),
        ("previous_hash", "h" * 10_000),
        ("event_hash", "h" * 10_000),
        ("expected_revision", "invalid-revision"),
        ("occurred_at_ms", "invalid-clock"),
    ),
)
def test_event_sql_preflight_rejects_oversize_or_wrong_type_before_replay(
    tmp_path, column: str, payload: str,
) -> None:
    path, journal = _prepared(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_plan_events SET {column}=? WHERE seq=1", (payload,),
        )
    with pytest.raises(
        SyntheticPlanJournalRejected,
        match="synthetic plan event hydration admission failed",
    ):
        journal.recover()
    # The reader must not repair, erase, or silently replay corrupted history.
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"SELECT {column} FROM synthetic_plan_events WHERE seq=1"
        ).fetchone() == (payload,)
        assert conn.execute(
            "SELECT event_count FROM synthetic_plan_header WHERE id=1"
        ).fetchone() == (1,)


@pytest.mark.parametrize(
    ("column", "payload"),
    (
        ("topology_digest", "p" * 10_000),
        ("status_digest", "s" * 10_000),
        ("tail_hash", "e" * 10_000),
        ("last_at_ms", "invalid-clock"),
    ),
)
def test_header_sql_preflight_rejects_tampered_stored_values(
    tmp_path, column: str, payload: str,
) -> None:
    path, journal = _prepared(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_plan_header SET {column}=? WHERE id=1", (payload,),
        )
    with pytest.raises(
        SyntheticPlanJournalRejected,
        match="synthetic plan header hydration admission failed",
    ):
        journal.recover()
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"SELECT {column} FROM synthetic_plan_header WHERE id=1"
        ).fetchone() == (payload,)


def test_healthy_cold_restart_retains_running_as_manual_only(tmp_path) -> None:
    path, original = _prepared(tmp_path)
    cold = SyntheticPlanJournal(path, original._steps)
    reviewed = cold.recover()
    assert reviewed.ambiguous_running_steps == ("root",)
    assert reviewed.step_statuses == (("root", "running", 1),)
    assert reviewed.dispatch_authorized is False
    assert reviewed.automatic_replay_authorized is False
    assert cold.recover().tail.event_count == 1
