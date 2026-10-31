"""Read-only retained local event/row alignment detects silent edits and rollback."""

import sqlite3
from dataclasses import replace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_alignment_retained_review import (
    MemoryAlignmentHistoryRejected,
    RetainedMemoryAlignmentComparison,
    compare_retained_memory_alignment,
)
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentReview,
    review_memory_event_alignment,
)


def _memory(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "retained.db", clock_ms=lambda: 5000)
    scope = MemoryScope("owner")
    store.put(MemoryWrite(scope, "source-one", "private one"))
    return store, scope


def test_unchanged_local_history_has_no_disclosure_or_authority(tmp_path):
    store, _ = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    first = compare_retained_memory_alignment(store, retained)
    second = compare_retained_memory_alignment(store, retained)
    assert first == second
    assert first.status == "UNCHANGED_LOCAL_HISTORY"
    assert first.appended_event_count == 0
    assert first.current_event_count == 1
    assert len(first.comparison_sha256) == 64
    assert first.historical_prefix_authenticated is False
    assert first.writer_authenticated is False
    assert first.content_disclosure_authorized is False
    assert first.dispatch_authorized is False
    assert "private" not in repr(first)


def test_legitimate_append_is_explicitly_not_authenticated(tmp_path):
    store, scope = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    store.put(MemoryWrite(scope, "source-two", "private two"))
    result = compare_retained_memory_alignment(store, retained)
    assert result.appended_event_count == 1
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.historical_prefix_authenticated is False
    assert result.writer_authenticated is False


@pytest.mark.parametrize(
    ("sql", "parameters"),
    [
        ("UPDATE memories SET expires_at_ms=?", (9000,)),
        ("UPDATE memories SET metadata_json=?", ('{"retained":"different"}',)),
        ("UPDATE memories SET updated_at_ms=?", (6000,)),
        ("UPDATE memory_events SET occurred_at_ms=?", (6000,)),
    ],
)
def test_no_event_append_cannot_hide_changed_local_data(tmp_path, sql, parameters):
    store, _ = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute(sql, parameters)
    with pytest.raises(MemoryAlignmentHistoryRejected, match="without appended"):
        compare_retained_memory_alignment(store, retained)


@pytest.mark.parametrize(
    "changes",
    [
        {"event_count": 2, "last_event_id": 2},
        {"last_event_id": 2},
        {"scope_count": 2},
        {"digest": "0" * 64},
        {"event_count": True},
        {"digest": "NOT_A_SHA"},
    ],
)
def test_forged_or_rolled_back_retained_witness_is_denied(tmp_path, changes):
    store, _ = _memory(tmp_path)
    retained = replace(review_memory_event_alignment(store), **changes)
    with pytest.raises(MemoryAlignmentHistoryRejected):
        compare_retained_memory_alignment(store, retained)


def test_comparison_does_not_change_database(tmp_path):
    store, _ = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    compare_retained_memory_alignment(store, retained)
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before


def test_retained_authority_property_cannot_be_forged(tmp_path, monkeypatch):
    store, _ = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    monkeypatch.setattr(
        MemoryEventAlignmentReview, "action_authorized",
        property(lambda self: True),
    )
    with pytest.raises(MemoryAlignmentHistoryRejected, match="authority"):
        compare_retained_memory_alignment(store, retained)


def test_result_authority_property_cannot_be_forged(tmp_path, monkeypatch):
    store, _ = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    monkeypatch.setattr(
        RetainedMemoryAlignmentComparison, "dispatch_authorized",
        property(lambda self: True),
    )
    with pytest.raises(MemoryAlignmentHistoryRejected, match="authority"):
        compare_retained_memory_alignment(store, retained)


def test_source_and_witness_type_must_be_exact(tmp_path):
    store, _ = _memory(tmp_path)
    retained = review_memory_event_alignment(store)
    with pytest.raises(MemoryAlignmentHistoryRejected):
        compare_retained_memory_alignment(object(), retained)
    with pytest.raises(MemoryAlignmentHistoryRejected):
        compare_retained_memory_alignment(store, object())
