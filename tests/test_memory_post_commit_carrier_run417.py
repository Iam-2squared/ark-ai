"""Committed Memory CAS + event survive a late rejected caller-carrier drift.

These are disposable local SQLite fixtures. A rejection after COMMIT does
not undo the durable write, authorize retries, or imply a trusted clock.
"""

import sqlite3
from pathlib import Path
from types import MappingProxyType

import pytest

import ark.memory.sqlite_store as module
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite


def _case(tmp_path):
    source = tmp_path / "memory.sqlite"
    store = module.SQLiteMemoryStore(source, clock_ms=lambda: 100)
    scope = MemoryScope("alice", "notes")
    write = MemoryWrite(
        scope, "fixture", "private but local",
        metadata={"tag": "offline"}, expires_at_ms=1000,
    )
    return source, store, scope, write


def _distinct_equal(value):
    replacement = ("~" + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize("mutate", (
    "content",
    "source_id",
    "owner_carrier",
    "namespace_carrier",
    "metadata_carrier",
    "path_carrier",
    "expiry",
))
def test_memory_record_constructor_cannot_hide_post_commit_input_drift(
    tmp_path, monkeypatch, mutate,
):
    source, store, scope, write = _case(tmp_path)
    original_constructor = module.MemoryRecord
    original_path = store.path

    def constructor(*args, **kwargs):
        if mutate == "content":
            object.__setattr__(write, "content", "changed after commit")
        elif mutate == "source_id":
            object.__setattr__(write, "source_id", "different-source")
        elif mutate == "owner_carrier":
            object.__setattr__(scope, "owner_id", _distinct_equal(scope.owner_id))
        elif mutate == "namespace_carrier":
            object.__setattr__(scope, "namespace", _distinct_equal(scope.namespace))
        elif mutate == "metadata_carrier":
            object.__setattr__(
                write, "metadata", MappingProxyType(dict(write.metadata)),
            )
        elif mutate == "path_carrier":
            object.__setattr__(store, "path", Path(str(store.path)))
            assert store.path is not original_path
        else:
            object.__setattr__(write, "expires_at_ms", 2000)
        return original_constructor(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(module, "MemoryRecord", constructor)
        with pytest.raises(MemorySchemaError, match="changed after commit"):
            store.put(write)

    # The late refusal is a diagnostic, never a rollback claim. The exact
    # revision/event pair remains durable after every late mutation.
    with sqlite3.connect(source) as conn:
        rows = conn.execute("SELECT revision,content FROM memories").fetchall()
        event_rows = conn.execute("SELECT operation,revision FROM memory_events").fetchall()
    assert rows == [(1, "private but local")]
    assert event_rows == [("create", 1)]
    object.__setattr__(store, "path", original_path)
    recovered = store.get(module.deterministic_memory_id(
        MemoryScope("alice", "notes"), "fixture",
    ), MemoryScope("alice", "notes"))
    assert recovered is not None
    assert recovered.revision == 1
    assert recovered.content == "private but local"


def test_unchanged_write_still_creates_one_durable_row_and_event(tmp_path):
    _source, store, scope, write = _case(tmp_path)
    record = store.put(write)
    assert record.revision == 1
    assert record.content == "private but local"
    assert store.get(record.memory_id, scope) == record
    events = store.events(scope)
    assert len(events) == 1
    assert events[0].operation == "create"
