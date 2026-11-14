"""Retained Memory event prefixes survive append, not historical rewrites."""

import sqlite3
from dataclasses import replace

import pytest

import ark.memory.sqlite_event_prefix_review as prefix_review
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixComparison,
    MemoryEventPrefixRejected,
    MemoryEventPrefixWitness,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)


def _memory(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "prefix.db", clock_ms=lambda: 5000)
    scope = MemoryScope("owner")
    store.put(MemoryWrite(scope, "source-one", "private memory text"))
    return store, scope


def test_empty_genesis_witness_is_stable_and_inert(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "empty.db", clock_ms=lambda: 1000)
    retained = capture_local_memory_event_prefix(store)
    assert retained.event_count == 0
    assert retained.last_event_id == 0
    assert len(retained.prefix_sha256) == 64
    result = compare_local_memory_event_prefix(store, retained)
    assert result.status == "UNCHANGED_LOCAL_EVENT_PREFIX"
    assert result.previous_event_count == result.current_event_count == 0
    assert result.action_authorized is False
    assert retained.independently_authenticated is False


def test_unchanged_prefix_is_deterministic_and_discloses_no_content(tmp_path):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    one = compare_local_memory_event_prefix(store, retained)
    two = compare_local_memory_event_prefix(store, retained)
    assert one == two
    assert one.status == "UNCHANGED_LOCAL_EVENT_PREFIX"
    assert one.previous_event_count == 1
    assert one.current_event_count == 1
    assert one.independent_witness_custody_proven is False
    assert one.historical_writer_authenticated is False
    assert one.memory_disclosure_authorized is False
    assert "private memory" not in repr(one)


def test_new_events_keep_retained_prefix_but_do_not_authenticate_it(tmp_path):
    store, scope = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "source-two", "private second memory"))
    result = compare_local_memory_event_prefix(store, retained)
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.action_authorized is False


@pytest.mark.parametrize(
    ("sql", "parameters"),
    [
        ("UPDATE memory_events SET occurred_at_ms=? WHERE event_id=1", (6000,)),
        ("UPDATE memory_events SET revision=? WHERE event_id=1", (2,)),
        ("UPDATE memory_events SET owner_id=? WHERE event_id=1", ("other",)),
        ("UPDATE memory_events SET operation=? WHERE event_id=1", ("delete",)),
    ],
)
def test_rewritten_historical_prefix_is_rejected_despite_new_append(
    tmp_path, sql, parameters,
):
    store, scope = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "source-two", "more private memory"))
    with sqlite3.connect(store.path) as conn:
        conn.execute(sql, parameters)
    with pytest.raises(MemoryEventPrefixRejected):
        compare_local_memory_event_prefix(store, retained)


def test_same_count_rewrite_is_rejected(tmp_path):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET occurred_at_ms=9000")
    with pytest.raises(MemoryEventPrefixRejected, match="prefix"):
        compare_local_memory_event_prefix(store, retained)


def test_rollback_of_event_tail_is_rejected(tmp_path):
    store, scope = _memory(tmp_path)
    store.put(MemoryWrite(scope, "source-two", "another memory"))
    retained = capture_local_memory_event_prefix(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=2")
    # The scan now rejects the deleted local tail at the durable SQLite
    # high-water check, before the retained-prefix rollback comparison.
    with pytest.raises(MemoryEventPrefixRejected, match="high-water"):
        compare_local_memory_event_prefix(store, retained)


def test_event_storage_class_and_lifecycle_are_checked(tmp_path):
    store, _ = _memory(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET occurred_at_ms=1.5")
    with pytest.raises(MemoryEventPrefixRejected, match="stored event"):
        capture_local_memory_event_prefix(store)


@pytest.mark.parametrize(
    "invalid",
    [
        {"event_count": True},
        {"last_event_id": 0},
        {"prefix_sha256": "not-sha"},
    ],
)
def test_witness_exact_types_and_shape_are_required(tmp_path, invalid):
    store, _ = _memory(tmp_path)
    retained = replace(capture_local_memory_event_prefix(store), **invalid)
    with pytest.raises(MemoryEventPrefixRejected):
        compare_local_memory_event_prefix(store, retained)


def test_source_and_witness_type_are_exact(tmp_path):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    with pytest.raises(MemoryEventPrefixRejected):
        capture_local_memory_event_prefix(object())
    with pytest.raises(MemoryEventPrefixRejected):
        compare_local_memory_event_prefix(store, object())
    assert retained.event_count == 1


def test_read_only_review_does_not_write_database(tmp_path):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    compare_local_memory_event_prefix(store, retained)
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before


def test_result_cannot_become_action_authority(tmp_path, monkeypatch):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    monkeypatch.setattr(
        MemoryEventPrefixComparison, "action_authorized",
        property(lambda self: True),
    )
    with pytest.raises(MemoryEventPrefixRejected, match="authority"):
        compare_local_memory_event_prefix(store, retained)


def test_witness_cannot_become_external_authentication(tmp_path, monkeypatch):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    monkeypatch.setattr(
        MemoryEventPrefixWitness, "independently_authenticated",
        property(lambda self: True),
    )
    with pytest.raises(MemoryEventPrefixRejected, match="authority"):
        compare_local_memory_event_prefix(store, retained)


def test_reentrant_prefix_scan_cannot_retarget_retained_witness(
    tmp_path, monkeypatch,
):
    store, _ = _memory(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    original = prefix_review._scan

    def mutate_after_scan(source, *, prefix_count):
        result = original(source, prefix_count=prefix_count)
        object.__setattr__(retained, "prefix_sha256", "0" * 64)
        return result

    monkeypatch.setattr(prefix_review, "_scan", mutate_after_scan)
    with pytest.raises(MemoryEventPrefixRejected, match="carrier"):
        compare_local_memory_event_prefix(store, retained)
