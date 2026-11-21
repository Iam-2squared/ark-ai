"""Bound private-context SQLite catalog names before Python schema hydration.

Disposable, synthetic hash-only replay databases; no consent or live context
ingestion. Tampered catalog rows never leave SQLite for Python comparison.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark import personal_context_replay_ledger as replay


class _HydrationTrap:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.hydration_calls = 0

    def execute(self, sql: str):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            self.hydration_calls += 1
            pytest.fail("unbounded private schema identifiers reached Python")
        return self.conn.execute(sql)


@pytest.mark.parametrize(
    ("field", "malicious"),
    (
        ("name", "x" * 9000),
        ("tbl_name", "x" * 9000),
        ("type", "x" * 9000),
        ("name", "界" * 2900),
    ),
)
def test_forged_catalog_identifier_refused_before_hydration(
    tmp_path, field: str, malicious: str,
) -> None:
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.db", create=True,
    )
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? WHERE name='context_requests'",
            (malicious,),
        )
        guarded = _HydrationTrap(conn)
        with pytest.raises(
            replay.OfflineContextReplayRejected, match="schema drift.*preflight",
        ):
            replay._schema(guarded)
        assert guarded.hydration_calls == 0


def test_cumulative_catalog_bytes_refused_before_hydration(tmp_path) -> None:
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.db", create=True,
    )
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? "
            "WHERE name='context_requests'",
            ("n" * 4500, "t" * 4500),
        )
        guarded = _HydrationTrap(conn)
        with pytest.raises(
            replay.OfflineContextReplayRejected, match="schema drift.*preflight",
        ):
            replay._schema(guarded)
        assert guarded.hydration_calls == 0


def test_normal_cold_context_ledger_still_read_only(tmp_path) -> None:
    path = tmp_path / "context.db"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    baseline = ledger.witness()
    cold = replay.DisconnectedContextReplayLedger(path)
    assert cold.witness() == baseline
    assert baseline.independent_custody_proven is False
