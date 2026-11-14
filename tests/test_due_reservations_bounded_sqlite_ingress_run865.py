"""Synthetic due-slot SQLite schema admission and bounded diagnostics.

In-memory fixtures only; a valid local ledger does not authenticate a clock,
authorize notifications, permit dispatch or prove independent provenance.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_due_reservation as due


class _QuickCursor:
    def __init__(self, diagnostics: tuple[str, ...], sizes: list[int]):
        self.diagnostics = diagnostics
        self.sizes = sizes

    def fetchmany(self, size: int):
        self.sizes.append(size)
        assert size == 2
        return [(item,) for item in self.diagnostics[:size]]

    def fetchall(self):
        raise AssertionError("unbounded due SQLite quick-check hydration")


class _QuickConnection:
    def __init__(self, conn: sqlite3.Connection, diagnostics: tuple[str, ...]):
        self.conn = conn
        self.diagnostics = diagnostics
        self.sizes: list[int] = []

    def execute(self, query: str):
        if query == "PRAGMA quick_check":
            return _QuickCursor(self.diagnostics, self.sizes)
        return self.conn.execute(query)


class _NoDDLHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("due DDL hydrated before SQLite preflight")
        return super().execute(sql, parameters)


@pytest.mark.parametrize(
    ("diagnostics", "allowed"),
    (
        (("ok",), True),
        (("corrupt synthetic page",), False),
        (("ok", "extra diagnostic"), False),
        (("corrupt synthetic page", "second error"), False),
    ),
)
def test_due_quick_check_bounded(
    diagnostics: tuple[str, ...], allowed: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        conn.execute(due._DDL)
        conn.execute("PRAGMA user_version=1")
        guarded = _QuickConnection(conn, diagnostics)
        if allowed:
            due._schema(guarded)
        else:
            with pytest.raises(
                due.DueReservationRejected, match="storage integrity failure",
            ):
                due._schema(guarded)
        assert guarded.sizes == [2]


def test_due_extra_catalog_object_refused_before_ddl_hydration() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        conn.execute(due._DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute("CREATE VIEW unexpected AS SELECT 1")
        with pytest.raises(
            due.DueReservationRejected, match="schema catalog preflight",
        ):
            due._schema(conn)


def test_due_oversized_catalog_rejected_at_exact_object_count() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        long_name = "x" * 5_000
        conn.execute(due._DDL[:-1] + ', "' + long_name + '" TEXT)')
        conn.execute("PRAGMA user_version=1")
        count, sql_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 2 and sql_bytes > 4_096
        with pytest.raises(
            due.DueReservationRejected, match="schema catalog preflight",
        ):
            due._schema(conn)
