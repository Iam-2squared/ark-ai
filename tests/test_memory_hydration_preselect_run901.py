"""Synthetic Memory v1 pre-SELECT SQLite TEXT budget and parser regressions.

No trusted consent/provenance, real context export, paid compute, or schema
migration is implied by this bounded local corruption fixture.
"""

import sqlite3

import pytest

import ark.memory.sqlite_store as module
from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def _fixture(tmp_path):
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("local-owner", "local-namespace")
    record = store.put(MemoryWrite(
        scope, "local-source", "fixture", {"key": "value"},
    ))
    return path, store, scope, record


@pytest.mark.parametrize(
    ("limit_name", "value"),
    [
        ("_MAX_MEMORY_ROW_CONTENT_BYTES", 6),
        ("_MAX_MEMORY_ROW_METADATA_BYTES", 1),
        ("_MAX_MEMORY_ROW_SOURCE_BYTES", 1),
    ],
)
def test_get_and_search_refuse_sqlite_text_oversize_before_record_decode(
    tmp_path, monkeypatch, limit_name, value,
):
    _, store, scope, record = _fixture(tmp_path)
    monkeypatch.setattr(module, limit_name, value)

    def cannot_decode(_row):
        raise AssertionError("pre-SELECT budget must refuse before _record")

    monkeypatch.setattr(module, "_record", cannot_decode)
    with pytest.raises(MemorySchemaError, match="MemoryWrite bounds"):
        store.get(record.memory_id, scope, include_expired=True)
    with pytest.raises(MemorySchemaError, match="MemoryWrite bounds"):
        store.search(MemoryQuery(scope, include_expired=True))


def test_search_total_hydration_budget_is_scoped_and_read_only(
    tmp_path, monkeypatch,
):
    path, store, scope, record = _fixture(tmp_path)
    other = MemoryScope(scope.owner_id, "unrelated")
    store.put(MemoryWrite(other, "second", "private-other-namespace"))
    # The same row is a valid point GET; the search-wide budget is separate.
    assert store.get(record.memory_id, scope) == record
    monkeypatch.setattr(module, "_MAX_MEMORY_SEARCH_HYDRATION_BYTES", 1)
    with pytest.raises(MemorySchemaError, match="hydration budget"):
        store.search(MemoryQuery(scope, limit=1))
    # One unrelated, otherwise small row is not evidence of authorized
    # disclosure; it must not consume another namespace's read budget.
    monkeypatch.setattr(module, "_MAX_MEMORY_SEARCH_HYDRATION_BYTES", 10_000)
    assert store.search(MemoryQuery(scope, limit=1))[0] == record
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (2,)
        assert conn.execute("PRAGMA user_version").fetchone() == (1,)


def test_deep_corrupt_metadata_is_classified_as_schema_error(tmp_path):
    path, store, scope, record = _fixture(tmp_path)
    # Valid nested arrays can parse on newer Python versions and then fail
    # the mapping check instead. Use genuinely invalid JSON at every depth
    # so this asserts the parser-error boundary on Python 3.11–3.13.
    deep_json = "[" * 1500 + "not-json" + "]" * 1500
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET metadata_json=? WHERE memory_id=?",
            (deep_json, record.memory_id),
        )
    with pytest.raises(MemorySchemaError, match="metadata JSON is invalid"):
        store.get(record.memory_id, scope, include_expired=True)
    with pytest.raises(MemorySchemaError, match="metadata JSON is invalid"):
        store.search(MemoryQuery(scope, include_expired=True))


def test_valid_multibyte_memory_roundtrip_still_supported(tmp_path):
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("多言語", "合成")
    write = MemoryWrite(scope, "出典", "🌱" * 100, {"鍵": "🔐" * 30})
    record = store.put(write)
    assert store.get(record.memory_id, scope) == record
    assert store.search(MemoryQuery(scope, text="", limit=1)) == [record]
