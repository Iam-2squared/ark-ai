"""Reject forged READ-journal catalog identifiers before Python hydration.

Disconnected, digest-only SQLite specimens; no READ backend is executed.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_read_journal as read_journal


class _NoHydration:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.hydration_calls = 0

    def execute(self, statement: str):
        if statement.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            self.hydration_calls += 1
            pytest.fail("oversized READ-journal schema reached Python")
        return self.conn.execute(statement)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("name", "n" * 4300),
        ("tbl_name", "t" * 4300),
        ("type", "x" * 4300),
        ("name", "表" * 1400),
    ),
)
def test_catalog_identifier_byte_budget_precedes_hydration(
    tmp_path, field: str, value: str,
) -> None:
    path = tmp_path / "detached-read.sqlite"
    with read_journal.DisconnectedReadJournal.create(path):
        pass
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? WHERE name='marker'",
            (value,),
        )
        guarded = _NoHydration(conn)
        with pytest.raises(
            read_journal.ReadJournalRejected, match="schema catalog preflight",
        ):
            read_journal._verify_schema(guarded)
        assert guarded.hydration_calls == 0


def test_cumulative_small_catalog_identifiers_denied(tmp_path) -> None:
    path = tmp_path / "detached-read.sqlite"
    with read_journal.DisconnectedReadJournal.create(path):
        pass
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? WHERE name='marker'",
            ("n" * 2200, "t" * 2200),
        )
        guarded = _NoHydration(conn)
        with pytest.raises(
            read_journal.ReadJournalRejected, match="schema catalog preflight",
        ):
            read_journal._verify_schema(guarded)
        assert guarded.hydration_calls == 0


def test_clean_read_journal_recovers_without_execution_permission(tmp_path) -> None:
    path = tmp_path / "detached-read.sqlite"
    with read_journal.DisconnectedReadJournal.create(path):
        expected = read_journal.genesis_witness()
    with read_journal.DisconnectedReadJournal.open(path) as reopened:
        recovered = reopened.recover_receipts(expected)
    assert recovered.witness == expected
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
