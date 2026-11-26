"""Independent Memory CAS rows share a global, gap-free v1 event timeline.

All cases use disposable local SQLite. Per-row tokens are neither consent nor
a writer identity; adjacent row changes should not stale unrelated CAS tokens,
but deletion of ANY v1 event must fail closed before interpreting a row.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("other_namespace", ("private", "other"))
def test_foreign_row_update_preserves_independent_cas_epoch(tmp_path, other_namespace):
    path = tmp_path / "independent.sqlite"
    clock = [100]
    store = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    target_scope = MemoryScope("alice", "private")
    foreign_scope = MemoryScope("bob", other_namespace)
    store.put(MemoryWrite(target_scope, "same-source", "a-before"))
    store.put(MemoryWrite(foreign_scope, "same-source", "b-before"))
    retained_target = observe_memory_generation_for_cas(
        store, target_scope, "same-source",
    )
    retained_foreign = observe_memory_generation_for_cas(
        store, foreign_scope, "same-source",
    )

    clock[0] = 200
    foreign = generation_fenced_memory_update(
        SQLiteMemoryStore(path, clock_ms=lambda: clock[0]),
        MemoryWrite(foreign_scope, "same-source", "b-updated"),
        retained=retained_foreign,
    )
    assert foreign.revision == 2
    assert observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: clock[0]),
        target_scope, "same-source",
    ) == retained_target

    clock[0] = 300
    target = generation_fenced_memory_update(
        store,
        MemoryWrite(target_scope, "same-source", "a-updated"),
        retained=retained_target,
    )
    assert target.revision == 2
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    assert restarted.get(target.memory_id, target_scope).content == "a-updated"
    assert restarted.get(foreign.memory_id, foreign_scope).content == "b-updated"
    assert len(restarted.events(target_scope)) == 2
    assert len(restarted.events(foreign_scope)) == 2
    assert retained_target.external_action_authorized is False
    assert retained_foreign.consent_authenticated is False


@pytest.mark.parametrize("lost_event", (1, 2, 3))
def test_foreign_event_gap_invalidates_target_observation(tmp_path, lost_event):
    path = tmp_path / "event-gap.sqlite"
    def clock():
        return 100
    store = SQLiteMemoryStore(path, clock_ms=clock)
    target_scope = MemoryScope("alice", "private")
    foreign_scope = MemoryScope("bob", "other")
    store.put(MemoryWrite(foreign_scope, "first", "foreign-1"))
    target = store.put(MemoryWrite(target_scope, "target", "target-1"))
    store.put(MemoryWrite(foreign_scope, "third", "foreign-2"))
    retained = observe_memory_generation_for_cas(store, target_scope, "target")
    assert retained.revision == 1

    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "DELETE FROM memory_events WHERE event_id=?", (lost_event,),
        )
        connection.commit()

    # The target row and its event can remain unchanged (events 1 and 3
    # belong to another row), but a missing global event still fails closed.
    with pytest.raises(
        MemoryGenerationCASRejected, match="global event high-water mismatch",
    ):
        observe_memory_generation_for_cas(
            SQLiteMemoryStore(path, clock_ms=clock), target_scope, "target",
        )
    with pytest.raises(
        MemoryGenerationCASRejected, match="global event high-water mismatch",
    ):
        generation_fenced_memory_update(
            store, MemoryWrite(target_scope, "target", "must-not-update"),
            retained=retained,
        )
    assert store.get(target.memory_id, target_scope).content == "target-1"
    assert retained.external_action_authorized is False
