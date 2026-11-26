"""Whole-store Memory row/event audit uses one committed SQLite WAL snapshot.

The second local connection writes after the reader has fetched its first
row but before the audit reads global events. A mixed-generation report
would be unsafe; neither report authenticates the writer or proves erasure.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_event_alignment as alignment
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("mutation", ("create_other_scope", "update", "delete_recreate"))
def test_readonly_event_alignment_excludes_midscan_committed_mutation(
    tmp_path, monkeypatch, mutation,
):
    path = tmp_path / "interleaved-audit.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    original = reader.put(MemoryWrite(scope, "alpha", "first"))
    before = alignment.review_memory_event_alignment(reader)
    assert (before.row_count, before.event_count, before.last_event_id) == (1, 1, 1)
    calls = 0
    native_decode = alignment._record

    def decode_and_commit(row):
        nonlocal calls
        record = native_decode(row)
        calls += 1
        if calls == 1:
            if mutation == "create_other_scope":
                writer.put(MemoryWrite(
                    MemoryScope("other-owner", "private"), "beta", "second",
                ))
            elif mutation == "update":
                writer.put(
                    MemoryWrite(scope, "alpha", "updated"),
                    expected_revision=original.revision,
                )
            else:
                assert writer.delete(
                    original.memory_id, scope, expected_revision=original.revision,
                )
                recreated = writer.put(MemoryWrite(scope, "alpha", "recreated"))
                assert recreated.revision == 1
        return record

    monkeypatch.setattr(alignment, "_record", decode_and_commit)
    during = alignment.review_memory_event_alignment(reader)
    assert calls == 1
    # The audit began before the independent WAL commit; event and row scans
    # must belong to that same snapshot, not a new live global event tail.
    assert during == before
    assert during.action_authorized is False
    assert during.deletion_or_erasure_proven is False

    later = alignment.review_memory_event_alignment(reader)
    assert later.digest != before.digest
    if mutation == "create_other_scope":
        assert (later.row_count, later.event_count, later.last_event_id) == (2, 2, 2)
    elif mutation == "update":
        assert (later.row_count, later.event_count, later.last_event_id) == (1, 2, 2)
    else:
        assert (later.row_count, later.event_count, later.last_event_id) == (1, 3, 3)
    assert later.independently_authenticated is False
