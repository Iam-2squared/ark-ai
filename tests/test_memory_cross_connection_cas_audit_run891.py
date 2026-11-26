"""Cross-connection Memory CAS with globally ordered audit events.

Synthetic SQLite stores only. An observed stale revision must neither mutate
the winning writer's data nor consume a committed event sequence number.
"""

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _stores(tmp_path, clock):
    path = tmp_path / "cas.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    second = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    return first, second, path


def test_stale_connection_cas_does_not_override_newer_commit_or_append_event(tmp_path):
    now = [100]
    first, second, path = _stores(tmp_path, now)
    scope = MemoryScope("synthetic-owner", "private")
    initial = first.put(MemoryWrite(scope, "item", "first"), expected_revision=0)
    winner = second.put(
        MemoryWrite(scope, "item", "second"), expected_revision=1,
    )
    assert (initial.revision, winner.revision) == (1, 2)
    with pytest.raises(MemoryConflictError):
        first.put(MemoryWrite(scope, "item", "stale"), expected_revision=1)
    assert first.get(initial.memory_id, scope).content == "second"
    assert [(e.event_id, e.revision) for e in first.events(scope)] == [
        (1, 1), (2, 2),
    ]
    now[0] = 110
    resumed = SQLiteMemoryStore(path, clock_ms=lambda: now[0])
    final = resumed.put(MemoryWrite(scope, "item", "third"), expected_revision=2)
    assert final.revision == 3
    assert [(e.event_id, e.operation) for e in resumed.events(scope)] == [
        (1, "create"), (2, "update"), (3, "update"),
    ]


def test_same_source_in_two_namespaces_has_independent_cas_and_global_event_ids(
    tmp_path,
):
    now = [100]
    first, second, _path = _stores(tmp_path, now)
    left = MemoryScope("synthetic-owner", "private")
    right = MemoryScope("synthetic-owner", "notes")
    a = first.put(MemoryWrite(left, "shared-source", "private"), expected_revision=0)
    b = second.put(MemoryWrite(right, "shared-source", "notes"), expected_revision=0)
    assert a.memory_id != b.memory_id
    with pytest.raises(MemoryConflictError):
        second.put(MemoryWrite(left, "shared-source", "invalid"), expected_revision=0)
    changed = first.put(
        MemoryWrite(right, "shared-source", "notes-new"), expected_revision=1,
    )
    assert changed.revision == 2
    assert [(e.event_id, e.operation) for e in first.events(left)] == [
        (1, "create"),
    ]
    assert [(e.event_id, e.operation) for e in second.events(right)] == [
        (2, "create"), (3, "update"),
    ]
    assert first.get(a.memory_id, right) is None


def test_expiry_purge_is_global_event_append_not_a_scope_cas_reset(tmp_path):
    now = [100]
    first, second, path = _stores(tmp_path, now)
    private = MemoryScope("synthetic-owner", "private")
    notes = MemoryScope("synthetic-owner", "notes")
    old = first.put(
        MemoryWrite(private, "same", "expires", expires_at_ms=150),
    )
    keep = second.put(MemoryWrite(notes, "same", "retained"))
    now[0] = 200
    assert second.purge_expired(scope=private, limit=1) == 1
    assert first.get(old.memory_id, private, include_expired=True) is None
    assert first.get(keep.memory_id, notes).revision == 1
    with pytest.raises(MemoryConflictError):
        first.put(MemoryWrite(notes, "same", "stale"), expected_revision=0)
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: now[0])
    assert [(e.event_id, e.operation) for e in reopened.events(private)] == [
        (1, "create"), (3, "expire"),
    ]
    assert [(e.event_id, e.operation) for e in reopened.events(notes)] == [
        (2, "create"),
    ]
