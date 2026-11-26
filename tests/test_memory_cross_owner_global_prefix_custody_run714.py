"""Cross-owner Memory event custody is independent of a target CAS token.

Dense event IDs and a valid target-row lifetime do not attest to foreign-owner
event payloads. Use a separately retained global prefix before claiming wider
integrity. All SQLite mutations here are disposable corruption fixtures only.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixRejected,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)


def _fixture(tmp_path):
    path = tmp_path / "cross-owner-custody.sqlite"
    clock = [1000]
    store = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    target_scope = MemoryScope("owner-a", "private")
    foreign_scope = MemoryScope("owner-b", "private")
    original = store.put(MemoryWrite(target_scope, "same", "target"))
    foreign = store.put(MemoryWrite(foreign_scope, "same", "other"))
    target = observe_memory_generation_for_cas(store, target_scope, "same")
    retained_global = capture_local_memory_event_prefix(store)
    return (
        store, clock, target_scope, foreign_scope, original, foreign, target,
        retained_global,
    )


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("occurred_at_ms", 900),
        ("revision", 3),
        ("owner_id", "owner-c"),
    ),
)
def test_foreign_semantic_rewrite_with_dense_ids_fails_global_custody(
    tmp_path, column, value,
):
    (
        store, _, target_scope, _, original, foreign, target, retained,
    ) = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memory_events SET {column}=? WHERE memory_id=?",
            (value, foreign.memory_id),
        )
    with sqlite3.connect(store.path) as conn:
        count, low, high = conn.execute(
            "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM memory_events"
        ).fetchone()
        seq = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone()[0]
    assert (count, low, high, seq) == (2, 1, 2, 2)
    assert target.create_event_id == target.last_event_id == 1
    assert target.external_action_authorized is False
    assert store.get(
        original.memory_id, target_scope, include_expired=True,
    ).content == "target"
    with pytest.raises(MemoryEventPrefixRejected):
        compare_local_memory_event_prefix(store, retained)
    with pytest.raises(MemoryEventAlignmentRejected):
        review_memory_event_alignment(store)


def test_legitimate_foreign_append_advances_global_witness_without_target_retry(
    tmp_path,
):
    store, clock, target_scope, foreign_scope, original, _, target, retained = (
        _fixture(tmp_path)
    )
    clock[0] = 1100
    another = SQLiteMemoryStore(store.path, clock_ms=lambda: clock[0])
    another.put(MemoryWrite(foreign_scope, "new-source", "unrelated"))
    comparison = compare_local_memory_event_prefix(store, retained)
    assert comparison.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert comparison.previous_event_count == 2
    assert comparison.current_event_count == 3
    assert comparison.historical_writer_authenticated is False
    assert comparison.independent_witness_custody_proven is False
    assert comparison.action_authorized is False
    assert observe_memory_generation_for_cas(
        store, target_scope, "same",
    ) == target
    assert store.get(original.memory_id, target_scope).content == "target"
