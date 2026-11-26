"""Memory event pagination retains a coherent WAL read snapshot.

All writers use disposable local SQLite handles. This confirms snapshot
isolation, not authenticated history, independent custody or consent.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.memory.sqlite_store as store_module
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "events-wal-race.sqlite", clock_ms=lambda: 2000,
    )
    peer = SQLiteMemoryStore(store.path, clock_ms=lambda: 2001)
    own = MemoryScope("owner", "notes")
    foreign = MemoryScope("foreign", "private")
    return store, peer, own, foreign


@pytest.mark.parametrize("writer_scope", ("own", "foreign"))
def test_new_wal_event_cannot_appear_after_global_scan_in_same_read(
    tmp_path, monkeypatch, writer_scope,
):
    store, peer, own, foreign = _fixture(tmp_path)
    first = store.put(MemoryWrite(own, "first", "safe fixture"))
    expected_first = store.events(own)[0]
    original = store_module._require_dense_committed_memory_events
    inserted = []

    def concurrent_append(conn):
        original(conn)
        # The global COUNT/MIN/MAX and sqlite_sequence reads already pinned
        # this SQLite snapshot. A second handle may commit in WAL mode.
        if not inserted:
            selected = own if writer_scope == "own" else foreign
            inserted.append(peer.put(MemoryWrite(
                selected, "later", "later synthetic content",
            )))

    monkeypatch.setattr(
        store_module, "_require_dense_committed_memory_events", concurrent_append,
    )
    initial = store.events(own)
    assert len(inserted) == 1
    assert initial == [expected_first]
    assert initial[0].memory_id == first.memory_id
    monkeypatch.setattr(
        store_module, "_require_dense_committed_memory_events", original,
    )
    next_read = store.events(own)
    if writer_scope == "own":
        assert [event.memory_id for event in next_read] == [
            first.memory_id, inserted[0].memory_id,
        ]
    else:
        assert next_read == initial
    assert "later synthetic content" not in repr(initial + next_read)


def test_foreign_event_corruption_after_scan_is_visible_only_next_read(
    tmp_path, monkeypatch,
):
    store, _, own, foreign = _fixture(tmp_path)
    record = store.put(MemoryWrite(own, "own", "own fixture"))
    store.put(MemoryWrite(foreign, "foreign", "private fixture"))
    original = store_module._require_dense_committed_memory_events
    changed = []

    def mutate_after_snapshot(conn):
        original(conn)
        if not changed:
            # Mutation of *another* connection cannot rewrite a pinned
            # SQLite read epoch. It must be rejected on the next read.
            with sqlite3.connect(store.path) as writer:
                writer.execute(
                    "DELETE FROM memory_events WHERE event_id=2",
                )
            changed.append(True)

    monkeypatch.setattr(
        store_module, "_require_dense_committed_memory_events",
        mutate_after_snapshot,
    )
    old_epoch = store.events(own)
    assert changed == [True]
    assert [event.memory_id for event in old_epoch] == [record.memory_id]
    monkeypatch.setattr(
        store_module, "_require_dense_committed_memory_events", original,
    )
    with pytest.raises(MemorySchemaError, match="global memory event append"):
        store.events(own)
