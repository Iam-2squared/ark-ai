"""Planner's disposable SQLite schema oracle must never retain an open handle.

These are local, deterministic, synthetic Planner fixtures. A recovered
RUNNING status remains UNKNOWN and authorizes neither dispatch nor replay.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.agency.planner_journal_review as planner
from ark.agency.contracts import PlanStep, ToolCall


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep("root", ToolCall("mock", "fixture.read", "local", {})),
    )


def _track_oracle(monkeypatch):
    opened: list[sqlite3.Connection] = []
    closed: list[sqlite3.Connection] = []
    original_connect = sqlite3.connect

    class TrackedOracle(sqlite3.Connection):
        def close(self):
            closed.append(self)
            return super().close()

    def connect(database, *args, **kwargs):
        if database == ":memory:":
            assert "factory" not in kwargs
            kwargs["factory"] = TrackedOracle
            created = original_connect(database, *args, **kwargs)
            opened.append(created)
            return created
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(planner.sqlite3, "connect", connect)
    return opened, closed


def test_schema_oracle_handles_close_after_initialization_and_cold_recovery(
    tmp_path: Path, monkeypatch,
) -> None:
    opened, closed = _track_oracle(monkeypatch)
    journal = planner.SyntheticPlanJournal(tmp_path / "plan.sqlite", _steps())
    for _ in range(3):
        recovery = journal.recover()
        assert recovery.tail.event_count == 0
        assert recovery.dispatch_authorized is False
        assert recovery.automatic_replay_authorized is False
    assert len(opened) >= 2
    assert len(opened) == len(closed)
    assert all(a is b for a, b in zip(opened, closed, strict=True))


def test_schema_oracle_closes_on_foreign_catalog_rejection(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "plan.sqlite"
    journal = planner.SyntheticPlanJournal(path, _steps())
    # The fixture is disposable. A different table layout with the same
    # object count must be rejected without leaking its comparison handle.
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE synthetic_plan_events")
        conn.execute("CREATE TABLE synthetic_plan_events (wrong TEXT)")
    opened, closed = _track_oracle(monkeypatch)
    with pytest.raises(planner.SyntheticPlanJournalRejected, match="schema changed"):
        journal.recover()
    assert len(opened) == len(closed) == 1
    assert opened[0] is closed[0]


def test_schema_oracle_closes_when_metadata_inspection_raises(
    tmp_path: Path, monkeypatch,
) -> None:
    journal = planner.SyntheticPlanJournal(tmp_path / "plan.sqlite", _steps())
    opened, closed = _track_oracle(monkeypatch)

    def fail_inspection(_connection):
        raise RuntimeError("synthetic metadata inspection fault")

    monkeypatch.setattr(planner, "_objects", fail_inspection)
    with pytest.raises(RuntimeError, match="synthetic metadata inspection fault"):
        journal.recover()
    assert len(opened) == len(closed) == 1
    assert opened[0] is closed[0]
