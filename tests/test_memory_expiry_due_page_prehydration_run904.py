"""Read-only due-page expiry review must not hydrate oversized stored text.

Only disposable local Memory v1 databases and synthetic scopes. No private
external data, trusted time, deletion, consent, replay or backend dispatch.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.expiry_candidate_preview import (
    MemoryExpiryPreviewRejected,
    review_memory_expiry_candidates,
)


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "expiry.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "notes")
    store.put(MemoryWrite(scope, "due", "small", expires_at_ms=1200))
    store.put(MemoryWrite(scope, "future", "small", expires_at_ms=2500))
    return store, scope


def _mutate(store, field, value, source="due"):
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memories SET {field}=? WHERE source_id=?",
            (value, source),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("content", "x" * 4_000_001),
        ("source_id", "q" * 2_049),
        ("metadata_json", sqlite3.Binary(b"not-text")),
        ("content", sqlite3.Binary(b"not-text")),
    ),
    ids=("oversized-content", "oversized-source", "blob-metadata", "blob-content"),
)
def test_due_row_rejected_before_python_hydration(
    tmp_path, monkeypatch, field, value,
):
    store, scope = _fixture(tmp_path)
    _mutate(store, field, value)

    class Guarded(sqlite3.Connection):
        def execute(self, sql, parameters=(), /):
            if "SELECT * FROM memories WHERE owner_id=?" in sql:
                raise AssertionError("unbounded due row was hydrated into Python")
            return super().execute(sql, parameters)

    def guarded_readonly(_self):
        conn = sqlite3.connect(
            store.path.as_uri() + "?mode=ro", uri=True, factory=Guarded,
        )
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", guarded_readonly)
    with pytest.raises(
        MemoryExpiryPreviewRejected, match="page hydration budget",
    ):
        review_memory_expiry_candidates(store, scope, now_ms=1500)


def test_non_due_corrupt_content_does_not_enter_bounded_page(tmp_path):
    store, scope = _fixture(tmp_path)
    _mutate(store, "content", "x" * 4_000_001, source="future")
    report = review_memory_expiry_candidates(store, scope, now_ms=1500)
    assert report.candidate_count == 1
    assert report.has_more is False
    assert report.deletion_authorized is False


def test_valid_page_still_reports_overflow_without_deleting(tmp_path):
    store, scope = _fixture(tmp_path)
    store.put(MemoryWrite(scope, "another", "short", expires_at_ms=1300))
    report = review_memory_expiry_candidates(store, scope, now_ms=1500, limit=1)
    assert report.candidate_count == 1
    assert report.has_more is True
    assert report.trusted_clock_verified is False
