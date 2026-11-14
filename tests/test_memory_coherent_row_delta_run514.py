"""One WAL snapshot reconciles retained Memory rows and event history."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import replace

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_row_delta_review import capture_local_memory_row_delta


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "coherent-row-delta.sqlite3", clock_ms=lambda: 1500)


def _put(store, source="first", content="private text", *, revision=0):
    return store.put(
        MemoryWrite(MemoryScope("owner", "notes"), source, content),
        expected_revision=revision,
    )


def _before(store):
    return (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
        capture_local_memory_row_delta(store),
    )


def _review(store, witnesses):
    return coherent.review_retained_coherent_memory(
        store, witnesses[0], witnesses[1], prior_rows=witnesses[2],
    )


def test_genesis_and_single_row_are_inert_and_do_not_leak_content(tmp_path):
    store = _store(tmp_path)
    empty = _review(store, _before(store))
    assert empty.retained_row_delta_checked is True
    assert empty.current_event_count == empty.row_count == 0
    _put(store)
    result = _review(store, _before(store))
    assert result.retained_row_delta_checked is True
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.memory_disclosure_authorized is False
    assert result.historical_writer_authenticated is False
    assert result.action_authorized is False
    assert "private text" not in repr(result)


def test_legacy_two_witness_call_stays_compatible(tmp_path):
    store = _store(tmp_path)
    _put(store)
    previous = _before(store)
    report = coherent.review_retained_coherent_memory(store, *previous[:2])
    assert report.retained_row_delta_checked is False
    assert report.status == "UNCHANGED_LOCAL_HISTORY"


def test_unrelated_append_preserves_unchanged_old_row(tmp_path):
    store = _store(tmp_path)
    _put(store)
    before = _before(store)
    _put(store, "second")
    result = _review(store, before)
    assert (result.previous_event_count, result.current_event_count) == (1, 2)
    assert result.row_count == 2
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.retained_row_delta_checked is True


def test_own_update_event_explains_change_without_proving_writer(tmp_path):
    store = _store(tmp_path)
    _put(store)
    before = _before(store)
    _put(store, content="new private text", revision=1)
    report = _review(store, before)
    assert report.current_event_count == 2
    assert report.historical_writer_authenticated is False


def test_own_delete_event_explains_removed_row(tmp_path):
    store = _store(tmp_path)
    initial = _put(store)
    before = _before(store)
    assert store.delete(initial.memory_id, initial.scope, expected_revision=1)
    report = _review(store, before)
    assert report.row_count == 0
    assert report.current_event_count == 2


@pytest.mark.parametrize("field,value", (
    ("metadata_json", '{"tag":"silent"}'),
    ("created_at_ms", 900),
    ("updated_at_ms", 1700),
    ("expires_at_ms", 9999),
))
def test_unrelated_append_does_not_excuse_silent_row_metadata_mutation(
    tmp_path, field, value,
):
    store = _store(tmp_path)
    initial = _put(store)
    before = _before(store)
    _put(store, "second")
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memories SET {field}=? WHERE memory_id=?",
            (value, initial.memory_id),
        )
    # Own-lifecycle timestamp drift now rejects before optional row-delta.
    expected = "row/time" if field in {"created_at_ms", "updated_at_ms"} else "without its own"
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match=expected):
        _review(store, before)


def test_rehashed_silent_content_rewrite_is_rejected_after_unrelated_append(tmp_path):
    store = _store(tmp_path)
    initial = _put(store)
    before = _before(store)
    _put(store, "second")
    text = "rewritten private content"
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memories SET content=?, content_sha256=? WHERE memory_id=?",
            (text, hashlib.sha256(text.encode()).hexdigest(), initial.memory_id),
        )
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="without its own"):
        _review(store, before)


def test_unrelated_append_does_not_excuse_silent_row_deletion(tmp_path):
    store = _store(tmp_path)
    initial = _put(store)
    before = _before(store)
    _put(store, "second")
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memories WHERE memory_id=?", (initial.memory_id,))
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        _review(store, before)


def test_cross_epoch_row_witness_is_rejected_before_any_read(tmp_path):
    store = _store(tmp_path)
    _put(store)
    old_prefix, old_alignment, _ = _before(store)
    _put(store, "second")
    new_rows = capture_local_memory_row_delta(store)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="epoch differs"):
        coherent.review_retained_coherent_memory(
            store, old_prefix, old_alignment, prior_rows=new_rows,
        )


def test_malformed_or_authority_forged_row_witness_is_not_accepted(tmp_path):
    store = _store(tmp_path)
    _put(store)
    old_prefix, old_alignment, old_rows = _before(store)
    for altered in (
        replace(old_rows, event_count=True),
        replace(old_rows, rows=old_rows.rows + old_rows.rows),
        replace(old_rows, event_prefix_sha256="0" * 64),
    ):
        with pytest.raises(coherent.MemoryCoherentHistoryRejected):
            coherent.review_retained_coherent_memory(
                store, old_prefix, old_alignment, prior_rows=altered,
            )


def test_row_witness_reflective_retargeting_during_scan_is_rejected(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    _put(store)
    retained = _before(store)
    original = coherent.row_delta._commitment
    changed = False

    def retarget(row):
        nonlocal changed
        result = original(row)
        if not changed:
            changed = True
            object.__setattr__(retained[2], "rows", ())
        return result

    monkeypatch.setattr(coherent.row_delta, "_commitment", retarget)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="witness"):
        _review(store, retained)
    assert changed


def test_concurrent_wal_writer_during_row_scan_does_not_mix_epochs(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    _put(store)
    retained = _before(store)
    original = coherent.row_delta._commitment
    injected = False

    def insert_after_row(row):
        nonlocal injected
        result = original(row)
        if not injected:
            injected = True
            _put(store, "second")
        return result

    monkeypatch.setattr(coherent.row_delta, "_commitment", insert_after_row)
    first = _review(store, retained)
    assert injected
    assert (first.row_count, first.current_event_count) == (1, 1)
    second = _review(store, retained)
    assert (second.row_count, second.current_event_count) == (2, 2)


def test_optional_row_delta_read_never_writes_database(tmp_path):
    store = _store(tmp_path)
    _put(store)
    retained = _before(store)
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    a = _review(store, retained)
    b = _review(store, retained)
    assert a == b
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before
