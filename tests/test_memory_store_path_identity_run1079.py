"""SQLite Memory cannot be retargeted to another regular private database."""

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryQuery, MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def test_regular_foreign_store_retarget_is_rejected_before_read_or_write(
    tmp_path: Path,
) -> None:
    source = SQLiteMemoryStore(
        tmp_path / "source.sqlite", clock_ms=lambda: 10,
    )
    foreign = SQLiteMemoryStore(
        tmp_path / "foreign.sqlite", clock_ms=lambda: 10,
    )
    source_scope = MemoryScope("owner-a", "private")
    foreign_scope = MemoryScope("owner-b", "private")
    foreign_record = foreign.put(
        MemoryWrite(foreign_scope, "foreign-source", "PRIVATE-FOREIGN-FIXTURE"),
    )
    foreign_events = foreign.events(foreign_scope)

    # Both files are valid, regular SQLite databases. A symlink/hardlink check
    # alone is not enough: the original store must retain its constructor path.
    source.path = foreign.path
    with pytest.raises(MemorySchemaError, match="single regular source"):
        source.get(foreign_record.memory_id, foreign_scope)
    with pytest.raises(MemorySchemaError, match="single regular source"):
        source.put(MemoryWrite(source_scope, "new-source", "must-not-write"))
    with pytest.raises(MemorySchemaError, match="single regular source"):
        source.search(MemoryQuery(foreign_scope, "PRIVATE"))

    assert foreign.get(foreign_record.memory_id, foreign_scope) == foreign_record
    assert foreign.events(foreign_scope) == foreign_events
    assert source_scope.owner_id == "owner-a"


def test_equal_value_replacement_path_object_is_still_a_new_source(
    tmp_path: Path,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    scope = MemoryScope("synthetic-owner", "private")
    original = store.path
    replacement = Path(str(original))
    assert replacement == original and replacement is not original

    store.path = replacement
    with pytest.raises(MemorySchemaError, match="single regular source"):
        store.events(scope)


def test_path_type_change_is_rejected_before_memory_query_validation(
    tmp_path: Path,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    original = store.path
    store.path = str(original)

    with pytest.raises(MemorySchemaError, match="stable Path"):
        store.search(object())  # type: ignore[arg-type]
