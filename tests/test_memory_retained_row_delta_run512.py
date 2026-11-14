"""Retained per-row Memory commitments detect silent edits despite event tails."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import replace

import pytest

import ark.memory.sqlite_retained_row_delta_review as delta
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "row-delta.sqlite3", clock_ms=lambda: 1500)


def _put(store, name="old", text="private original", *, revision=0):
    return store.put(
        MemoryWrite(MemoryScope("owner", "notes"), name, text),
        expected_revision=revision,
    )


def test_empty_row_baseline_is_content_free_and_inert(tmp_path):
    store = _store(tmp_path)
    witness = delta.capture_local_memory_row_delta(store)
    report = delta.review_retained_memory_row_delta(store, witness)
    assert (witness.event_count, witness.last_event_id, witness.rows) == (0, 0, ())
    assert (report.retained_rows, report.current_rows) == (0, 0)
    assert (report.appended_events, report.explained_changes) == (0, 0)
    assert witness.independently_authenticated is False
    assert witness.historical_writer_authenticated is False
    assert witness.disclosure_authorized is False
    assert witness.action_authorized is False
    assert report.writer_authenticated is False
    assert report.disclosure_authorized is False
    assert report.action_authorized is False


def test_clean_unchanged_baseline_is_repeatable(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    one = delta.review_retained_memory_row_delta(store, witness)
    two = delta.review_retained_memory_row_delta(store, witness)
    assert one == two
    assert one.explained_changes == 0
    assert len(witness.rows) == 1
    assert "private original" not in repr(witness)
    assert "private original" not in repr(one)


def test_independent_new_memory_append_does_not_invalidate_old_rows(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    _put(store, "new", "second content")
    report = delta.review_retained_memory_row_delta(store, witness)
    assert (report.retained_rows, report.current_rows) == (1, 2)
    assert (report.appended_events, report.explained_changes) == (1, 1)


def test_own_update_event_allows_changed_row_without_claiming_authorship(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    _put(store, "old", "updated content", revision=1)
    report = delta.review_retained_memory_row_delta(store, witness)
    assert (report.appended_events, report.explained_changes) == (1, 1)
    assert report.writer_authenticated is False


def test_own_delete_event_accounts_for_missing_row(tmp_path):
    store = _store(tmp_path)
    first = _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    assert store.delete(first.memory_id, first.scope, expected_revision=1)
    report = delta.review_retained_memory_row_delta(store, witness)
    assert (report.current_rows, report.explained_changes) == (0, 1)


@pytest.mark.parametrize("mutation", ("metadata", "content", "expiry", "revision"))
def test_unrelated_append_cannot_hide_old_row_drift(tmp_path, mutation):
    store = _store(tmp_path)
    first = _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    _put(store, "new", "valid event on another memory")
    with sqlite3.connect(store.path) as conn:
        if mutation == "metadata":
            conn.execute(
                "UPDATE memories SET metadata_json=? WHERE memory_id=?",
                ('{"changed":"yes"}', first.memory_id),
            )
        elif mutation == "content":
            changed = "silent replacement"
            conn.execute(
                "UPDATE memories SET content=?,content_sha256=? WHERE memory_id=?",
                (changed, hashlib.sha256(changed.encode()).hexdigest(), first.memory_id),
            )
        elif mutation == "expiry":
            conn.execute(
                "UPDATE memories SET expires_at_ms=9999 WHERE memory_id=?",
                (first.memory_id,),
            )
        else:
            conn.execute(
                "UPDATE memories SET revision=2 WHERE memory_id=?",
                (first.memory_id,),
            )
    with pytest.raises(
        delta.MemoryRowDeltaRejected, match="without its own|event lifecycle",
    ):
        delta.review_retained_memory_row_delta(store, witness)


def test_unrelated_event_cannot_hide_silent_row_deletion(tmp_path):
    store = _store(tmp_path)
    first = _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    _put(store, "new")
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memories WHERE memory_id=?", (first.memory_id,))
    with pytest.raises(
        delta.MemoryRowDeltaRejected, match="without its own|event lifecycle",
    ):
        delta.review_retained_memory_row_delta(store, witness)


def test_historical_event_mutation_with_following_append_is_rejected(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    _put(store, "new")
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET occurred_at_ms=999 WHERE event_id=1")
    with pytest.raises(
        delta.MemoryRowDeltaRejected, match="event prefix|lacks creation event|timestamps",
    ):
        delta.review_retained_memory_row_delta(store, witness)


def test_deleted_historical_event_is_rejected(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(
        delta.MemoryRowDeltaRejected, match="event prefix|lacks creation event",
    ):
        delta.review_retained_memory_row_delta(store, witness)


def test_independently_pinned_witness_cannot_be_mutated_during_scan(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    original = delta._commitment

    def mutate_at_row(row):
        result = original(row)
        object.__setattr__(witness, "event_prefix_sha256", "0" * 64)
        return result

    monkeypatch.setattr(delta, "_commitment", mutate_at_row)
    with pytest.raises(delta.MemoryRowDeltaRejected, match="changed"):
        delta.review_retained_memory_row_delta(store, witness)


def test_invalid_witness_shape_is_not_a_baseline(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    for replacement in (
        replace(witness, event_count=True),
        replace(witness, rows=(("wrong", 1, "0" * 64),)),
        replace(witness, last_event_id=0),
        replace(witness, rows=witness.rows + witness.rows),
    ):
        with pytest.raises(delta.MemoryRowDeltaRejected):
            delta.review_retained_memory_row_delta(store, replacement)


def test_coherent_reader_does_not_write_to_sqlite(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    delta.review_retained_memory_row_delta(store, witness)
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before


def test_wal_writer_between_row_and_event_scan_cannot_mix_epochs(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    _put(store)
    original = delta._commitment
    injected = False

    def append_during_read(row):
        nonlocal injected
        value = original(row)
        if not injected:
            injected = True
            _put(store, "new")
        return value

    monkeypatch.setattr(delta, "_commitment", append_during_read)
    baseline = delta.capture_local_memory_row_delta(store)
    assert injected
    assert baseline.event_count == 1
    assert len(baseline.rows) == 1
    result = delta.review_retained_memory_row_delta(store, baseline)
    assert (result.appended_events, result.current_rows) == (1, 2)


def test_modified_or_unknown_schema_is_rejected(tmp_path):
    store = _store(tmp_path)
    _put(store)
    witness = delta.capture_local_memory_row_delta(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute("PRAGMA user_version=987")
    with pytest.raises(delta.MemoryRowDeltaRejected):
        delta.review_retained_memory_row_delta(store, witness)


@pytest.mark.parametrize(("field", "replacement"), [
    ("event_count", 2),
    ("event_prefix_sha256", "f" * 64),
    ("rows", ()),
])
def test_capture_refuses_mutated_witness_after_last_false_denial(
    tmp_path, monkeypatch, field, replacement,
):
    store = _store(tmp_path)
    _put(store)
    def mutate_capture(self):
        object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        delta.MemoryRowDeltaWitness, "action_authorized",
        property(mutate_capture),
    )
    with pytest.raises(delta.MemoryRowDeltaRejected, match="changed after denial"):
        delta.capture_local_memory_row_delta(store)


def test_capture_refuses_swapped_prior_denial_descriptor(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    _put(store)

    def mutate_capture(self):
        monkeypatch.setattr(
            delta.MemoryRowDeltaWitness, "independently_authenticated",
            property(lambda ignored: True),
        )
        return False

    monkeypatch.setattr(
        delta.MemoryRowDeltaWitness, "action_authorized",
        property(mutate_capture),
    )
    with pytest.raises(
        delta.MemoryRowDeltaRejected, match="authority descriptor changed",
    ):
        delta.capture_local_memory_row_delta(store)
