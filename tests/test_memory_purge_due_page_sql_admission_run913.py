"""Due-page SQL hydration preflight for local Memory expiry deletion.

Only disposable SQLite v1 fixtures; no real private data or expiry authority.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.memory.sqlite_store as module
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "purge-page.sqlite", clock_ms=lambda: 1000)
    owner = MemoryScope("synthetic-owner", "private")
    record = store.put(MemoryWrite(owner, "old", "payload", expires_at_ms=900))
    return store, owner, record


def _replace(path, memory_id, column, value):
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (value, memory_id),
        )


@pytest.mark.parametrize(
    ("column", "value", "budget"),
    (
        ("content", "multiple-bytes", "_MAX_MEMORY_ROW_CONTENT_BYTES"),
        ("metadata_json", "{\"key\":\"value\"}", "_MAX_MEMORY_ROW_METADATA_BYTES"),
        ("source_id", "old", "_MAX_MEMORY_ROW_SOURCE_BYTES"),
        ("content", sqlite3.Binary(b"not-text"), None),
        ("metadata_json", sqlite3.Binary(b"not-text"), None),
    ),
)
def test_corrupt_due_row_refused_before_select_or_event(
    tmp_path, monkeypatch, column, value, budget,
):
    store, scope, record = _fixture(tmp_path)
    _replace(store.path, record.memory_id, column, value)
    if budget is not None:
        monkeypatch.setattr(module, budget, 1)
    selected = []

    class Guarded(sqlite3.Connection):
        def execute(self, sql, parameters=(), /):
            if sql.strip().lower().startswith("select * from memories"):
                selected.append(sql)
                raise AssertionError("private due page was materialized")
            return super().execute(sql, parameters)

    def guarded_connect(self, *, create=False):
        conn = sqlite3.connect(self.path, factory=Guarded)
        conn.row_factory = sqlite3.Row
        return conn

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect", guarded_connect)
        with pytest.raises(MemorySchemaError, match="expiry page hydration"):
            store.purge_expired(scope=scope, limit=1)

    assert selected == []
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE operation='expire'"
        ).fetchone() == (0,)


def test_global_page_admits_only_ordered_bounded_prefix(tmp_path):
    store, scope, record = _fixture(tmp_path)
    other = MemoryScope("second-owner", "notes")
    second = store.put(MemoryWrite(other, "old2", "payload", expires_at_ms=800))
    first_id, last_id = sorted((record.memory_id, second.memory_id))
    _replace(store.path, last_id, "content", sqlite3.Binary(b"invalid"))
    assert store.purge_expired(limit=1) == 1
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT memory_id FROM memories WHERE memory_id=?", (first_id,),
        ).fetchone() is None
        assert conn.execute(
            "SELECT memory_id FROM memories WHERE memory_id=?", (last_id,),
        ).fetchone() == (last_id,)
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE operation='expire'"
        ).fetchone() == (1,)
    with pytest.raises(MemorySchemaError, match="expiry page hydration"):
        store.purge_expired(limit=1)


def test_unrelated_future_corruption_does_not_block_due_purge(tmp_path):
    store, scope, _ = _fixture(tmp_path)
    future = store.put(MemoryWrite(
        scope, "future", "payload", expires_at_ms=2000,
    ))
    _replace(store.path, future.memory_id, "content", sqlite3.Binary(b"invalid"))
    assert store.purge_expired(scope=scope, limit=10) == 1
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE operation='expire'"
        ).fetchone() == (1,)


def test_valid_multibyte_due_unbounded_compatibility(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "utf8-purge.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("合成", "日本語")
    store.put(MemoryWrite(
        scope, "初期", "🌱" * 50, {"鍵": "🔒" * 30}, expires_at_ms=900,
    ))
    store.put(MemoryWrite(
        scope, "次", "雪の日", expires_at_ms=900,
    ))
    assert store.purge_expired(scope=scope) == 2
    assert store.purge_expired(scope=scope) == 0
    assert [event.operation for event in store.events(scope)].count("expire") == 2
