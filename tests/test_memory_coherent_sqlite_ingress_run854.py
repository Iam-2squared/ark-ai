"""SQLite-native preflight denies malformed Memory before private hydration.

All records are disposable offline fixtures. The retained prefix is not an
independent attestation; neither reviewer grants disclosure or action authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_retained_coherent_review as coherent
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "synthetic-coherent.sqlite", clock_ms=lambda: 1000)
    store.put(MemoryWrite(MemoryScope("owner-a"), "source-a", "private-a"))
    store.put(MemoryWrite(MemoryScope("owner-b"), "source-b", "private-b"))
    retained = (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
    )
    return store, retained


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("content", sqlite3.Binary(b"foreign-binary")),
        ("metadata_json", sqlite3.Binary(b"{}")),
        ("owner_id", sqlite3.Binary(b"owner-a")),
        ("content_sha256", "f" * 65),
        ("source_id", "x" * 513),
        ("content", "x" * 1_000_001),
        ("metadata_json", "x" * 4_000_001),
    ),
)
def test_corrupt_foreign_memory_denied_before_any_python_row_hydration(
    tmp_path, monkeypatch, column, replacement,
):
    store, retained = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE owner_id='owner-b'",
            (replacement,),
        )
    seen = []

    def forbidden_decode(_row):
        seen.append("private data hydrated")
        pytest.fail("untrusted Memory row reached Python hydration")

    monkeypatch.setattr(coherent, "_record", forbidden_decode)
    with pytest.raises(
        coherent.MemoryCoherentHistoryRejected,
        match="width or storage type changed",
    ):
        coherent.review_retained_coherent_memory(store, *retained)
    assert seen == []


@pytest.mark.parametrize("budget", ("_MAX_ROWS", "_MAX_EVENTS"))
def test_sqlite_row_and_event_budgets_refuse_before_hydration(
    tmp_path, monkeypatch, budget,
):
    store, retained = _fixture(tmp_path)
    monkeypatch.setattr(coherent, budget, 0)

    def forbidden_decode(_row):
        pytest.fail("over-budget Memory content was hydrated")

    monkeypatch.setattr(coherent, "_record", forbidden_decode)
    with pytest.raises(
        coherent.MemoryCoherentHistoryRejected,
        match="row/event scan budget exceeded",
    ):
        coherent.review_retained_coherent_memory(store, *retained)


def test_healthy_wal_snapshot_remains_denial_only_and_unchanged(tmp_path):
    store, retained = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    reviewed = coherent.review_retained_coherent_memory(store, *retained)
    assert reviewed.row_count == 2
    assert reviewed.current_event_count == 2
    assert reviewed.status == "UNCHANGED_LOCAL_HISTORY"
    assert reviewed.memory_disclosure_authorized is False
    assert reviewed.action_authorized is False
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before
