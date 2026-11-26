"""Offline Memory CAS, expiry and coherent read witnesses after restart.

Only synthetic in-process text, temporary SQLite, and a supplied fake clock.
No memory sharing, external tool, user consent or live account connector.
"""

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)


def _store(tmp_path, now):
    return SQLiteMemoryStore(
        tmp_path / "memory.sqlite", clock_ms=lambda: now[0],
    )


def test_expired_record_remains_cas_fenced_until_explicit_revision_refresh(tmp_path):
    now = [100]
    store = _store(tmp_path, now)
    scope = MemoryScope("synthetic-owner", "private")
    first = store.put(
        MemoryWrite(scope, "source-one", "old synthetic", expires_at_ms=150),
        expected_revision=0,
    )
    assert first.revision == 1
    now[0] = 200
    assert store.get(first.memory_id, scope) is None
    expired = store.get(first.memory_id, scope, include_expired=True)
    assert expired is not None and expired.revision == 1
    with pytest.raises(MemoryConflictError):
        store.put(
            MemoryWrite(scope, "source-one", "stale attempt"),
            expected_revision=0,
        )
    refreshed = store.put(
        MemoryWrite(scope, "source-one", "new synthetic", expires_at_ms=None),
        expected_revision=1,
    )
    assert refreshed.revision == 2
    assert store.get(first.memory_id, scope).content == "new synthetic"
    assert [event.operation for event in store.events(scope)] == ["create", "update"]


def test_restart_read_projects_one_clock_and_excludes_expired_namespace(tmp_path):
    now = [100]
    store = _store(tmp_path, now)
    one = MemoryScope("synthetic-owner", "private")
    two = MemoryScope("synthetic-owner", "notes")
    store.put(MemoryWrite(one, "one", "still available", expires_at_ms=300))
    store.put(MemoryWrite(two, "two", "expired fixture", expires_at_ms=150))
    now[0] = 200
    restarted = _store(tmp_path, now)
    default = review_coherent_snapshot(
        restarted, CoherentSnapshotRequest(
            "synthetic-owner", ("private", "notes"),
        ),
    )
    assert default.read_at_ms == 200
    assert len(default.records[0]) == 1
    assert default.records[0][0].content == "still available"
    assert default.records[1] == ()
    assert len(default.provenance_sha256) == 64
    historical = review_coherent_snapshot(
        restarted, CoherentSnapshotRequest(
            "synthetic-owner", ("private", "notes"),
            include_expired=True,
        ),
    )
    assert len(historical.records[0]) == 1
    assert len(historical.records[1]) == 1
    assert historical.records[1][0].content == "expired fixture"
    assert historical.provenance_sha256 != default.provenance_sha256


def test_expiry_purge_keeps_audit_and_survivor_separate(tmp_path):
    now = [100]
    store = _store(tmp_path, now)
    scope = MemoryScope("synthetic-owner", "private")
    expired = store.put(MemoryWrite(
        scope, "expired", "retained for audit", expires_at_ms=150,
    ))
    survivor = store.put(MemoryWrite(
        scope, "survivor", "still live", expires_at_ms=300,
    ))
    now[0] = 200
    assert store.purge_expired(scope=scope, limit=1) == 1
    assert store.get(expired.memory_id, scope, include_expired=True) is None
    assert store.get(survivor.memory_id, scope) is not None
    assert store.purge_expired(scope=scope, limit=1) == 0
    events = store.events(scope)
    assert len(events) == 3
    assert events[-1].memory_id == expired.memory_id
    assert events[-1].operation == "expire"
