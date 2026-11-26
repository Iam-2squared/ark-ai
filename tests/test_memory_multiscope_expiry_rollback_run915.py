"""Multi-row Memory expiry rollback is atomic across scopes and read handles.

Local synthetic SQLite only. No real user data, scheduler permission, trusted
clock, backup erasure, physical device or external action is involved.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("scoped", (False, True))
def test_multirow_expiry_failure_rolls_back_every_row_and_event(
    tmp_path, monkeypatch, scoped,
):
    path = tmp_path / "multirow-expiry.sqlite"
    owner = MemoryScope("synthetic-owner-a", "private")
    other = owner if scoped else MemoryScope("synthetic-owner-b", "private")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    first = writer.put(
        MemoryWrite(owner, "first", "one", expires_at_ms=900)
    )
    second = writer.put(
        MemoryWrite(other, "second", "two", expires_at_ms=900)
    )
    future = writer.put(
        MemoryWrite(owner, "future", "preserved", expires_at_ms=2_000)
    )
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    before_owner = tuple(observer.events(owner))
    before_other = tuple(observer.events(other))
    original = SQLiteMemoryStore._event
    attempted = []

    def lose_second_event(conn, memory_id, event_scope, operation, revision, at_ms):
        if operation == "expire":
            attempted.append(memory_id)
            if len(attempted) == 2:
                raise RuntimeError("synthetic second-event failure")
        return original(conn, memory_id, event_scope, operation, revision, at_ms)

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_event", staticmethod(lose_second_event))
        with pytest.raises(RuntimeError, match="second-event failure"):
            writer.purge_expired(scope=owner if scoped else None, limit=2)

    assert len(attempted) == 2
    assert len(set(attempted)) == 2
    assert tuple(observer.events(owner)) == before_owner
    assert tuple(observer.events(other)) == before_other
    for record, record_scope in ((first, owner), (second, other), (future, owner)):
        restored = observer.get(
            record.memory_id, record_scope, include_expired=True,
        )
        assert restored is not None
        assert restored.content == record.content
        assert restored.revision == record.revision

    # Only after the fault hook is removed can a fresh local expiry
    # transaction commit. The failed attempt left no event-ID gap.
    assert observer.purge_expired(scope=owner if scoped else None, limit=2) == 2
    owner_events = tuple(observer.events(owner))
    other_events = tuple(observer.events(other))
    if scoped:
        assert sum(event.operation == "expire" for event in owner_events) == 2
    else:
        assert sum(event.operation == "expire" for event in owner_events) == 1
        assert sum(event.operation == "expire" for event in other_events) == 1
    assert observer.get(future.memory_id, owner, include_expired=True) is not None
