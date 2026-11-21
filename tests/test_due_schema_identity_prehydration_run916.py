"""Bound synthetic due ledger catalog identities before Python hydration.

All mutations use a disposable in-memory SQLite schema; no real scheduler,
trusted clock, notification, tool execution or approval is involved.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import disconnected_due_reservation as due


class _RefuseHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("catalog identity hydrated before SQLite budget")
        return super().execute(sql, parameters)


@pytest.mark.parametrize("column", ("type", "name", "tbl_name"))
def test_oversized_stored_catalog_identity_rejected_before_hydration(column):
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        conn.execute(due._DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? WHERE type='table'",
            ("x" * 4_097,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0:2] == (2, len(due._DDL.encode("utf-8")))
        with pytest.raises(due.DueReservationRejected, match="catalog preflight"):
            due._schema(conn)


def test_multibyte_catalog_name_uses_utf8_bytes_not_character_count():
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        conn.execute(due._DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=? WHERE type='table'",
            ("山" * 1_400,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT length(name),length(CAST(name AS BLOB)) "
            "FROM sqlite_master WHERE type='table'"
        ).fetchone() == (1_400, 4_200)
        with pytest.raises(due.DueReservationRejected, match="catalog preflight"):
            due._schema(conn)


def test_split_short_identifiers_exceed_cumulative_byte_budget():
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        conn.execute(due._DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?, tbl_name=? WHERE type='table'",
            ("a" * 2_050, "b" * 2_050),
        )
        conn.commit()
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] < 4_096
        with pytest.raises(due.DueReservationRejected, match="catalog preflight"):
            due._schema(conn)


def test_original_due_schema_passes_identity_budget():
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute(due._DDL)
        conn.execute("PRAGMA user_version=1")
        due._schema(conn)
