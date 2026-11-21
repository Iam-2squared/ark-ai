"""Planner crash-recovery schema must not hydrate unlimited SQLite diagnostics.

These are disposable in-memory journals only, never tools or replay authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import planner_journal_review as planner


class _QuickCursor:
    def __init__(self, values: tuple[str, ...], sizes: list[int]):
        self.values = values
        self.sizes = sizes

    def fetchmany(self, size: int):
        self.sizes.append(size)
        assert size == 2
        return [(value,) for value in self.values[:size]]

    def fetchall(self):
        raise AssertionError("unbounded plan quick_check hydration")


class _Connection:
    def __init__(self, real: sqlite3.Connection, values: tuple[str, ...]):
        self.real = real
        self.values = values
        self.sizes: list[int] = []

    def execute(self, query: str):
        if query == "PRAGMA quick_check":
            return _QuickCursor(self.values, self.sizes)
        return self.real.execute(query)


@pytest.mark.parametrize(
    ("diagnostics", "allowed"),
    (
        (("ok",), True),
        (("synthetic-error",), False),
        (("ok", "unexpected-second-row"), False),
        (("synthetic-error", "second-error"), False),
    ),
)
def test_planner_quick_check_is_bounded_after_exact_schema(
    diagnostics: tuple[str, ...], allowed: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        for ddl in planner._SCHEMA:
            conn.execute(ddl)
        conn.execute("PRAGMA user_version=1")
        guarded = _Connection(conn, diagnostics)
        if allowed:
            planner._schema_check(guarded)
        else:
            with pytest.raises(
                planner.SyntheticPlanJournalRejected, match="quick_check",
            ):
                planner._schema_check(guarded)
        assert guarded.sizes == [2]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
