"""Cross-namespace Memory witness and SQLite callback custody checks.

All probes use disposable local SQLite; no schema changes or data disclosure.
"""

from dataclasses import replace
from pathlib import Path

import pytest

import ark.memory.synthetic_multiscope_integrity_review as review
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "mem.sqlite", clock_ms=lambda: 120)
    scopes = (MemoryScope("local-owner", "alpha"), MemoryScope("local-owner", "beta"))
    store.put(MemoryWrite(scopes[0], "fixture-source", "local-fixture"))
    return store, scopes


@pytest.mark.parametrize("phase", ("connect", "validate", "record", "event_hash"))
def test_mutating_scope_at_each_sqlite_callback_is_rejected(
    tmp_path, monkeypatch, phase,
):
    store, scopes = _fixture(tmp_path)
    if phase == "connect":
        original = store._connect_readonly

        def altered():
            conn = original()
            store.path = Path(str(store.path))
            return conn

        monkeypatch.setattr(store, "_connect_readonly", altered)
    elif phase == "validate":
        original = review._validate_v1_schema

        def altered(conn):
            result = original(conn)
            object.__setattr__(scopes[0], "namespace", "changed")
            return result

        monkeypatch.setattr(review, "_validate_v1_schema", altered)
    elif phase == "record":
        original = review._record

        def altered(row):
            result = original(row)
            object.__setattr__(scopes[0], "namespace", "changed")
            return result

        monkeypatch.setattr(review, "_record", altered)
    else:
        original = review._hash

        def altered(label, value):
            result = original(label, value)
            if label == "ARK-synthetic-memory-event-v1":
                object.__setattr__(scopes[0], "namespace", "changed")
            return result

        monkeypatch.setattr(review, "_hash", altered)

    with pytest.raises(
        review.SyntheticMemorySnapshotRejected,
        match="scope or source changed",
    ):
        review.review_synthetic_memory_scopes(store, scopes)


def test_equal_valued_retained_event_replacement_rejected(tmp_path, monkeypatch):
    store, scopes = _fixture(tmp_path)
    previous = review.review_synthetic_memory_scopes(store, scopes)
    retained = tuple(item.events for item in previous.scopes)
    original = review._record

    def altered(row):
        hydrated = original(row)
        event = retained[0]
        cloned = event.tail_hash[:20] + event.tail_hash[20:]
        assert cloned == event.tail_hash and cloned is not event.tail_hash
        object.__setattr__(event, "tail_hash", cloned)
        return hydrated

    monkeypatch.setattr(review, "_record", altered)
    with pytest.raises(
        review.SyntheticMemorySnapshotRejected,
        match="retained Memory event witness changed",
    ):
        review.review_synthetic_memory_scopes(store, scopes, retained_events=retained)


def test_equal_valued_cached_event_rebinding_rejected(tmp_path, monkeypatch):
    store, scopes = _fixture(tmp_path)
    cached = review.review_synthetic_memory_scopes(store, scopes)
    original = review._row_hash

    def altered(record):
        result = original(record)
        item = cached.scopes[0]
        object.__setattr__(item, "events", replace(item.events))
        return result

    monkeypatch.setattr(review, "_row_hash", altered)
    with pytest.raises(
        review.SyntheticMemorySnapshotRejected,
        match="retained exact Memory snapshot changed",
    ):
        review.review_synthetic_memory_scopes(
            store, scopes, require_same_snapshot=cached,
        )


def test_final_snapshot_digest_does_not_hide_path_replacement(tmp_path, monkeypatch):
    store, scopes = _fixture(tmp_path)
    original = review._hash

    def altered(label, value):
        result = original(label, value)
        if label == "ARK-synthetic-memory-multiscope-v1":
            store.path = Path(str(store.path))
        return result

    monkeypatch.setattr(review, "_hash", altered)
    with pytest.raises(
        review.SyntheticMemorySnapshotRejected,
        match="scope or source changed",
    ):
        review.review_synthetic_memory_scopes(store, scopes)


def test_unmodified_cross_namespace_witness_stays_deterministic(tmp_path):
    store, scopes = _fixture(tmp_path)
    first = review.review_synthetic_memory_scopes(store, scopes)
    next_snapshot = review.review_synthetic_memory_scopes(
        store, scopes, require_same_snapshot=first,
    )
    assert next_snapshot == first
    assert not next_snapshot.context_use_authorized
    assert not next_snapshot.external_disclosure_authorized
