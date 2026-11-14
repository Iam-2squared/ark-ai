"""Detached Memory generation tokens: unrelated owner churn vs global corruption.

Disposable local SQLite only. These are row-lifetime concurrency checks, not
consent, authenticated event custody, or an external exactly-once guarantee.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("churn", ("update", "delete-recreate"))
@pytest.mark.parametrize("other_scope", (
    MemoryScope("other-owner", "private"),
    MemoryScope("owner-a", "other-namespace"),
))
def test_unrelated_scope_churn_does_not_redeem_or_invalidate_own_generation(
    tmp_path: Path, churn: str, other_scope: MemoryScope,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    owner = MemoryScope("owner-a", "private")
    a = store.put(MemoryWrite(owner, "source-a", "initial"))
    b = store.put(MemoryWrite(other_scope, "source-b", "initial"))
    retained_a = observe_memory_generation_for_cas(store, owner, "source-a")
    if churn == "update":
        changed = store.put(
            MemoryWrite(other_scope, "source-b", "changed"),
            expected_revision=1,
        )
        assert changed.revision == 2
        expected_a_event = 4
    else:
        assert store.delete(b.memory_id, other_scope, expected_revision=1)
        changed = store.put(MemoryWrite(other_scope, "source-b", "reborn"))
        assert changed.revision == 1
        expected_a_event = 5
    assert changed.memory_id == b.memory_id
    assert store.get(a.memory_id, owner) == a

    updated_a = generation_fenced_memory_update(
        store, MemoryWrite(owner, "source-a", "after-other-churn"),
        retained=retained_a,
    )
    assert updated_a.revision == 2
    assert updated_a.content == "after-other-churn"
    assert [(x.event_id, x.operation) for x in store.events(owner)] == [
        (1, "create"), (expected_a_event, "update"),
    ]
    assert store.get(b.memory_id, other_scope) == changed
    new_a = observe_memory_generation_for_cas(store, owner, "source-a")
    assert new_a.create_event_id == retained_a.create_event_id
    assert new_a.last_event_id == expected_a_event
    assert new_a.event_prefix_sha256 != retained_a.event_prefix_sha256
    assert new_a.external_action_authorized is False
    assert new_a.consent_authenticated is False


@pytest.mark.parametrize("tamper", ("duplicate", "missing"))
def test_global_event_high_water_marker_corruption_refuses_cas_before_write(
    tmp_path: Path, tamper: str,
) -> None:
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-a", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    record = store.put(MemoryWrite(scope, "source-a", "unchanged"))
    retained = observe_memory_generation_for_cas(store, scope, "source-a")
    with sqlite3.connect(path) as conn:
        if tamper == "duplicate":
            conn.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES (?,?)",
                ("memory_events", 1),
            )
        else:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name=?", ("memory_events",),
            )
    with pytest.raises(MemoryGenerationCASRejected):
        generation_fenced_memory_update(
            store, MemoryWrite(scope, "source-a", "must-not-commit"),
            retained=retained,
        )
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT content, revision FROM memories WHERE memory_id=?",
            (record.memory_id,),
        ).fetchone()
        events = conn.execute(
            "SELECT event_id,operation FROM memory_events ORDER BY event_id",
        ).fetchall()
    assert row == ("unchanged", 1)
    assert events == [(1, "create")]
