"""Memory put must revalidate frozen dataclasses after reflective input mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


class _StrSubclass(str):
    pass


@pytest.mark.parametrize(("field", "value"), [
    ("source_id", " "),
    ("source_id", _StrSubclass("src")),
    ("content", ""),
    ("content", _StrSubclass("private")),
    ("metadata", {"": "value"}),
    ("metadata", {str(i): "v" for i in range(65)}),
    ("metadata", {"ok": 123}),
    ("expires_at_ms", True),
    ("expires_at_ms", -1),
])
def test_reject_preexisting_reflected_invalid_write_without_events(
    tmp_path: Path, field: str, value: object,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    write = MemoryWrite(MemoryScope("alice"), "src", "private")
    object.__setattr__(write, field, value)
    with pytest.raises(MemorySchemaError):
        store.put(write, expected_revision=0)
    assert store.events(MemoryScope("alice")) == []


@pytest.mark.parametrize(("field", "value"), [
    ("owner_id", " "),
    ("owner_id", _StrSubclass("alice")),
    ("namespace", _StrSubclass("default")),
    ("namespace", ""),
])
def test_reject_preexisting_reflected_scope_mutation(
    tmp_path: Path, field: str, value: object,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    write = MemoryWrite(MemoryScope("alice"), "src", "private")
    object.__setattr__(write.scope, field, value)
    with pytest.raises(MemorySchemaError):
        store.put(write)
    assert store.events(MemoryScope("alice")) == []


def test_unmodified_memory_write_still_commits_atomic_row_and_event(tmp_path: Path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("alice")
    record = store.put(MemoryWrite(scope, "src", "private"), expected_revision=0)
    assert record.revision == 1
    assert store.get(record.memory_id, scope) == record
    assert [event.operation for event in store.events(scope)] == ["create"]
