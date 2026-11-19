"""No private row hydration before the coherent expiry scalar SQL admission."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import coherent_expiry_snapshot_review as mod


@pytest.mark.parametrize(
    "column",
    ("content_sha256", "created_at_ms", "updated_at_ms", "revision", "memory_id"),
)
def test_corrupt_due_scalar_blob_refused_before_select_star(
    tmp_path, monkeypatch, column,
):
    path = tmp_path / "expiry.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("offline-owner", "private")
    store.put(MemoryWrite(scope, "first", "private text", expires_at_ms=1200))
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE source_id='first'",
            (sqlite3.Binary(b"Z" * 1024 * 1024),),
        )

    full_row_selects: list[str] = []
    original = SQLiteMemoryStore._connect_readonly

    def traced_connect(self):
        conn = original(self)
        conn.set_trace_callback(
            lambda sql: full_row_selects.append(sql)
            if sql.startswith("SELECT * FROM memories") else None
        )
        return conn

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", traced_connect)
    with pytest.raises(
        mod.CoherentExpirySnapshotRejected, match="scalar hydration admission",
    ):
        mod.review_coherent_expiry_snapshot(store, (scope,), now_ms=1500)
    assert full_row_selects == []


def test_other_scope_corruption_does_not_block_valid_due_page(tmp_path):
    path = tmp_path / "expiry.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    good = MemoryScope("offline-owner", "safe")
    bad = MemoryScope("offline-owner", "broken")
    store.put(MemoryWrite(good, "first", "valid", expires_at_ms=1200))
    store.put(MemoryWrite(bad, "second", "private", expires_at_ms=1200))
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET updated_at_ms=? WHERE namespace='broken'",
            (sqlite3.Binary(b"Z" * 1024 * 1024),),
        )

    report = mod.review_coherent_expiry_snapshot(
        store, (good,), now_ms=1500,
    )
    assert report.cohort.candidate_count == 1
    assert report.automatic_purge_authorized is False
