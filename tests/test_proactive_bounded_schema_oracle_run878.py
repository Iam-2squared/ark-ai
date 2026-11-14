"""Bound proactive synthetic SQLite admissions and close its DDL oracle.

All data is disposable local fixtures, not live scheduling or notifications.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.proactive_synthetic_review as proactive


def _fixture(ddl: str = proactive._TABLE) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl)
    conn.execute("PRAGMA user_version=1")
    return conn


def _track_oracle(monkeypatch):
    seen: list[sqlite3.Connection] = []
    original = proactive.closing

    def tracked(conn):
        seen.append(conn)
        return original(conn)

    monkeypatch.setattr(proactive, "closing", tracked)
    return seen


def _assert_closed(seen: list[sqlite3.Connection]) -> None:
    assert len(seen) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        seen[0].execute("SELECT 1")


def test_proactive_oracle_closes_on_valid_empty_schema(monkeypatch) -> None:
    with closing(_fixture()) as conn:
        seen = _track_oracle(monkeypatch)
        proactive._validate(conn)
        _assert_closed(seen)


def test_proactive_oracle_closes_on_same_count_foreign_schema(
    monkeypatch,
) -> None:
    ddl = proactive._TABLE.replace(
        "prepared_at_ms INTEGER NOT NULL", "prepared_at_ms TEXT NOT NULL",
    )
    with closing(_fixture(ddl)) as conn:
        seen = _track_oracle(monkeypatch)
        with pytest.raises(
            proactive.SyntheticTriggerRejected, match="schema changed",
        ):
            proactive._validate(conn)
        _assert_closed(seen)


def test_proactive_catalog_preflight_rejects_foreign_view_without_hydrating(
    monkeypatch,
) -> None:
    class NoDDL(sqlite3.Connection):
        def execute(self, sql, parameters=(), /):
            if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
                raise AssertionError("catalog hydrated before preflight")
            return super().execute(sql, parameters)

    with closing(sqlite3.connect(":memory:", factory=NoDDL)) as conn:
        conn.execute(proactive._TABLE)
        conn.execute("CREATE VIEW foreign_view AS SELECT 1")
        conn.execute("PRAGMA user_version=1")
        seen = _track_oracle(monkeypatch)
        with pytest.raises(
            proactive.SyntheticTriggerRejected, match="schema changed",
        ):
            proactive._validate(conn)
        _assert_closed(seen)


@pytest.mark.parametrize(
    ("diagnostics", "valid"),
    [
        (("ok",), True),
        (("corrupt",), False),
        (("ok", "extra diagnostic"), False),
    ],
)
def test_proactive_quick_check_reads_no_more_than_two_diagnostics(
    diagnostics: tuple[str, ...], valid: bool,
) -> None:
    class QuickCursor:
        def fetchmany(self, size):
            sizes.append(size)
            assert size == 2
            return [(item,) for item in diagnostics[:size]]

        def fetchall(self):
            raise AssertionError("unbounded diagnostic materialization")

    class Guarded:
        def execute(self, sql, *args):
            if sql == "PRAGMA quick_check":
                return QuickCursor()
            return conn.execute(sql, *args)

    sizes: list[int] = []
    with closing(_fixture()) as conn:
        if valid:
            proactive._validate(Guarded())
        else:
            with pytest.raises(
                proactive.SyntheticTriggerRejected, match="integrity failed",
            ):
                proactive._validate(Guarded())
    assert sizes == [2]
