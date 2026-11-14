"""Read-only, synthetic READ journal SQL and hydration admission regressions.

All fixtures use in-memory SQLite; no real read tool, private content,
execution permission, user approval or authentic provenance is inferred.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_read_journal as read


class _QuickCursor:
    def __init__(self, diagnostics: tuple[str, ...], sizes: list[int]):
        self.diagnostics = diagnostics
        self.sizes = sizes

    def fetchmany(self, size: int):
        assert size == 2
        self.sizes.append(size)
        return [(value,) for value in self.diagnostics[:size]]

    def fetchall(self):
        raise AssertionError("unbounded SQLite quick-check hydration")


class _QuickConnection:
    def __init__(self, conn: sqlite3.Connection, diagnostics: tuple[str, ...]):
        self.conn = conn
        self.diagnostics = diagnostics
        self.sizes: list[int] = []

    def execute(self, sql: str):
        if sql == "PRAGMA quick_check":
            return _QuickCursor(self.diagnostics, self.sizes)
        return self.conn.execute(sql)


class _NoDDLHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("read journal DDL hydrated before SQL preflight")
        return super().execute(sql, parameters)


class _BoundedReceiptCursor:
    def __init__(self, sizes: list[int]):
        self.sizes = sizes

    def fetchmany(self, size: int):
        self.sizes.append(size)
        assert size == read._MAX_ROWS + 1
        return [("private synthetic placeholder",) * 8] * size

    def fetchall(self):
        raise AssertionError("unbounded receipt hydration")


class _BoundedReceiptConnection(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT seq, request_id, step_id"):
            return _BoundedReceiptCursor(self.receipt_sizes)
        return super().execute(sql, parameters)


def _schema(conn: sqlite3.Connection) -> None:
    conn.execute(read._MARKER_DDL)
    conn.execute(read._RECEIPT_DDL)


@pytest.mark.parametrize(
    ("diagnostics", "allowed"),
    (
        (("ok",), True),
        (("corrupt synthetic page",), False),
        (("ok", "second diagnostic"), False),
        (("corrupt synthetic page", "second error"), False),
    ),
)
def test_read_journal_bounded_integrity_results(
    diagnostics: tuple[str, ...], allowed: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        _schema(conn)
        guarded = _QuickConnection(conn, diagnostics)
        if allowed:
            read._verify_schema(guarded)
        else:
            with pytest.raises(
                read.ReadJournalRejected, match="SQLite integrity failure",
            ):
                read._verify_schema(guarded)
        assert guarded.sizes == [2]


def test_read_journal_extra_catalog_rejected_before_python_sql() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        _schema(conn)
        conn.execute("CREATE VIEW unexpected AS SELECT 1")
        with pytest.raises(
            read.ReadJournalRejected, match="schema catalog preflight",
        ):
            read._verify_schema(conn)


def test_read_journal_oversize_ddl_rejected_at_exact_object_count() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        conn.execute(read._MARKER_DDL)
        long_name = "z" * 5_000
        conn.execute(read._RECEIPT_DDL[:-1] + ', "' + long_name + '" TEXT)')
        count, sql_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 3 and sql_bytes > 4_096
        with pytest.raises(
            read.ReadJournalRejected, match="schema catalog preflight",
        ):
            read._verify_schema(conn)


def test_read_journal_marker_scan_rejects_more_than_one_row() -> None:
    with sqlite3.connect(":memory:") as conn:
        _schema(conn)
        conn.executemany(
            "INSERT INTO marker VALUES (?)",
            [(read._SCHEMA,), (read._SCHEMA,), (read._SCHEMA,)],
        )
        journal = read.DisconnectedReadJournal(conn)
        with pytest.raises(read.ReadJournalRejected, match="foreign journal marker"):
            journal._scan()


def test_read_journal_receipts_are_bounded_before_validation() -> None:
    with sqlite3.connect(":memory:", factory=_BoundedReceiptConnection) as conn:
        _schema(conn)
        conn.execute("INSERT INTO marker VALUES (?)", (read._SCHEMA,))
        conn.receipt_sizes = []
        journal = read.DisconnectedReadJournal(conn)
        with pytest.raises(read.ReadJournalRejected, match="journal row budget"):
            journal._scan()
        assert conn.receipt_sizes == [read._MAX_ROWS + 1]
