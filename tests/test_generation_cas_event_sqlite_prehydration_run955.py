"""Run955: optional generation CAS rejects corrupt event cells before hydration.

Only disposable local SQLite fixtures are modified. A generation token never
attests consent, historical custody, trusted time or a real tool action.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("column", "corruption"),
    (
        ("owner_id", "o" * 1025),
        ("namespace", "n" * 1025),
        ("owner_id", sqlite3.Binary(b"x" * 1200)),
        ("occurred_at_ms", sqlite3.Binary(b"100")),
    ),
)
def test_generation_cas_rejects_malformed_event_before_read_or_write(
    tmp_path, column: str, corruption: object,
) -> None:
    path = tmp_path / "disconnected-generation-event.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = store.put(MemoryWrite(scope, "source", "private-fixture"))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False

    # Only the synthetic row's metadata is damaged. The SQLite v1 DDL
    # remains untouched, and the optional writer may neither repair nor
    # silently skip the malformed append-log event.
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memory_events SET {column}=? WHERE memory_id=?",
            (corruption, row.memory_id),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    with pytest.raises(MemoryGenerationCASRejected, match="event hydration denied"):
        observe_memory_generation_for_cas(reopened, scope, "source")
    with pytest.raises(MemoryGenerationCASRejected, match="event hydration denied"):
        generation_fenced_memory_update(
            reopened, MemoryWrite(scope, "source", "must-not-commit"),
            retained=retained,
        )

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (row.memory_id,),
        ).fetchone() == ("private-fixture", 1)
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (1,)
