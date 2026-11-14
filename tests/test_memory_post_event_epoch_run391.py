"""Memory row and event must roll back on post-write synthetic input drift."""

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryQuery, MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path: Path) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(tmp_path / "memory # %.sqlite", clock_ms=lambda: 100)


def _change(field: str, write: MemoryWrite) -> None:
    if field == "content":
        object.__setattr__(write, "content", "changed-after-event")
    elif field == "source_id":
        object.__setattr__(write, "source_id", "other-source")
    elif field == "metadata":
        object.__setattr__(write, "metadata", {"label": "other"})
    elif field == "expiry":
        object.__setattr__(write, "expires_at_ms", 900)
    elif field == "scope":
        object.__setattr__(write, "scope", MemoryScope("other", "private"))
    else:
        object.__setattr__(write.scope, "namespace", "different")


@pytest.mark.parametrize("field", [
    "content", "source_id", "metadata", "expiry", "scope", "namespace",
])
@pytest.mark.parametrize("updating", [False, True])
def test_put_rolls_back_row_and_event_if_post_event_write_changed(
    tmp_path: Path, monkeypatch, field: str, updating: bool,
) -> None:
    store = _store(tmp_path)
    canonical_scope = MemoryScope("owner", "private")
    original = None
    if updating:
        original = store.put(
            MemoryWrite(canonical_scope, "source", "original", {"label": "old"})
        )
    scope = MemoryScope("owner", "private")
    write = MemoryWrite(
        scope, "source", "new private fixture", {"label": "fixture"},
        expires_at_ms=1000,
    )
    original_event = store._event

    def reflected_change(*args):
        original_event(*args)
        _change(field, write)

    monkeypatch.setattr(store, "_event", reflected_change)
    with pytest.raises(MemorySchemaError, match="changed before event commit"):
        store.put(write, expected_revision=1 if updating else 0)

    fresh = _store(tmp_path)
    actual_scope = MemoryScope("owner", "private")
    rows = fresh.search(MemoryQuery(actual_scope, include_expired=True))
    events = fresh.events(actual_scope)
    if updating:
        assert len(rows) == 1
        assert rows[0].memory_id == original.memory_id
        assert rows[0].content == "original"
        assert rows[0].revision == 1
        assert [(e.operation, e.revision) for e in events] == [("create", 1)]
    else:
        assert rows == []
        assert events == []


@pytest.mark.parametrize("operation", ["delete", "purge"])
def test_terminal_mutation_rolls_back_on_post_event_scope_change(
    tmp_path: Path, monkeypatch, operation: str,
) -> None:
    store = _store(tmp_path)
    scope = MemoryScope("owner", "private")
    saved = store.put(
        MemoryWrite(scope, "source", "original", expires_at_ms=50)
    )
    original_event = store._event

    def reflected_change(*args):
        original_event(*args)
        object.__setattr__(scope, "namespace", "other")

    monkeypatch.setattr(store, "_event", reflected_change)
    with pytest.raises(MemorySchemaError, match="scope changed before commit"):
        if operation == "delete":
            store.delete(saved.memory_id, scope, expected_revision=1)
        else:
            store.purge_expired(scope=scope)

    fresh = _store(tmp_path)
    canonical_scope = MemoryScope("owner", "private")
    assert fresh.get(saved.memory_id, canonical_scope, include_expired=True)
    assert [(e.operation, e.revision) for e in fresh.events(canonical_scope)] == [
        ("create", 1),
    ]
