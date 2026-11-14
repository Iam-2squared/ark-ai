"""Bound disconnected WRITE reservation catalog/diagnostic hydration.

Only inert in-memory SQLite fixtures; no write dispatch, issuer, consent,
replay or external exactly-once effect can follow from a passing test.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slot


class _Diagnostics:
    def __init__(self, rows: tuple[str, ...], sizes: list[int]):
        self.rows = rows
        self.sizes = sizes

    def fetchmany(self, size: int):
        self.sizes.append(size)
        assert size == 2
        return [(message,) for message in self.rows[:size]]

    def fetchall(self):
        raise AssertionError("unbounded quick_check result hydration")


class _Connection:
    def __init__(self, real: sqlite3.Connection, rows: tuple[str, ...]):
        self.real = real
        self.rows = rows
        self.sizes: list[int] = []

    def execute(self, sql: str):
        if sql == "PRAGMA quick_check":
            return _Diagnostics(self.rows, self.sizes)
        return self.real.execute(sql)


class _NoCatalogHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("private catalog hydrated before SQL-side budget")
        return super().execute(sql, parameters)


@pytest.mark.parametrize(
    ("diagnostics", "accept"),
    (
        (("ok",), True),
        (("broken",), False),
        (("ok", "second error"), False),
    ),
)
def test_write_slot_bounded_integrity_diagnostics(
    diagnostics: tuple[str, ...], accept: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        conn.execute(slot._DDL)
        conn.execute("PRAGMA user_version=1")
        guarded = _Connection(conn, diagnostics)
        if accept:
            slot._schema(guarded)
        else:
            with pytest.raises(
                slot.WriteSlotLedgerRejected, match="SQLite integrity failure",
            ):
                slot._schema(guarded)
        assert guarded.sizes == [2]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)


def test_write_slot_extra_catalog_refused_before_hydration() -> None:
    with sqlite3.connect(":memory:", factory=_NoCatalogHydration) as conn:
        conn.execute(slot._DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute("CREATE VIEW extra AS SELECT 1")
        with pytest.raises(
            slot.WriteSlotLedgerRejected, match="schema catalog preflight",
        ):
            slot._schema(conn)


def test_write_slot_large_ddl_refused_before_hydration() -> None:
    with sqlite3.connect(":memory:", factory=_NoCatalogHydration) as conn:
        ddl = slot._DDL.replace(
            "UNIQUE(plan_id, step_id))",
            '"' + "z" * 5_000 + '" TEXT, UNIQUE(plan_id, step_id))',
        )
        conn.execute(ddl)
        conn.execute("PRAGMA user_version=1")
        count, ddl_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 3 and ddl_bytes > 4_096
        with pytest.raises(
            slot.WriteSlotLedgerRejected, match="schema catalog preflight",
        ):
            slot._schema(conn)
