"""A target generation CAS survives unrelated fully committed Memory writes.

Local SQLite events across owners/namespaces share one global sequence. A
foreign append must preserve continuity without falsely invalidating a token
for an unchanged target lifetime. A valid token is neither writer attribution
nor consent, and these tests do not dispatch any external action.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    "foreign_change",
    (
        "new_other_owner",
        "update_other_owner",
        "delete_recreate_other_owner",
        "update_other_source_same_scope",
    ),
)
def test_foreign_events_do_not_spuriously_stale_target_cas(
    tmp_path, foreign_change,
):
    path = tmp_path / "independent-cas.sqlite"
    target_scope = MemoryScope("owner-a", "private")
    foreign_scope = (
        target_scope if foreign_change == "update_other_source_same_scope"
        else MemoryScope("owner-b", "private")
    )
    target = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    other = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    initial = target.put(
        MemoryWrite(target_scope, "target", "first", expires_at_ms=5000)
    )
    token = observe_memory_generation_for_cas(target, target_scope, "target")
    if foreign_change != "new_other_owner":
        foreign = other.put(MemoryWrite(foreign_scope, "foreign", "old"))
        if foreign_change == "delete_recreate_other_owner":
            assert other.delete(
                foreign.memory_id, foreign_scope, expected_revision=1,
            )
            other.put(
                MemoryWrite(foreign_scope, "foreign", "recreated"),
                expected_revision=0,
            )
        else:
            other.put(
                MemoryWrite(foreign_scope, "foreign", "changed"),
                expected_revision=1,
            )
    else:
        other.put(MemoryWrite(foreign_scope, "foreign", "created"))

    foreign_before = other.events(foreign_scope)
    target_before = target.events(target_scope)
    assert target.get(initial.memory_id, target_scope).revision == 1

    updated = generation_fenced_memory_update(
        target,
        MemoryWrite(
            target_scope, "target", "second", expires_at_ms=4000,
        ),
        retained=token,
    )
    assert updated.memory_id == initial.memory_id
    assert updated.revision == 2
    assert updated.content == "second"
    assert updated.expires_at_ms == 4000
    assert other.get(initial.memory_id, target_scope) == updated
    foreign_scope_events = other.events(foreign_scope)
    if foreign_scope == target_scope:
        assert foreign_scope_events[:-1] == foreign_before
        assert foreign_scope_events[-1].memory_id == initial.memory_id
    else:
        assert foreign_scope_events == foreign_before
    assert len(target.events(target_scope)) == len(target_before) + 1
    fresh = observe_memory_generation_for_cas(other, target_scope, "target")
    assert fresh.create_event_id == token.create_event_id
    assert fresh.last_event_id > token.last_event_id
    assert fresh.event_prefix_sha256 != token.event_prefix_sha256
    assert fresh.external_action_authorized is False
    assert fresh.consent_authenticated is False
