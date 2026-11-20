"""Run1024: distinguish local logical expiry from explicit row purge.

Synthetic temporary SQLite only. The injected Memory clock is deliberately
non-monotonic and is not trusted time, retention authorization, or consent.
"""

from __future__ import annotations

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path):
    now = {"ms": 1_000}
    calls: list[int] = []

    def clock() -> int:
        calls.append(now["ms"])
        return now["ms"]

    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=clock)
    scope = MemoryScope("synthetic-owner", "private")
    record = store.put(
        MemoryWrite(scope, "source", "synthetic content", expires_at_ms=1_200),
    )
    return store, scope, record, now, calls


def _event_image(store, scope):
    return tuple(
        (event.event_id, event.operation, event.revision, event.occurred_at_ms)
        for event in store.events(scope)
    )


def test_logical_expiry_visibility_can_reappear_after_local_clock_rollback(
    tmp_path,
):
    store, scope, record, now, calls = _fixture(tmp_path)
    before = _event_image(store, scope)

    now["ms"] = 1_200
    assert store.get(record.memory_id, scope) is None
    after_expired_read = tuple(calls)
    assert store.get(record.memory_id, scope, include_expired=True) == record
    # include_expired is a diagnostic read and must not sample the local clock.
    assert tuple(calls) == after_expired_read

    now["ms"] = 1_199
    assert store.get(record.memory_id, scope) == record
    # A read-only expiry filter never appends a deletion/expiry event.
    assert _event_image(store, scope) == before


def test_explicit_expiry_purge_remains_deleted_after_clock_rollback(tmp_path):
    store, scope, record, now, _ = _fixture(tmp_path)

    now["ms"] = 1_200
    assert store.purge_expired(scope=scope, limit=1) == 1
    assert store.get(record.memory_id, scope, include_expired=True) is None

    now["ms"] = 1_199
    assert store.get(record.memory_id, scope, include_expired=True) is None
    assert _event_image(store, scope) == (
        (1, "create", 1, 1_000),
        (2, "expire", 1, 1_200),
    )
