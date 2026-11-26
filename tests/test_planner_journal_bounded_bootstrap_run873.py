"""Planner bootstrap must not enumerate an unversioned foreign catalog.

All steps and databases are synthetic; recovered plans cannot execute tools.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.agency.planner_journal_review as planner_journal
from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps():
    return (PlanStep("first", ToolCall("fixture", "read", "local", {})),)


class _NoUnversionedCatalogHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            version = super().execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                raise AssertionError("Planner bootstrap must not hydrate a foreign catalog")
        return super().execute(sql, parameters)


def test_clean_planner_bootstrap_preserves_inert_recovery(tmp_path):
    path = tmp_path / "plan.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    recovered = journal.recover()
    assert recovered.tail.event_count == 0
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False


@pytest.mark.parametrize(
    "foreign_ddl",
    ("CREATE TABLE unexpected(x INTEGER)", "CREATE VIEW unexpected AS SELECT 1"),
)
def test_unversioned_foreign_plan_schema_refused_without_repair(tmp_path, foreign_ddl):
    path = tmp_path / "plan.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(foreign_ddl)
    with pytest.raises(
        SyntheticPlanJournalRejected, match="unversioned synthetic plan",
    ):
        SyntheticPlanJournal(path, _steps())
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='unexpected'"
        ).fetchone() == ("unexpected",)
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='synthetic_plan_header'"
        ).fetchone() is None


def test_foreign_catalog_never_hydrated_before_bootstrap_rejection(
    tmp_path, monkeypatch,
):
    path = tmp_path / "plan.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unexpected(x TEXT)")
    original_connect = sqlite3.connect

    def guarded_connect(database, *args, **kwargs):
        if database == path:
            kwargs["factory"] = _NoUnversionedCatalogHydration
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(planner_journal.sqlite3, "connect", guarded_connect)
    with pytest.raises(
        SyntheticPlanJournalRejected, match="unversioned synthetic plan",
    ):
        SyntheticPlanJournal(path, _steps())


def test_clean_planner_catalog_can_be_validated_after_versioned_bootstrap(
    tmp_path, monkeypatch,
):
    path = tmp_path / "plan.sqlite"
    original_connect = sqlite3.connect

    def guarded_connect(database, *args, **kwargs):
        if database == path:
            kwargs["factory"] = _NoUnversionedCatalogHydration
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(planner_journal.sqlite3, "connect", guarded_connect)
    journal = SyntheticPlanJournal(path, _steps())
    assert journal.recover().tail.event_count == 0
