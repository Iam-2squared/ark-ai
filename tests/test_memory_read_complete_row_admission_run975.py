"""Synthetic Memory get/search admission for corrupt non-content SQLite cells.

The frozen v1 row and event schemas are unchanged; a local integrity guard
does not attest writers, authorize memory access, or prove private erasure.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemoryQuery,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize(
    ("column", "corrupt"),
    (
        ("content_sha256", sqlite3.Binary(b"d" * 64)),
        ("content_sha256", "d" * 262144),
        ("created_at_ms", sqlite3.Binary(b"x" * 262144)),
        ("updated_at_ms", 100.5),
        ("expires_at_ms", sqlite3.Binary(b"x" * 262144)),
    ),
    ids=(
        "digest-blob", "digest-oversized", "created-blob",
        "updated-real", "expiry-blob",
    ),
)
def test_read_rejects_noncontent_corruption_before_select_all(
    tmp_path, monkeypatch, column, corrupt,
):
    path = tmp_path / "read-admission.sqlite3"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = store.put(MemoryWrite(scope, "source", "safe fixture"))
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (corrupt, row.memory_id),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    real_connect = reopened._connect_readonly
    reached_select_all: list[str] = []

    class GuardConnection:
        def __init__(self, actual):
            self.actual = actual

        def execute(self, sql, *args):
            if "SELECT * FROM memories" in sql:
                reached_select_all.append(sql)
                pytest.fail("corrupt private row reached Python SELECT * hydration")
            return self.actual.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self.actual, name)

    monkeypatch.setattr(
        reopened, "_connect_readonly", lambda: GuardConnection(real_connect()),
    )
    with pytest.raises(MemorySchemaError, match="read row hydration admission"):
        reopened.get(row.memory_id, scope, include_expired=True)
    with pytest.raises(MemorySchemaError, match="read row hydration admission"):
        reopened.search(MemoryQuery(scope, include_expired=True))
    assert reached_select_all == []

    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)
        assert conn.execute(
            "SELECT operation FROM memory_events",
        ).fetchall() == [("create",)]


def test_read_admission_is_scoped_and_accepts_multilingual_rows(tmp_path):
    path = tmp_path / "read-scope.sqlite3"
    good = MemoryScope("日本語所有者", "調査")
    bad = MemoryScope("日本語所有者", "隔離")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    healthy = store.put(
        MemoryWrite(good, "出典", "安全な合成記録", {"鍵": "値"}),
    )
    damaged = store.put(MemoryWrite(bad, "source", "synthetic"))
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET created_at_ms=? WHERE memory_id=?",
            (sqlite3.Binary(b"unsafe"), damaged.memory_id),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert reopened.get(healthy.memory_id, good) == healthy
    assert reopened.search(MemoryQuery(good, include_expired=True)) == [healthy]
    with pytest.raises(MemorySchemaError, match="read row hydration admission"):
        reopened.search(MemoryQuery(bad, include_expired=True))
