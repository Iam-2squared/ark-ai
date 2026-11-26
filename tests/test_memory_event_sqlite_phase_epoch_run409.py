"""Ordinary Memory event queries pin their source at every SQLite read phase.

These are disposable local Memory v1 records, not private export or external
processing. A failed review never silently recreates or mutates its store.
"""

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import MemorySchemaError, SQLiteMemoryStore


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory events # %.sqlite", clock_ms=lambda: 10)
    scope = MemoryScope("offline-owner", "private-fixture")
    store.put(MemoryWrite(scope, "one", "first local sample"))
    store.put(MemoryWrite(scope, "two", "second local sample"))
    return store, scope


@pytest.mark.parametrize("boundary", ("connect", "begin", "select", "fetchall"))
@pytest.mark.parametrize("target", ("source", "scope"))
def test_memory_events_reject_source_retarget_before_later_callback_restores(
    tmp_path: Path, monkeypatch, boundary: str, target: str,
):
    store, scope = _fixture(tmp_path)
    original_connect = store._connect_readonly
    original_path = store.path
    original_namespace = scope.namespace
    calls = []

    def mutate():
        if target == "source":
            store.path = Path(str(original_path))
            assert store.path == original_path and store.path is not original_path
        else:
            object.__setattr__(scope, "namespace", "temporary-other")
        calls.append("mutate")

    def restore():
        if target == "source":
            store.path = original_path
        else:
            object.__setattr__(scope, "namespace", original_namespace)
        calls.append("restore")

    class Cursor:
        def __init__(self, real):
            self.real = real

        def fetchall(self):
            rows = self.real.fetchall()
            if boundary == "fetchall":
                mutate()
            return rows

    class Connection:
        def __init__(self, real):
            self.real = real

        def execute(self, sql, *args, **kwargs):
            if calls == ["mutate"]:
                restore()
            returned = self.real.execute(sql, *args, **kwargs)
            if boundary == "begin" and sql == "BEGIN":
                mutate()
            if sql.startswith("SELECT * FROM memory_events"):
                if boundary == "select":
                    mutate()
                return Cursor(returned)
            return returned

        def close(self):
            self.real.close()

    def connecting():
        real = original_connect()
        if boundary == "connect":
            mutate()
        return Connection(real)

    monkeypatch.setattr(store, "_connect_readonly", connecting)
    with pytest.raises(
        MemorySchemaError, match=f"memory events {target} changed",
    ):
        store.events(scope)
    assert calls == ["mutate"]

    monkeypatch.undo()
    store.path = original_path
    object.__setattr__(scope, "namespace", original_namespace)
    events = store.events(scope)
    assert [event.operation for event in events] == ["create", "create"]
    assert "first local sample" not in repr(events)


def test_memory_events_phased_read_preserves_cursor_budget(tmp_path: Path):
    store, scope = _fixture(tmp_path)
    one = store.events(scope, limit=1)
    assert len(one) == 1
    later = store.events(scope, after_event_id=one[0].event_id, limit=1)
    assert len(later) == 1
    assert later[0].event_id > one[0].event_id
