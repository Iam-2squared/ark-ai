"""Bound the disconnected atomic pre-action schema and quick-check ingress.

Only fabricated :memory: SQLite fixtures are used. A clean local schema does
not authenticate an audit, consent or authorize real tool execution.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


class _QuickCursor:
    def __init__(self, diagnostics: tuple[str, ...], sizes: list[int]):
        self.diagnostics = diagnostics
        self.sizes = sizes

    def fetchmany(self, size: int):
        self.sizes.append(size)
        assert size == 2
        return [(value,) for value in self.diagnostics[:size]]

    def fetchall(self):
        raise AssertionError("unbounded quick_check diagnostic hydration")


class _QuickConnection:
    def __init__(self, connection: sqlite3.Connection, diagnostics: tuple[str, ...]):
        self.connection = connection
        self.diagnostics = diagnostics
        self.sizes: list[int] = []

    def execute(self, query: str):
        if query == "PRAGMA quick_check":
            return _QuickCursor(self.diagnostics, self.sizes)
        return self.connection.execute(query)


class _NoDDLHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("private schema hydrated before SQLite preflight")
        return super().execute(sql, parameters)


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(atomic._INTENTS)
    conn.execute(atomic._AUDITS)
    conn.execute("PRAGMA user_version=1")


@pytest.mark.parametrize(
    ("diagnostics", "allowed"),
    (
        (("ok",), True),
        (("synthetic-corruption",), False),
        (("ok", "synthetic-second-diagnostic"), False),
        (("synthetic-corruption", "other-error"), False),
    ),
)
def test_atomic_preaction_quick_check_is_bounded(
    diagnostics: tuple[str, ...], allowed: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        _create_schema(conn)
        guarded = _QuickConnection(conn, diagnostics)
        if allowed:
            atomic._schema(guarded)
        else:
            with pytest.raises(
                atomic.AtomicPreactionRejected, match="SQLite integrity failure",
            ):
                atomic._schema(guarded)
        assert guarded.sizes == [2]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)


def test_atomic_preaction_extra_catalog_object_rejected_before_hydration() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        _create_schema(conn)
        conn.execute("CREATE VIEW unexpected AS SELECT 1")
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="schema catalog preflight",
        ):
            atomic._schema(conn)


def test_atomic_preaction_oversize_ddl_rejected_before_hydration() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        long_name = "x" * 5_000
        conn.execute(atomic._INTENTS[:-1] + ', "' + long_name + '" TEXT)')
        conn.execute(atomic._AUDITS)
        conn.execute("PRAGMA user_version=1")
        count, ddl_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 4 and ddl_bytes > 4_096
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="schema catalog preflight",
        ):
            atomic._schema(conn)
