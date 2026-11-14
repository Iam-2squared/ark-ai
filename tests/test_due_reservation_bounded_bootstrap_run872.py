"""Synthetic due reservation bootstrap refuses foreign unversioned SQLite files.

These tests only touch disposable temp paths. No scheduler notifications,
trusted-clock claims, real tool execution, or automatic recovery are allowed.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_due_reservation as due


@pytest.mark.parametrize(
    ("kind", "sql"),
    (
        ("table", "CREATE TABLE planted (id INTEGER)"),
        ("view", "CREATE VIEW planted AS SELECT 1 AS id"),
    ),
)
def test_due_create_refuses_nonempty_unversioned_sqlite_without_repair(
    tmp_path, kind: str, sql: str,
) -> None:
    path = tmp_path / "due.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(sql)
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)

    with pytest.raises(due.DueReservationRejected, match="unversioned nonempty"):
        due.DisconnectedDueReservations(path)

    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        objects = conn.execute(
            "SELECT type,name FROM sqlite_master ORDER BY name"
        ).fetchall()
    assert objects == [(kind, "planted")]


def test_due_empty_unversioned_sqlite_bootstraps_without_foreign_objects(
    tmp_path,
) -> None:
    path = tmp_path / "due.sqlite"
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone() is None
    due.DisconnectedDueReservations(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (1,)
        objects = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    assert objects == [("due_reservations",)]
