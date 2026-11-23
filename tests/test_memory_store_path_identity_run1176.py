"""Run1176: SQLite Memory cannot be redirected to another valid private store."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _stores(tmp_path: Path):
    scope = MemoryScope("same-owner", "private")
    original_path = tmp_path / "original.sqlite"
    foreign_path = tmp_path / "foreign.sqlite"
    original = SQLiteMemoryStore(original_path, clock_ms=lambda: 100)
    foreign = SQLiteMemoryStore(foreign_path, clock_ms=lambda: 100)
    own = original.put(MemoryWrite(scope, "profile", "original private fixture"))
    other = foreign.put(MemoryWrite(scope, "profile", "foreign private fixture"))
    return original, foreign, scope, own, other


def test_store_rejects_rebind_to_another_valid_private_database_before_read(
    tmp_path: Path,
) -> None:
    original, foreign, scope, own, other = _stores(tmp_path)
    original.path = foreign.path

    with pytest.raises(MemorySchemaError, match="path identity changed"):
        original.get(own.memory_id, scope)

    assert foreign.get(other.memory_id, scope) == other
    assert own.content == "original private fixture"


def test_store_rejects_equal_value_new_path_object_before_write(
    tmp_path: Path,
) -> None:
    original, _, scope, own, _ = _stores(tmp_path)
    retained_path = original.path
    original.path = Path(str(retained_path))

    with pytest.raises(MemorySchemaError, match="path identity changed"):
        original.put(MemoryWrite(scope, "profile", "must not be written"))

    cold = SQLiteMemoryStore(retained_path, clock_ms=lambda: 200)
    assert cold.get(own.memory_id, scope) == own
    assert [event.operation for event in cold.events(scope)] == ["create"]


def test_store_path_identity_anchor_cannot_be_reassigned_or_deleted(
    tmp_path: Path,
) -> None:
    original, foreign, _, _, _ = _stores(tmp_path)

    with pytest.raises(AttributeError, match="path identity is immutable"):
        original._path_identity = foreign.path
    with pytest.raises(AttributeError, match="path identity is immutable"):
        del original._path_identity

    scope = MemoryScope("same-owner", "private")
    saved = original.put(MemoryWrite(scope, "second", "local"))
    assert original.get(saved.memory_id, scope).content == "local"
