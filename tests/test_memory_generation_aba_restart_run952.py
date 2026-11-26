"""Run952: delete/re-create ABA must not revive a Memory generation-CAS token.

All rows live in disposable local SQLite fixtures. This test grants neither
consent nor real-world execution, and does not alter frozen Memory v1 APIs.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("restored_content", "append_foreign"),
    (
        ("identical", False),
        ("replacement", False),
        ("identical", True),
        ("replacement", True),
    ),
)
def test_delete_recreate_aba_never_reuses_prior_generation(
    tmp_path, restored_content: str, append_foreign: bool,
) -> None:
    path = tmp_path / "synthetic-aba.sqlite3"
    clock = {"now": 100}
    scope = MemoryScope("owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: clock["now"])
    old_row = store.put(MemoryWrite(scope, "source", "identical"))
    old_token = observe_memory_generation_for_cas(store, scope, "source")
    assert old_token.create_event_id == 1
    assert old_token.revision == 1
    assert old_token.external_action_authorized is False

    clock["now"] = 110
    assert store.delete(old_row.memory_id, scope, expected_revision=1)
    clock["now"] = 120
    new_row = store.put(MemoryWrite(scope, "source", restored_content))
    assert new_row.memory_id == old_row.memory_id
    assert new_row.revision == 1
    clock["now"] = 130
    if append_foreign:
        store.put(MemoryWrite(MemoryScope("other", "private"), "other", "safe"))

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: clock["now"])
    fresh = observe_memory_generation_for_cas(reopened, scope, "source")
    assert fresh.create_event_id != old_token.create_event_id
    assert fresh.last_event_id != old_token.last_event_id
    assert fresh.external_action_authorized is False
    assert fresh.consent_authenticated is False

    with sqlite3.connect(path) as conn:
        prior_events = conn.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall()
    assert [row[1] for row in prior_events[:3]] == [
        "create", "delete", "create",
    ]

    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            reopened, MemoryWrite(scope, "source", "must-not-write"),
            retained=old_token,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall() == prior_events
        assert conn.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (old_row.memory_id,),
        ).fetchone() == (restored_content, 1)

    # A new, explicitly observed lifetime can advance only the local Memory
    # row; it still carries no approval, dispatch or external action authority.
    clock["now"] = 140
    updated = generation_fenced_memory_update(
        reopened, MemoryWrite(scope, "source", "confirmed-local-update"),
        retained=fresh,
    )
    assert updated.revision == 2
    assert updated.content == "confirmed-local-update"
