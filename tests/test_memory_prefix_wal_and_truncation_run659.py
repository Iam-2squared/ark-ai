"""Retained Memory prefix audits resist WAL append races and local tail loss.

Only disposable synthetic SQLite fixture rows are touched. Prefix hashes and
sequence high-water are LOCAL diagnostics, not user consent, secure deletion,
authenticated writer identity, or authority to retry any WRITE.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.memory.sqlite_event_prefix_review as prefix
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)


@pytest.mark.parametrize("mutation", ("create", "update", "delete"))
def test_memory_prefix_scan_keeps_precommit_wal_snapshot(
    tmp_path, monkeypatch, mutation,
):
    path = tmp_path / "memory-prefix-wal.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 10)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 20)
    created = reader.put(MemoryWrite(scope, "first-source", "synthetic first"))
    before = prefix.capture_local_memory_event_prefix(reader)
    assert (before.event_count, before.last_event_id) == (1, 1)
    committed = []
    original = prefix._charge

    def append_during_scan(hasher, event):
        original(hasher, event)
        if committed:
            return
        if mutation == "create":
            writer.put(MemoryWrite(
                MemoryScope("other-synthetic-owner", "private"),
                "second-source", "synthetic second",
            ))
        elif mutation == "update":
            writer.put(
                MemoryWrite(scope, "first-source", "synthetic changed"),
                expected_revision=created.revision,
            )
        else:
            assert writer.delete(
                created.memory_id, scope, expected_revision=created.revision,
            )
        committed.append(mutation)

    with monkeypatch.context() as patch:
        patch.setattr(prefix, "_charge", append_during_scan)
        during = prefix.capture_local_memory_event_prefix(reader)

    assert committed == [mutation]
    assert during == before
    assert during.action_authorized is False
    assert during.independently_authenticated is False

    fresh = prefix.capture_local_memory_event_prefix(reader)
    assert fresh.event_count == 2
    assert fresh.last_event_id == 2
    assert fresh.prefix_sha256 != before.prefix_sha256
    comparison = prefix.compare_local_memory_event_prefix(reader, before)
    assert comparison.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert comparison.previous_event_count == 1
    assert comparison.current_event_count == 2
    assert comparison.action_authorized is False
    assert comparison.historical_writer_authenticated is False


@pytest.mark.parametrize("removed_event", (1, 2, 3))
def test_missing_event_at_any_position_is_detected_by_both_audits(
    tmp_path, removed_event,
):
    path = tmp_path / "missing-event.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    records = [
        store.put(MemoryWrite(scope, f"source-{i}", f"fixture-{i}"))
        for i in range(3)
    ]
    retained = prefix.capture_local_memory_event_prefix(store)
    assert retained.event_count == 3
    assert review_memory_event_alignment(store).event_count == 3

    # Controlled corruption of an EPHEMERAL test file only; v1 has no
    # production journal deletion or compaction API.
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=?", (removed_event,))
        if removed_event == 3:
            # The remaining rows and events form an otherwise valid 2-event
            # world. Its AUTOINCREMENT high-water must still expose tail loss.
            conn.execute(
                "DELETE FROM memories WHERE memory_id=?", (records[2].memory_id,),
            )

    with pytest.raises(MemoryEventAlignmentRejected):
        review_memory_event_alignment(store)
    with pytest.raises(prefix.MemoryEventPrefixRejected):
        prefix.capture_local_memory_event_prefix(store)
    with pytest.raises(prefix.MemoryEventPrefixRejected):
        prefix.compare_local_memory_event_prefix(store, retained)
