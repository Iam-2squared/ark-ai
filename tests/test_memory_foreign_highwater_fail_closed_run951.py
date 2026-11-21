"""Run951: foreign-scope event corruption cannot admit an opt-in Memory CAS.

These checks operate only on disposable synthetic SQLite fixtures. A local
event sequence or retained CAS token is not authenticated provenance, trusted
time, human consent, or authorization for an external action.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("tamper", (
    "foreign-event-gap",
    "duplicate-sequence-marker",
    "sequence-rewind",
    "sequence-future",
))
def test_foreign_scope_highwater_corruption_rejects_owner_cas_without_write(
    tmp_path, tamper: str,
) -> None:
    path = tmp_path / "synthetic-foreign-highwater.sqlite3"
    owner = MemoryScope("synthetic-owner", "private")
    foreign = MemoryScope("synthetic-foreign", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    primary = store.put(MemoryWrite(owner, "primary", "original"))
    store.put(MemoryWrite(foreign, "foreign", "unrelated"))
    store.put(MemoryWrite(owner, "second", "another"))
    retained = observe_memory_generation_for_cas(store, owner, "primary")
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT event_id FROM memory_events ORDER BY event_id"
        ).fetchall() == [(1,), (2,), (3,)]
        if tamper == "foreign-event-gap":
            conn.execute("DELETE FROM memory_events WHERE event_id=2")
        elif tamper == "duplicate-sequence-marker":
            conn.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES (?,?)",
                ("memory_events", 3),
            )
        elif tamper == "sequence-rewind":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=2 WHERE name='memory_events'"
            )
        else:
            conn.execute(
                "UPDATE sqlite_sequence SET seq=4 WHERE name='memory_events'"
            )
        prior_count = conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone()[0]

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    with pytest.raises(MemorySchemaError):
        observe_memory_generation_for_cas(cold, owner, "primary")
    with pytest.raises(MemorySchemaError):
        generation_fenced_memory_update(
            cold,
            MemoryWrite(owner, "primary", "forbidden"),
            retained=retained,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone()[0] == prior_count
        assert conn.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (primary.memory_id,),
        ).fetchone() == ("original", 1)
