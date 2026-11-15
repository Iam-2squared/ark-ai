"""Corrupted Memory v1 metadata must be bounded before JSON parsing.

Disposable SQLite rows only. The documented v1 metadata key/value budget is
unchanged; no connector data, external context or tool authority is involved.
"""

import sqlite3

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


@pytest.mark.parametrize("method", ["get", "search"])
def test_oversized_persisted_metadata_is_denied_before_json_parser(
    tmp_path, monkeypatch, method,
):
    path = tmp_path / "oversized-metadata.sqlite"
    scope = MemoryScope("synthetic-owner", "notes")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    saved = writer.put(
        MemoryWrite(scope, "source", "fixture-content", {"safe": "yes"}),
        expected_revision=0,
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET metadata_json=? WHERE memory_id=?",
            (" " * (memory_module._MAX_METADATA_JSON_CHARS + 1), saved.memory_id),
        )

    reader = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    calls = []

    def forbidden_parser(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("unbounded SQLite metadata reached JSON parser")

    with monkeypatch.context() as patch:
        patch.setattr(memory_module.json, "loads", forbidden_parser)
        with pytest.raises(MemorySchemaError, match="stored metadata JSON exceeds"):
            if method == "get":
                reader.get(saved.memory_id, scope, include_expired=True)
            else:
                reader.search(MemoryQuery(scope, "", include_expired=True))
    assert calls == []


def test_legal_escaped_metadata_roundtrips_after_reopening(tmp_path):
    path = tmp_path / "escaped-metadata.sqlite"
    scope = MemoryScope("synthetic-owner", "notes")
    metadata = {"entry": "\\u0000" * 4}
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    written = writer.put(
        MemoryWrite(scope, "source", "synthetic-content", metadata),
        expected_revision=0,
    )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    read = reopened.get(written.memory_id, scope)
    assert read is not None
    assert dict(read.metadata) == metadata
    assert read.revision == 1
    assert [(item.event_id, item.operation) for item in reopened.events(scope)] == [
        (1, "create"),
    ]
