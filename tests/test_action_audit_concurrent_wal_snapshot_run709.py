"""A paged action-audit read owns one coherent WAL snapshot.

A second SQLite writer is injected AFTER the reader pins its transaction and
BEFORE the full-history review. This is synthetic local evidence only, never
authorization, authenticated custody, or permission to dispatch a real tool.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(number: int) -> ToolCall:
    return ToolCall(
        "fixture.read", "fixture.read", "synthetic:scope",
        {"number": number},
    )


def _seed(path) -> SQLiteActionAudit:
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    for number in (1, 2, 3):
        audit.append(_call(number), outcome="synthetic")
    return audit


@pytest.mark.parametrize("concurrent_write", ("append", "corrupt_older_row"))
def test_paged_audit_read_uses_one_committed_wal_epoch(
    tmp_path, monkeypatch, concurrent_write,
):
    path = tmp_path / "audit.sqlite"
    reader = _seed(path)
    original_review = audit_module._require_valid_committed_audit_history
    writer_ran: list[str] = []

    def interleaved_history_review(conn: sqlite3.Connection) -> None:
        # Restore the original hook BEFORE reentering audit.append(), so the
        # writer exercises the production path without recursive callbacks.
        monkeypatch.setattr(
            audit_module, "_require_valid_committed_audit_history",
            original_review,
        )
        if concurrent_write == "append":
            writer = SQLiteActionAudit(path, clock_ms=lambda: 101)
            assert writer.append(_call(4), outcome="synthetic").event_id == 4
        else:
            with closing(sqlite3.connect(path)) as writer, writer:
                assert writer.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
                writer.execute(
                    "UPDATE action_events SET outcome='' WHERE event_id=1"
                )
        writer_ran.append(concurrent_write)
        original_review(conn)

    monkeypatch.setattr(
        audit_module, "_require_valid_committed_audit_history",
        interleaved_history_review,
    )
    # Page and full-history check must see the SAME pre-writer snapshot.
    assert [event.event_id for event in reader.events(limit=2)] == [1, 2]
    assert writer_ran == [concurrent_write]

    # A later, independent read MUST observe the newly committed writer.
    if concurrent_write == "append":
        assert [event.event_id for event in reader.events()] == [1, 2, 3, 4]
    else:
        with pytest.raises(ActionAuditSchemaError):
            reader.events(limit=2)

    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        expected_count = 4 if concurrent_write == "append" else 3
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone() == (
            expected_count,
        )
