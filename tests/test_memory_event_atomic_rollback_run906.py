"""Run906: SQLite Memory mutations and matching events roll back together.

Synthetic local failure injection only. This is not a real crash, external
backup deletion, trusted clock, independent provenance or replay authority.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryQuery, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("operation", ("create", "update", "delete", "expire"))
def test_injected_post_event_error_rolls_back_record_and_event(
    tmp_path, monkeypatch, operation,
):
    path = tmp_path / "atomic.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    initial = writer.put(
        MemoryWrite(
            scope, "original", "old",
            expires_at_ms=150 if operation == "expire" else None,
        ),
    )
    before = writer.events(scope)
    real_event = SQLiteMemoryStore._event
    observed = []

    def interrupted(conn, memory_id, event_scope, kind, revision, timestamp):
        real_event(conn, memory_id, event_scope, kind, revision, timestamp)
        observed.append(kind)
        raise RuntimeError("synthetic pre-COMMIT interruption")

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_event", staticmethod(interrupted))
        with pytest.raises(RuntimeError, match="pre-COMMIT"):
            if operation == "create":
                writer.put(MemoryWrite(scope, "second", "new"))
            elif operation == "update":
                writer.put(
                    MemoryWrite(scope, "original", "new"),
                    expected_revision=initial.revision,
                )
            elif operation == "delete":
                writer.delete(
                    initial.memory_id, scope, expected_revision=initial.revision,
                )
            else:
                later = SQLiteMemoryStore(path, clock_ms=lambda: 200)
                later.purge_expired(scope=scope, limit=1)
    assert observed == [operation]
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert cold.events(scope) == before
    current = cold.get(initial.memory_id, scope, include_expired=True)
    assert current is not None
    assert current.revision == initial.revision
    assert current.content == "old"
    if operation == "create":
        assert [record.source_id for record in cold.search(
            MemoryQuery(
                scope, include_expired=True,
            ),
        )] == ["original"]


def test_cross_scope_expiry_batch_rolls_back_all_prior_deletions(
    tmp_path, monkeypatch,
):
    path = tmp_path / "multi-scope.sqlite"
    a = MemoryScope("synthetic-owner", "a")
    b = MemoryScope("synthetic-owner", "b")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 10)
    left = initial.put(MemoryWrite(a, "left", "keep", expires_at_ms=20))
    right = initial.put(MemoryWrite(b, "right", "keep", expires_at_ms=20))
    baseline = (initial.events(a), initial.events(b))
    real_event = SQLiteMemoryStore._event
    seen = []

    def interrupted(conn, memory_id, scope, kind, revision, timestamp):
        real_event(conn, memory_id, scope, kind, revision, timestamp)
        seen.append(kind)
        if len(seen) == 2:
            raise RuntimeError("synthetic second event interruption")

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_event", staticmethod(interrupted))
        with pytest.raises(RuntimeError, match="second event"):
            SQLiteMemoryStore(path, clock_ms=lambda: 30).purge_expired()
    assert seen == ["expire", "expire"]
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 30)
    assert cold.events(a) == baseline[0]
    assert cold.events(b) == baseline[1]
    assert cold.get(left.memory_id, a, include_expired=True) is not None
    assert cold.get(right.memory_id, b, include_expired=True) is not None
