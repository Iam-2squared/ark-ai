"""Generation-fenced CAS bounds local memory-row hydration before SELECT *.

Synthetic SQLite corruption only; these tests confer neither consent nor a
trusted clock, authenticated writer identity, external action, or auto-retry.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize(
    ("column", "corruption"),
    (
        ("content", sqlite3.Binary(b"x")),
        ("metadata_json", sqlite3.Binary(b"{}")),
        ("source_id", sqlite3.Binary(b"source")),
        ("content_sha256", sqlite3.Binary(b"a" * 64)),
        ("revision", sqlite3.Binary(b"1")),
        ("content", "a" * 4_000_001),
    ),
    ids=(
        "content-blob", "metadata-blob", "source-blob",
        "hash-blob", "revision-blob", "content-byte-overflow",
    ),
)
def test_corrupt_generation_row_denied_before_python_hydration(
    tmp_path, monkeypatch: pytest.MonkeyPatch, column: str, corruption: object,
) -> None:
    path = tmp_path / "synthetic-cas-row.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    first = store.put(MemoryWrite(scope, "source", "initial fixture"))
    retained = cas.observe_memory_generation_for_cas(store, scope, "source")

    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (corruption, first.memory_id),
        )

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    # Reaching _record proves the row was materialized before SQL admission.
    # Both the observation and optional writer must refuse before that point.
    def forbidden_record(_row: object) -> None:
        raise AssertionError("corrupted private Memory row was hydrated")

    with monkeypatch.context() as patch:
        patch.setattr(cas, "_record", forbidden_record)
        with pytest.raises(
            MemorySchemaError, match="memory mutation row hydration admission failed",
        ):
            cas.observe_memory_generation_for_cas(reopened, scope, "source")
        with pytest.raises(
            MemorySchemaError, match="memory mutation row hydration admission failed",
        ):
            cas.generation_fenced_memory_update(
                reopened,
                MemoryWrite(scope, "source", "must never write"),
                retained=retained,
            )

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events",
        ).fetchone() == (1,)
        assert conn.execute(
            "SELECT revision FROM memories WHERE memory_id=?",
            (first.memory_id,),
        ).fetchone() == (sqlite3.Binary(b"1") if column == "revision" else 1,)


def test_unchanged_memory_row_still_supports_one_local_cas(tmp_path) -> None:
    path = tmp_path / "normal-cas-row.sqlite"
    scope = MemoryScope("所有者", "個人")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "source", "original"))
    retained = cas.observe_memory_generation_for_cas(store, scope, "source")
    assert retained.external_action_authorized is False
    changed = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", "updated"), retained=retained,
    )
    assert changed.revision == 2
    assert [event.operation for event in store.events(scope)] == [
        "create", "update",
    ]
