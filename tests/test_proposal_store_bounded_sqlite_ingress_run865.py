"""Bound local-only proposal catalog SQL and integrity diagnostics.

Every fixture is an in-memory synthetic SQLite database, never actual approval
or a permitted model promotion. The original proposal DDL is unchanged.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_proposal_store as proposals


class _DiagnosticCursor:
    def __init__(self, diagnostics: tuple[str, ...], sizes: list[int]):
        self.diagnostics = diagnostics
        self.sizes = sizes

    def fetchmany(self, size: int):
        self.sizes.append(size)
        assert size == 2
        return [(value,) for value in self.diagnostics[:size]]

    def fetchall(self):
        raise AssertionError("unbounded proposal diagnostic hydration")


class _DiagnosticConnection:
    def __init__(self, conn: sqlite3.Connection, diagnostics: tuple[str, ...]):
        self.conn = conn
        self.diagnostics = diagnostics
        self.sizes: list[int] = []

    def execute(self, sql: str):
        if sql == "PRAGMA quick_check":
            return _DiagnosticCursor(self.diagnostics, self.sizes)
        return self.conn.execute(sql)


class _NoDDLHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("proposal DDL hydrated before SQL-side admission")
        return super().execute(sql, parameters)


@pytest.mark.parametrize(
    ("diagnostics", "allowed"),
    (
        (("ok",), True),
        (("corrupt synthetic page",), False),
        (("ok", "extra diagnostic"), False),
        (("corrupt page", "other failure"), False),
    ),
)
def test_proposal_integrity_bounded_hydration(
    diagnostics: tuple[str, ...], allowed: bool,
) -> None:
    with sqlite3.connect(":memory:") as conn:
        conn.execute(proposals._DDL)
        conn.execute("PRAGMA user_version=1")
        wrapped = _DiagnosticConnection(conn, diagnostics)
        if allowed:
            proposals._schema(wrapped)
        else:
            with pytest.raises(
                proposals.DisconnectedProposalStoreRejected,
                match="proposal SQLite integrity failure",
            ):
                proposals._schema(wrapped)
        assert wrapped.sizes == [2]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)


def test_proposal_extra_catalog_object_rejected_without_hydrating_ddl() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        conn.execute(proposals._DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute("CREATE VIEW unexpected AS SELECT 1")
        with pytest.raises(
            proposals.DisconnectedProposalStoreRejected,
            match="proposal schema catalog preflight",
        ):
            proposals._schema(conn)


def test_proposal_oversize_ddl_rejected_with_original_object_count() -> None:
    with sqlite3.connect(":memory:", factory=_NoDDLHydration) as conn:
        long_name = "x" * 5_000
        conn.execute(proposals._DDL.replace(
            "UNIQUE(proposal_id,revision)",
            '"' + long_name + '" TEXT, UNIQUE(proposal_id,revision)',
        ))
        conn.execute("PRAGMA user_version=1")
        count, ddl_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 2 and ddl_bytes > 4_096
        with pytest.raises(
            proposals.DisconnectedProposalStoreRejected,
            match="proposal schema catalog preflight",
        ):
            proposals._schema(conn)
