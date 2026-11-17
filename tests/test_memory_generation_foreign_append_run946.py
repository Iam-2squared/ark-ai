"""Run946: foreign event appends cannot consume a generation-CAS row token.

The SQLite fixture is synthetic, scoped and local. Event continuity proves
neither authenticated custody nor consent for any external operation.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("foreign_change", (
    "new_other_owner",
    "new_other_namespace",
    "new_same_namespace_source",
    "update_other_owner",
    "delete_other_owner",
))
def test_foreign_committed_append_does_not_consume_retained_row_token(
    tmp_path, foreign_change: str,
) -> None:
    path = tmp_path / "scoped-generation-cas.sqlite3"
    owner = MemoryScope("synthetic-owner", "private")
    foreign = (
        owner if foreign_change == "new_same_namespace_source"
        else MemoryScope("synthetic-owner", "other")
        if foreign_change == "new_other_namespace"
        else MemoryScope("different-owner", "private")
    )
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    primary = initial.put(MemoryWrite(owner, "primary", "private-original"))
    other = None
    if foreign_change.startswith(("update_", "delete_")):
        other = initial.put(MemoryWrite(foreign, "foreign", "foreign-original"))
    token = observe_memory_generation_for_cas(initial, owner, "primary")
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False

    # Restarted handle writes an unrelated event AFTER observation.
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    if foreign_change.startswith("new_"):
        restarted.put(MemoryWrite(foreign, "foreign", "foreign-created"))
    elif foreign_change == "update_other_owner":
        assert other is not None
        assert restarted.put(
            MemoryWrite(foreign, "foreign", "foreign-updated"),
            expected_revision=1,
        ).revision == 2
    else:
        assert other is not None
        assert restarted.delete(other.memory_id, foreign, expected_revision=1)

    # Global append continuity is intact; only the primary row generation
    # is fenced by the retained token, not other rows or owner namespaces.
    updated = generation_fenced_memory_update(
        SQLiteMemoryStore(path, clock_ms=lambda: 3000),
        MemoryWrite(owner, "primary", "private-updated"),
        retained=token,
    )
    assert updated.memory_id == primary.memory_id
    assert updated.revision == 2
    assert updated.content == "private-updated"
    fresh = observe_memory_generation_for_cas(initial, owner, "primary")
    assert fresh.create_event_id == token.create_event_id
    assert fresh.last_event_id > token.last_event_id
    assert fresh.row_sha256 != token.row_sha256
    assert fresh.event_prefix_sha256 != token.event_prefix_sha256

    with sqlite3.connect(path) as conn:
        events = conn.execute(
            "SELECT event_id,memory_id,operation FROM memory_events ORDER BY event_id"
        ).fetchall()
        assert [number for number, _, _ in events] == list(
            range(1, len(events) + 1)
        )
        assert [
            operation for _, memory_id, operation in events
            if memory_id == primary.memory_id
        ] == ["create", "update"]
