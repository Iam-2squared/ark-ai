"""A retained Memory generation cannot survive another connection's writes.

The opt-in generation fence is a local CAS/replay guard, not evidence of
author consent, an authenticated clock, or authority to reuse a stale write.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    "intervention",
    (
        "refresh_expiry",
        "delete_recreate",
        "expire_recreate",
        "expire_without_recreate",
    ),
)
def test_second_connection_invalidates_retained_generation_without_implicit_retry(
    tmp_path, intervention,
):
    path = tmp_path / "stale-generation.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    caller = SQLiteMemoryStore(path, clock_ms=lambda: 1300)
    first = observer.put(
        MemoryWrite(scope, "source", "original", expires_at_ms=1100),
    )
    retained = observe_memory_generation_for_cas(observer, scope, "source")
    assert retained.create_event_id == 1
    assert retained.revision == 1
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False

    if intervention == "refresh_expiry":
        writer.put(
            MemoryWrite(scope, "source", "refreshed", expires_at_ms=5000),
            expected_revision=1,
        )
    elif intervention == "delete_recreate":
        assert writer.delete(first.memory_id, scope, expected_revision=1)
        writer.put(MemoryWrite(scope, "source", "recreated", expires_at_ms=5000))
    else:
        assert writer.purge_expired(scope=scope) == 1
        if intervention == "expire_recreate":
            writer.put(MemoryWrite(scope, "source", "recreated", expires_at_ms=5000))

    before_events = tuple(writer.events(scope))
    before_row = writer.get(first.memory_id, scope, include_expired=True)
    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            caller,
            MemoryWrite(scope, "source", "stale replacement", expires_at_ms=4000),
            retained=retained,
        )
    assert tuple(writer.events(scope)) == before_events
    assert writer.get(first.memory_id, scope, include_expired=True) == before_row
    assert len(writer.events(scope)) == (
        2 if intervention in ("refresh_expiry", "expire_without_recreate") else 3
    )
    if before_row is not None:
        current = observe_memory_generation_for_cas(writer, scope, "source")
        assert current.last_event_id != retained.last_event_id
        assert current.event_prefix_sha256 != retained.event_prefix_sha256
        if intervention != "refresh_expiry":
            assert current.create_event_id != retained.create_event_id
        assert current.external_action_authorized is False
        assert current.consent_authenticated is False
