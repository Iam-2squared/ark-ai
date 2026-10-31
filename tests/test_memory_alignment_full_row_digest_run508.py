"""Whole-row local Memory audit fingerprint regression.

Fingerprints are local consistency evidence, NOT signed/witnessed provenance.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize(
    ("sql", "params"),
    [
        ("UPDATE memories SET expires_at_ms=?", (9000,)),
        ("UPDATE memories SET metadata_json=?", ('{"review":"local"}',)),
        ("UPDATE memories SET created_at_ms=?, updated_at_ms=?", (4500, 4900)),
        ("UPDATE memories SET updated_at_ms=?", (6000,)),
    ],
)
def test_every_mutable_row_epoch_changes_local_alignment_digest(tmp_path, sql, params):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)
    store.put(MemoryWrite(MemoryScope("owner"), "source", "private local text"))
    before = review_memory_event_alignment(store)

    # Simulate on-disk local edits which leave the CREATE history intact.
    # Such edits need an independently retained prior digest to detect later.
    with sqlite3.connect(store.path) as conn:
        conn.execute(sql, params)

    after = review_memory_event_alignment(store)
    assert (before.row_count, before.event_count) == (1, 1)
    assert (after.row_count, after.event_count) == (1, 1)
    assert after.last_event_id == before.last_event_id
    assert after.digest != before.digest
    assert after.independently_authenticated is False
    assert after.user_consent_verified is False
    assert after.deletion_or_erasure_proven is False
    assert after.action_authorized is False


def test_snapshot_is_repeatable_and_does_not_reveal_content_or_metadata(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)
    store.put(MemoryWrite(
        MemoryScope("owner"), "source", "sensitive text",
        metadata={"secret": "do not return"},
        expires_at_ms=8000,
    ))
    first = review_memory_event_alignment(store)
    second = review_memory_event_alignment(store)
    assert first == second
    assert len(first.digest) == 64
    assert "sensitive" not in repr(first)
    assert "do not return" not in repr(first)
    assert first.action_authorized is False
