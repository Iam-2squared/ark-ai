"""Audit live Memory rows against their own local CREATE/UPDATE/terminal history.

The audit is read-only, bounded and *not* a provenance/consent attestation.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)


def _write(scope, source="source", expires=None):
    return MemoryWrite(scope, source, "local content", expires_at_ms=expires)


def test_empty_ledger_audit_is_inert(tmp_path):
    store = _store(tmp_path)
    report = review_memory_event_alignment(store)
    assert (report.row_count, report.event_count, report.scope_count) == (0, 0, 0)
    assert report.last_event_id == 0
    assert len(report.digest) == 64
    assert report.action_authorized is False
    assert report.independently_authenticated is False
    assert report.user_consent_verified is False
    assert report.deletion_or_erasure_proven is False


def test_create_update_delete_recreate_revision_lifecycles(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    first = store.put(_write(scope))
    second = store.put(MemoryWrite(scope, "source", "updated"), expected_revision=1)
    assert first.revision == 1 and second.revision == 2
    assert store.delete(first.memory_id, scope, expected_revision=2)
    store.put(_write(scope), expected_revision=0)
    report = review_memory_event_alignment(store)
    assert (report.row_count, report.event_count, report.scope_count) == (1, 4, 1)
    assert report.last_event_id == 4


def test_expiry_and_multiple_scopes_leave_no_leaked_rows(tmp_path):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner-a", "ns"), "a", 4999))
    store.put(_write(MemoryScope("owner-b", "ns"), "b", 4999))
    assert store.purge_expired() == 2
    report = review_memory_event_alignment(store)
    assert (report.row_count, report.event_count, report.scope_count) == (0, 4, 2)
    assert report.last_event_id == 4


@pytest.mark.parametrize(
    ("sql", "params"),
    [
        ("DELETE FROM memory_events", ()),
        ("UPDATE memory_events SET revision=2 WHERE operation='create'", ()),
        ("UPDATE memory_events SET operation='update' WHERE operation='create'", ()),
        ("UPDATE memory_events SET operation='delete' WHERE operation='create'", ()),
        ("UPDATE memory_events SET owner_id='other'", ()),
        ("UPDATE memory_events SET memory_id='mem_' || lower(hex(randomblob(32)))", ()),
        ("UPDATE memory_events SET occurred_at_ms=-1", ()),
        ("UPDATE memory_events SET event_id=0", ()),
    ],
)
def test_altered_event_lifecycle_is_rejected(tmp_path, sql, params):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    with sqlite3.connect(store.path) as conn:
        conn.execute(sql, params)
    with pytest.raises(MemoryEventAlignmentRejected):
        review_memory_event_alignment(store)


def test_orphan_terminal_event_is_rejected(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    record = store.put(_write(scope))
    assert store.delete(record.memory_id, scope, expected_revision=1)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE operation='create'")
    with pytest.raises(MemoryEventAlignmentRejected, match="without active"):
        review_memory_event_alignment(store)


def test_live_row_without_event_is_rejected(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    store.put(_write(scope))
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(MemoryEventAlignmentRejected, match="no creation event"):
        review_memory_event_alignment(store)


def test_terminal_event_cannot_leave_row_live(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    store.put(_write(scope))
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET operation='delete'")
    with pytest.raises(MemoryEventAlignmentRejected):
        review_memory_event_alignment(store)


def test_bounded_event_scan_fails_closed(tmp_path, monkeypatch):
    import ark.memory.sqlite_event_alignment as audit

    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    monkeypatch.setattr(audit, "_MAX_EVENTS", 0)
    with pytest.raises(MemoryEventAlignmentRejected, match="event budget"):
        review_memory_event_alignment(store)


def test_audit_does_not_modify_rows_events_or_metadata(tmp_path):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    one = review_memory_event_alignment(store)
    two = review_memory_event_alignment(store)
    assert one == two
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before
