"""Synthetic quarantine SQLite catalog identity has a fixed byte budget.

The corrupted catalogs exist only in in-memory SQLite fixtures. Nothing in
these tests authorizes notification, execution, retry, or consent.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark import disconnected_schedule_quarantine_ledger as quarantine


class _RefuseHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("quarantine catalog hydrated before SQLite preflight")
        return super().execute(sql, parameters)


def _prepare(conn):
    for statement in quarantine._DDL:
        conn.execute(statement)
    conn.execute("PRAGMA user_version=1")
    conn.execute("PRAGMA writable_schema=ON")


def _inspect(conn):
    # The schema preflight precedes all policy and row checks. These inert
    # scalars are only a fixture input, not an authenticated policy epoch.
    return quarantine._validate(conn, ("f" * 64, 1_000, 100, 5, 10))


@pytest.mark.parametrize("field", ("type", "name", "tbl_name"))
def test_quarantine_stored_catalog_identity_rejected_before_hydration(field):
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        _prepare(conn)
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? WHERE type='table'",
            ("a" * 8_193,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] < 8_192
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected, match="schema preflight budget",
        ):
            _inspect(conn)


def test_quarantine_catalog_budget_uses_utf8_bytes():
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        _prepare(conn)
        conn.execute(
            "UPDATE sqlite_master SET name=? WHERE name='policy'",
            ("山" * 2_750,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT length(name),length(CAST(name AS BLOB)) "
            "FROM sqlite_master WHERE type='table' AND name LIKE ?",
            ("山%",),
        ).fetchone() == (2_750, 8_250)
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected, match="schema preflight budget",
        ):
            _inspect(conn)


def test_quarantine_cumulative_short_identifiers_exceed_budget():
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        _prepare(conn)
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? WHERE name='policy'",
            ("a" * 4_100, "b" * 4_100),
        )
        conn.commit()
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected, match="schema preflight budget",
        ):
            _inspect(conn)


def test_unchanged_quarantine_catalog_is_accepted_by_local_constructor(tmp_path):
    path = tmp_path / "quarantine-catalog.sqlite"
    policy = quarantine.QuarantinePolicy(
        policy_sha256="f" * 64,
        first_ms=1_000,
        interval_ms=1_000,  # Policy requires at least 1,000 ms; test intact catalog.
        count=5,
        grace_ms=10,
    )
    quarantine.DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    cold = quarantine.DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert cold is not None
