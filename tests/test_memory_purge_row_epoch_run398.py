"""Multi-row Memory expiry must reject transient caller/source epochs.

These are local SQLite and reflection fault-injection fixtures, not historic
writer attestation or permission to erase a user's real personal information.
"""

from pathlib import Path

import pytest

import ark.memory.sqlite_store as memory_sqlite
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _two_expired_memories(tmp_path):
    clock = [100]
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: clock[0])
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    records = tuple(
        store.put(MemoryWrite(scope, f"fixture-source-{index}", "fixture text", {}, 150))
        for index in range(2)
    )
    clock[0] = 200
    return store, scope, records


def _reflect_drift(store, scope, drift):
    if drift == "path":
        original = store.path
        # The equal-text Path is a different carrier; it is not custody of
        # the same open SQLite file across the transaction.
        store.path = Path(str(original))

        def restore():
            store.path = original

    else:
        original = getattr(scope, drift)
        object.__setattr__(scope, drift, "different-fixture-scope")

        def restore():
            object.__setattr__(scope, drift, original)

    return restore


@pytest.mark.parametrize(
    ("drift", "scoped"),
    (
        ("owner_id", True),
        ("namespace", True),
        ("path", True),
        ("path", False),
    ),
)
def test_purge_refuses_drift_after_first_expiry_event_and_rolls_back(
    tmp_path, monkeypatch, drift, scoped,
):
    store, scope, records = _two_expired_memories(tmp_path)
    real_event = memory_sqlite.SQLiteMemoryStore._event
    calls = 0
    restore = lambda: None

    def event_with_reflection(conn, memory_id, event_scope, operation, revision, now):
        nonlocal calls, restore
        real_event(conn, memory_id, event_scope, operation, revision, now)
        calls += 1
        if calls == 1:
            restore = _reflect_drift(store, scope, drift)
        elif calls == 2:
            # A final-only check would miss that the first write happened
            # against an inconsistent scope or source epoch.
            restore()

    monkeypatch.setattr(
        memory_sqlite.SQLiteMemoryStore, "_event", staticmethod(event_with_reflection),
    )
    with pytest.raises(MemorySchemaError, match="memory purge .* changed before commit"):
        store.purge_expired(scope=scope if scoped else None)
    restore()

    # No partial delete AND no partial expire event can escape the transaction.
    assert calls == 1
    for record in records:
        assert store.get(record.memory_id, scope, include_expired=True) is not None
    assert [event.operation for event in store.events(scope)] == ["create", "create"]


@pytest.mark.parametrize("drift", ("owner_id", "namespace", "path"))
def test_purge_refuses_drift_during_first_row_hydration_without_any_delete(
    tmp_path, monkeypatch, drift,
):
    store, scope, records = _two_expired_memories(tmp_path)
    real_record = memory_sqlite._record
    calls = 0
    restore = lambda: None

    def hydrated_with_reflection(row):
        nonlocal calls, restore
        result = real_record(row)
        calls += 1
        if calls == 1:
            restore = _reflect_drift(store, scope, drift)
        return result

    monkeypatch.setattr(memory_sqlite, "_record", hydrated_with_reflection)
    with pytest.raises(MemorySchemaError, match="memory purge .* changed before commit"):
        store.purge_expired(scope=scope)
    restore()
    monkeypatch.setattr(memory_sqlite, "_record", real_record)
    assert calls == 1
    for record in records:
        assert store.get(record.memory_id, scope, include_expired=True) is not None
    assert [event.operation for event in store.events(scope)] == ["create", "create"]
