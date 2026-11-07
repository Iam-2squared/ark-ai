"""Disjoint SQLite Memory lifetime churn does not steal another row's CAS.

All records are disposable local fixtures. A retained row token witnesses only
a local lifetime, not user consent, authenticated actors, or an external retry.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize(
    "other_identity",
    ("owner", "namespace", "source"),
)
def test_unrelated_delete_recreate_does_not_invalidate_target_lifetime(
    tmp_path, other_identity,
):
    path = tmp_path / "disjoint-lifetime.sqlite"
    target_scope = MemoryScope("target-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    target = first.put(MemoryWrite(target_scope, "target-source", "old"))
    token = observe_memory_generation_for_cas(first, target_scope, "target-source")

    if other_identity == "owner":
        other_scope = MemoryScope("other-owner", "private")
        other_source = "target-source"
    elif other_identity == "namespace":
        other_scope = MemoryScope("target-owner", "other-private")
        other_source = "target-source"
    else:
        other_scope = target_scope
        other_source = "other-source"

    second = SQLiteMemoryStore(path, clock_ms=lambda: 1100)
    side = second.put(MemoryWrite(other_scope, other_source, "old-side"))
    third = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    assert third.delete(side.memory_id, other_scope, expected_revision=1)
    fourth = SQLiteMemoryStore(path, clock_ms=lambda: 1300)
    recreated = fourth.put(MemoryWrite(other_scope, other_source, "fresh-side"))
    assert recreated.memory_id == side.memory_id
    assert recreated.revision == 1
    assert recreated.content != side.content
    assert observe_memory_generation_for_cas(
        fourth, target_scope, "target-source",
    ) == token

    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1400)
    changed = generation_fenced_memory_update(
        writer, MemoryWrite(target_scope, "target-source", "new"),
        retained=token,
    )
    assert changed.memory_id == target.memory_id
    assert changed.revision == 2
    assert writer.get(recreated.memory_id, other_scope) == recreated
    events = writer.events(target_scope)
    assert [event.operation for event in events if event.memory_id == target.memory_id] == [
        "create", "update",
    ]
    aligned = review_memory_event_alignment(writer)
    assert (aligned.row_count, aligned.event_count, aligned.last_event_id) == (2, 5, 5)
    assert aligned.action_authorized is False
