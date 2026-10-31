"""Ordinary private Memory reads pin scope/source even for empty results.

No production content, erasure, external disclosure, or new Memory schema.
"""

from pathlib import Path

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path: Path):
    path = tmp_path / "memory # %.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    record = store.put(MemoryWrite(scope, "fixture", "synthetic private text"))
    return store, scope, record


@pytest.mark.parametrize("read_api", ["get_missing", "get_existing", "events_empty", "events_full"])
@pytest.mark.parametrize("change", ["scope", "source"])
def test_reentrant_sqlite_validation_cannot_retarget_read(
    tmp_path: Path, monkeypatch, read_api: str, change: str,
):
    store, scope, record = _fixture(tmp_path)
    if read_api == "events_empty":
        scope = MemoryScope("other-owner", "private")
    original_validate = memory_module._validate_v1_schema

    def reentrant_validate(conn):
        original_validate(conn)
        if change == "scope":
            object.__setattr__(scope, "namespace", "different")
        else:
            store.path = Path(str(store.path))

    monkeypatch.setattr(memory_module, "_validate_v1_schema", reentrant_validate)
    expected = "scope changed" if change == "scope" else "source changed"
    with pytest.raises(MemorySchemaError, match=expected):
        if read_api == "get_missing":
            store.get("mem_" + "0" * 64, scope)
        elif read_api == "get_existing":
            store.get(record.memory_id, scope, include_expired=True)
        elif read_api == "events_empty":
            store.events(scope)
        else:
            store.events(scope, limit=1)


def test_empty_results_are_stable_for_unchanged_scope(tmp_path: Path):
    store, _scope, record = _fixture(tmp_path)
    other = MemoryScope("another-owner", "private")
    assert store.get(record.memory_id, other) is None
    assert store.events(other) == []


def test_normal_existing_reads_remain_private_and_content_free_in_events(
    tmp_path: Path,
):
    store, scope, record = _fixture(tmp_path)
    assert store.get(record.memory_id, scope).content == "synthetic private text"
    entries = store.events(scope)
    assert len(entries) == 1
    assert entries[0].operation == "create"
    assert "synthetic private text" not in repr(entries)
