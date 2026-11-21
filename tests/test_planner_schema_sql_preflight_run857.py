"""Reject oversized Planner SQLite metadata before Python DDL hydration.

This is a synthetic crash-replay schema fixture, not permission to retry a
RUNNING step, dispatch a tool or trust local provenance after rollback.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import planner_journal_review as journal


class _NoDDLHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("unbounded plan DDL was fetched into Python")
        return super().execute(sql, parameters)


def _schema_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", factory=_NoDDLHydration)
    for ddl in journal._SCHEMA:
        conn.execute(ddl)
    conn.execute("PRAGMA user_version=1")
    return conn


def test_valid_synthetic_plan_schema_still_passes() -> None:
    with _schema_db() as conn:
        # This path must reach its exact-DDL comparison when within the bound.
        # Use a normal connection since the sentinel forbids DDL hydration.
        with sqlite3.connect(":memory:") as normal:
            for ddl in journal._SCHEMA:
                normal.execute(ddl)
            normal.execute("PRAGMA user_version=1")
            journal._schema_check(normal)
        count, sql_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 2
        assert 0 < sql_bytes < 4096


def test_added_plan_view_refused_before_ddl_hydration() -> None:
    with _schema_db() as conn:
        conn.execute("CREATE VIEW unexpected AS SELECT 1")
        with pytest.raises(
            journal.SyntheticPlanJournalRejected,
            match="schema changed: preflight budget",
        ):
            journal._schema_check(conn)


def test_oversized_plan_schema_refused_before_ddl_hydration() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        conn.execute(journal._SCHEMA[0])
        huge_name = "z" * 5000
        conn.execute(
            'CREATE TABLE synthetic_plan_events(seq INTEGER PRIMARY KEY, "'
            + huge_name + '" TEXT)'
        )
        conn.execute("PRAGMA user_version=1")
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] > 4096
        with pytest.raises(
            journal.SyntheticPlanJournalRejected,
            match="schema changed: preflight budget",
        ):
            journal._schema_check(conn)
