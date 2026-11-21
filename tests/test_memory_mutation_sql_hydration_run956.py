"""Run956: Memory put/delete guard the primary-key row before SQL hydration.

This synthetic corruption test does not alter frozen Memory-v1 schema or
authenticate a writer. Both mutation paths must fail before SELECT * if the
target row has a damaged scope or an oversized/non-TEXT persisted field.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


@pytest.mark.parametrize(
    ("column", "damaged"),
    (
        ("owner_id", "o" * 1025),
        ("namespace", "n" * 1025),
        ("source_id", "s" * 2049),
        ("content", sqlite3.Binary(b"binary private payload")),
        ("metadata_json", sqlite3.Binary(b"binary private metadata")),
        ("content_sha256", sqlite3.Binary(b"binary digest")),
        ("created_at_ms", sqlite3.Binary(b"100")),
        ("updated_at_ms", sqlite3.Binary(b"100")),
    ),
)
def test_mutation_target_corruption_refused_before_any_row_hydration(
    tmp_path, column: str, damaged: object,
) -> None:
    path = tmp_path / "synthetic-memory-prehydrate.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = store.put(MemoryWrite(scope, "source", "private synthetic fixture"))

    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (damaged, row.memory_id),
        )
        baseline = conn.execute(
            "SELECT * FROM memories WHERE memory_id=?", (row.memory_id,),
        ).fetchone()
        events = conn.execute("SELECT * FROM memory_events").fetchall()

    # A damaged owner/namespace is deliberately absent from a scope-filtered
    # read; the mutation path must still preflight it by deterministic ID.
    with pytest.raises(
        MemorySchemaError, match="mutation row hydration admission",
    ):
        store.put(
            MemoryWrite(scope, "source", "must-not-write"),
            expected_revision=1,
        )
    with pytest.raises(
        MemorySchemaError, match="mutation row hydration admission",
    ):
        store.delete(row.memory_id, scope, expected_revision=1)

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM memories WHERE memory_id=?", (row.memory_id,),
        ).fetchone() == baseline
        assert conn.execute("SELECT * FROM memory_events").fetchall() == events


def test_healthy_unicode_memory_mutations_keep_frozen_v1_semantics(tmp_path) -> None:
    store = SQLiteMemoryStore(
        tmp_path / "healthy-unicode.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("日本語ユーザー", "プライベート")
    initial = store.put(MemoryWrite(scope, "ソース", "機密ではないテスト"))
    updated = store.put(
        MemoryWrite(scope, "ソース", "次の内容"), expected_revision=1,
    )
    assert updated.memory_id == initial.memory_id
    assert updated.revision == 2
    assert store.delete(initial.memory_id, scope, expected_revision=2)
    assert store.get(initial.memory_id, scope) is None
    assert [event.operation for event in store.events(scope)] == [
        "create", "update", "delete",
    ]
