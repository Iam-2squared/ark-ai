"""Disconnected write-slot catalog identities must be bounded before hydration.

In-memory SQLite only, with no ToolBackend, real grant, or action execution.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


class _CatalogTrap:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.hydration_calls = 0

    def execute(self, statement: str):
        if statement.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            self.hydration_calls += 1
            pytest.fail("foreign write-slot catalog reached Python")
        return self.connection.execute(statement)


def _sqlite_schema() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(slots._DDL)
    conn.execute("PRAGMA user_version=1")
    return conn


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("name", "n" * 4200),
        ("tbl_name", "t" * 4200),
        ("type", "x" * 4200),
        ("name", "界" * 1400),
    ),
)
def test_write_slot_catalog_identity_bytes_are_preflighted(
    field: str, value: str,
) -> None:
    with _sqlite_schema() as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? "
            "WHERE type='table'",
            (value,),
        )
        guarded = _CatalogTrap(conn)
        with pytest.raises(
            slots.WriteSlotLedgerRejected, match="schema catalog preflight",
        ):
            slots._schema(guarded)
        assert guarded.hydration_calls == 0


def test_write_slot_cumulative_identifier_budget() -> None:
    with _sqlite_schema() as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? WHERE type='table'",
            ("n" * 2200, "t" * 2200),
        )
        guarded = _CatalogTrap(conn)
        with pytest.raises(
            slots.WriteSlotLedgerRejected, match="schema catalog preflight",
        ):
            slots._schema(guarded)
        assert guarded.hydration_calls == 0


def test_healthy_write_slot_schema_remains_unchanged() -> None:
    with _sqlite_schema() as conn:
        slots._schema(conn)
        assert conn.execute("PRAGMA user_version").fetchone() == (1,)
