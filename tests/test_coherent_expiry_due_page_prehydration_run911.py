"""Pre-SELECT coherent expiry multi-scope hydration admission.

Every database contains disposable synthetic Memory v1 rows only. This is
read-only and cannot authorize consent, expiry deletion, replay or tools.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.memory.coherent_expiry_snapshot_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "coherent-due.sqlite", clock_ms=lambda: 1000)
    notes = MemoryScope("synthetic-owner", "notes")
    tasks = MemoryScope("synthetic-owner", "tasks")
    store.put(MemoryWrite(notes, "due-notes", "small", expires_at_ms=1200))
    store.put(MemoryWrite(tasks, "due-tasks", "small", expires_at_ms=1300))
    store.put(MemoryWrite(tasks, "future", "small", expires_at_ms=2500))
    return store, notes, tasks


def _corrupt(store, field, value, source):
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memories SET {field}=? WHERE source_id=?",
            (value, source),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("content", "x" * 4_000_001),
        ("source_id", "s" * 2_049),
        ("metadata_json", sqlite3.Binary(b"blob-instead-of-text")),
        ("content", sqlite3.Binary(b"blob-instead-of-text")),
    ),
    ids=("content-size", "source-size", "metadata-blob", "content-blob"),
)
def test_invalid_first_due_page_never_hydrated(
    tmp_path, monkeypatch, field, value,
):
    store, notes, tasks = _fixture(tmp_path)
    _corrupt(store, field, value, "due-notes")
    selected = []

    class Guarded(sqlite3.Connection):
        def execute(self, sql, parameters=(), /):
            if "SELECT * FROM memories WHERE owner_id=?" in sql:
                selected.append(sql)
                raise AssertionError("unbounded private page reached Python")
            return super().execute(sql, parameters)

    def guarded_readonly(_self):
        conn = sqlite3.connect(
            store.path.as_uri() + "?mode=ro", uri=True, factory=Guarded,
        )
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", guarded_readonly)
    with pytest.raises(
        coherent.CoherentExpirySnapshotRejected, match="hydration budget",
    ):
        coherent.review_coherent_expiry_snapshot(
            store, (notes, tasks), now_ms=1500,
        )
    assert selected == []


def test_second_due_scope_refused_before_its_select(tmp_path, monkeypatch):
    store, notes, tasks = _fixture(tmp_path)
    _corrupt(store, "source_id", "z" * 2_049, "due-tasks")
    selected = []

    class Guarded(sqlite3.Connection):
        def execute(self, sql, parameters=(), /):
            if "SELECT * FROM memories WHERE owner_id=?" in sql:
                selected.append(tuple(parameters))
                if parameters[1] == "tasks":
                    raise AssertionError("second malformed due page hydrated")
            return super().execute(sql, parameters)

    def guarded_readonly(_self):
        conn = sqlite3.connect(
            store.path.as_uri() + "?mode=ro", uri=True, factory=Guarded,
        )
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", guarded_readonly)
    with pytest.raises(
        coherent.CoherentExpirySnapshotRejected, match="hydration budget",
    ):
        coherent.review_coherent_expiry_snapshot(
            store, (notes, tasks), now_ms=1500,
        )
    assert selected == [("synthetic-owner", "notes", 1500, 101)]


def test_unrelated_future_content_does_not_block_due_snapshot(tmp_path):
    store, notes, tasks = _fixture(tmp_path)
    _corrupt(store, "content", "x" * 4_000_001, "future")
    report = coherent.review_coherent_expiry_snapshot(
        store, (notes, tasks), now_ms=1500, limit=1,
    )
    assert report.cohort.candidate_count == 2
    assert report.cohort.truncated_scopes == ()
    assert report.automatic_purge_authorized is False
    assert report.owner_consent_authenticated is False
    assert report.trusted_clock_verified is False


def test_mutated_cross_scope_hydration_budget_denied_before_open(
    tmp_path, monkeypatch,
):
    store, notes, tasks = _fixture(tmp_path)
    calls = []

    def forbidden(_self):
        calls.append(True)
        raise AssertionError("tampered policy reached private SQLite")

    monkeypatch.setattr(coherent, "_MAX_TOTAL_HYDRATION_BYTES", 100_000_000)
    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden)
    with pytest.raises(
        coherent.CoherentExpirySnapshotRejected, match="protocol changed",
    ):
        coherent.review_coherent_expiry_snapshot(
            store, (notes, tasks), now_ms=1500,
        )
    assert calls == []
