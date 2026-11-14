"""Free-only, retained Memory v1 comparisons across local observations."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.memory.retained_epoch_review as retained
from ark.memory.atomic_epoch_review import review_atomic_memory_epoch
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path, name="memory.sqlite", clock=None):
    return SQLiteMemoryStore(
        tmp_path / name,
        clock_ms=(lambda: clock[0]) if clock is not None else (lambda: 1000),
    )


def _put(store, scope, *, content="private memory", revision=0):
    return store.put(
        MemoryWrite(scope, "fixture-source", content),
        expected_revision=revision,
    )


def test_unchanged_local_rows_are_clock_independent(tmp_path):
    clock = [1000]
    store = _store(tmp_path, clock=clock)
    scope = MemoryScope("owner", "notes")
    _put(store, scope)
    first = review_atomic_memory_epoch(store, (scope,))
    clock[0] = 2000
    second = review_atomic_memory_epoch(store, (scope,))
    assert first.epoch_digest != second.epoch_digest
    assert first.content_digest == second.content_digest
    compared = retained.review_retained_memory_epoch(first, second)
    assert compared.status == "UNCHANGED_LOCAL_CONTENT"
    assert compared.new_event_counts == (0,)
    assert not compared.independent_writer_proven
    assert not compared.custody_authenticated
    assert not compared.historical_prefix_proven
    assert not compared.memory_disclosure_authorized
    assert not compared.dispatch_authorized
    assert "private memory" not in repr(compared)


def test_legitimate_append_is_explicitly_unverified(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    _put(store, scope)
    first = review_atomic_memory_epoch(store, (scope,))
    _put(store, scope, content="updated private", revision=1)
    second = review_atomic_memory_epoch(store, (scope,))
    compared = retained.review_retained_memory_epoch(first, second)
    assert compared.new_event_counts == (1,)
    assert compared.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert compared.historical_prefix_proven is False


def test_restart_with_same_store_bytes_stays_coherent(tmp_path):
    first_store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    _put(first_store, scope)
    first = review_atomic_memory_epoch(first_store, (scope,))
    reopened = _store(tmp_path)
    second = review_atomic_memory_epoch(reopened, (scope,))
    assert retained.review_retained_memory_epoch(
        first, second,
    ).status == "UNCHANGED_LOCAL_CONTENT"


def test_consistent_older_database_is_detected_as_regression(tmp_path):
    scope = MemoryScope("owner", "notes")
    newer_store = _store(tmp_path, "new.sqlite")
    older_store = _store(tmp_path, "old.sqlite")
    _put(newer_store, scope)
    _put(newer_store, scope, revision=1, content="private update")
    _put(older_store, scope)
    previous = review_atomic_memory_epoch(newer_store, (scope,))
    current = review_atomic_memory_epoch(older_store, (scope,))
    with pytest.raises(MemorySchemaError, match="regressed"):
        retained.review_retained_memory_epoch(previous, current)


def test_same_event_tail_with_rewritten_content_is_denied(tmp_path):
    scope = MemoryScope("owner", "notes")
    first_store = _store(tmp_path, "left.sqlite")
    second_store = _store(tmp_path, "right.sqlite")
    _put(first_store, scope, content="first secret")
    _put(second_store, scope, content="different secret")
    previous = review_atomic_memory_epoch(first_store, (scope,))
    current = review_atomic_memory_epoch(second_store, (scope,))
    assert previous.event_tail_ids == current.event_tail_ids
    with pytest.raises(MemorySchemaError, match="content changed without event"):
        retained.review_retained_memory_epoch(previous, current)


def test_same_count_but_different_tail_id_denied(tmp_path):
    scope = MemoryScope("owner", "notes")
    first_store = _store(tmp_path, "left.sqlite")
    second_store = _store(tmp_path, "right.sqlite")
    _put(first_store, scope)
    _put(second_store, MemoryScope("owner", "other"))
    _put(second_store, scope)
    previous = review_atomic_memory_epoch(first_store, (scope,))
    current = review_atomic_memory_epoch(second_store, (scope,))
    with pytest.raises(MemorySchemaError, match="tail replaced"):
        retained.review_retained_memory_epoch(previous, current)


def test_other_scope_cannot_be_substituted(tmp_path):
    store = _store(tmp_path)
    a = MemoryScope("owner", "a")
    b = MemoryScope("owner", "b")
    _put(store, a)
    _put(store, b)
    left = review_atomic_memory_epoch(store, (a,))
    right = review_atomic_memory_epoch(store, (b,))
    with pytest.raises(MemorySchemaError, match="scope identity"):
        retained.review_retained_memory_epoch(left, right)


@pytest.mark.parametrize("mutation", (
    {"event_counts": (True,)},
    {"row_counts": (1.0,)},
    {"content_digest": ""},
))
def test_malformed_retained_review_denied(tmp_path, mutation):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    _put(store, scope)
    original = review_atomic_memory_epoch(store, (scope,))
    counterfeit = replace(original, **mutation)
    with pytest.raises(MemorySchemaError, match="invalid retained"):
        retained.review_retained_memory_epoch(original, counterfeit)


def test_reused_review_is_not_an_independent_observation(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    _put(store, scope)
    first = review_atomic_memory_epoch(store, (scope,))
    with pytest.raises(MemorySchemaError, match="two independent"):
        retained.review_retained_memory_epoch(first, first)


def test_constructed_result_cannot_grant_dispatch(tmp_path, monkeypatch):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    _put(store, scope)
    previous = review_atomic_memory_epoch(store, (scope,))
    current = review_atomic_memory_epoch(store, (scope,))
    monkeypatch.setattr(
        retained, "RetainedMemoryEpochComparison", lambda *args: object(),
    )
    with pytest.raises(MemorySchemaError, match="comparison result changed"):
        retained.review_retained_memory_epoch(previous, current)
