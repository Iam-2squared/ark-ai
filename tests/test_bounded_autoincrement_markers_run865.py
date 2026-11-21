"""Bound Memory and ActionAudit AUTOINCREMENT marker hydration.

Synthetic in-memory v1 databases only. Local sqlite_sequence checks cannot
authenticate retained histories or authorize action replay.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import audit
from ark.memory import sqlite_store as memory


class _MarkerCursor:
    def __init__(self, values: tuple[tuple[int, ...], ...], sizes: list[int]):
        self.values = values
        self.sizes = sizes

    def fetchmany(self, size: int):
        assert size == 2
        self.sizes.append(size)
        return list(self.values[:size])

    def fetchall(self):
        raise AssertionError("unbounded sqlite_sequence marker hydration")


class _MarkerConnection:
    def __init__(
        self, conn: sqlite3.Connection, marker: str,
        values: tuple[tuple[int, ...], ...],
    ):
        self.conn = conn
        self.marker = marker
        self.values = values
        self.sizes: list[int] = []

    def execute(self, sql: str):
        if sql == self.marker:
            return _MarkerCursor(self.values, self.sizes)
        return self.conn.execute(sql)


@pytest.mark.parametrize(
    ("values", "valid"),
    (
        ((), True),
        (((1,),), False),
        (((1,), (2,), (3,)), False),
    ),
)
def test_memory_marker_hydration_is_bounded(
    values: tuple[tuple[int, ...], ...], valid: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(memory._SCHEMA_V1_SQL)
        wrapped = _MarkerConnection(
            conn, "SELECT seq FROM sqlite_sequence WHERE name='memory_events'",
            values,
        )
        if valid:
            memory._require_dense_committed_memory_events(wrapped)
        else:
            with pytest.raises(
                memory.MemorySchemaError, match="append high-water mismatch",
            ):
                memory._require_dense_committed_memory_events(wrapped)
        assert wrapped.sizes == [2]


@pytest.mark.parametrize(
    ("values", "valid"),
    (
        ((), True),
        (((1,),), False),
        (((1,), (2,), (3,)), False),
    ),
)
def test_action_audit_marker_hydration_is_bounded(
    values: tuple[tuple[int, ...], ...], valid: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(audit._AUDIT_SCHEMA_V1_SQL)
        wrapped = _MarkerConnection(
            conn, "SELECT seq FROM sqlite_sequence WHERE name='action_events'",
            values,
        )
        if valid:
            audit._require_dense_committed_audit_sequence(wrapped)
        else:
            with pytest.raises(
                audit.ActionAuditSchemaError, match="history was truncated",
            ):
                audit._require_dense_committed_audit_sequence(wrapped)
        assert wrapped.sizes == [2]


@pytest.mark.parametrize(
    ("ddl", "check", "error"),
    (
        (
            memory._SCHEMA_V1_SQL,
            memory._require_dense_committed_memory_events,
            memory.MemorySchemaError,
        ),
        (
            audit._AUDIT_SCHEMA_V1_SQL,
            audit._require_dense_committed_audit_sequence,
            audit.ActionAuditSchemaError,
        ),
    ),
)
def test_duplicate_sqlite_sequence_rows_fail_closed(
    ddl: str, check, error: type[Exception],
) -> None:
    name = (
        "memory_events"
        if check is memory._require_dense_committed_memory_events
        else "action_events"
    )
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(ddl)
        conn.execute(
            "INSERT INTO sqlite_sequence (name,seq) VALUES (?,?)", (name, 1),
        )
        with pytest.raises(error):
            check(conn)
