"""Memory event audit reads must retain the caller's original scope carriers.

These are disposable local v1 SQLite events only; no personal data erasure,
external action, or privacy authorization is attempted.
"""

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "events.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "isolated-namespace")
    record = store.put(MemoryWrite(scope, "source", "first"))
    store.put(
        MemoryWrite(scope, "source", "second"),
        expected_revision=record.revision,
    )
    return store, scope


def _replace_equal(scope, field):
    original = getattr(scope, field)
    replacement = ("~" + original)[1:]
    assert replacement == original and replacement is not original
    object.__setattr__(scope, field, replacement)


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
@pytest.mark.parametrize("boundary", ("connect", "schema", "event"))
def test_event_reader_rejects_equal_value_scope_retargeting(
    tmp_path, monkeypatch, field, boundary,
):
    store, scope = _fixture(tmp_path)
    called = []

    if boundary == "connect":
        original = SQLiteMemoryStore._connect_readonly

        def callback(self):
            result = original(self)
            called.append(True)
            _replace_equal(scope, field)
            return result

        monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", callback)
    elif boundary == "schema":
        original = memory_module._validate_v1_schema

        def callback(conn):
            result = original(conn)
            called.append(True)
            _replace_equal(scope, field)
            return result

        monkeypatch.setattr(memory_module, "_validate_v1_schema", callback)
    else:
        original = memory_module.MemoryEvent

        def callback(*args, **kwargs):
            result = original(*args, **kwargs)
            if not called:
                called.append(True)
                _replace_equal(scope, field)
            return result

        monkeypatch.setattr(memory_module, "MemoryEvent", callback)

    with pytest.raises(
        MemorySchemaError, match="memory events scope changed during read",
    ):
        store.events(scope)
    assert called == [True]


def test_unchanged_scope_reads_all_events_without_cross_owner_leak(tmp_path):
    store, scope = _fixture(tmp_path)
    unrelated = MemoryScope("another-owner", scope.namespace)
    store.put(MemoryWrite(unrelated, "source", "private-content"))
    events = store.events(scope)
    assert tuple(event.operation for event in events) == ("create", "update")
    assert all(event.scope == scope for event in events)
    assert store.events(unrelated)[0].scope == unrelated
