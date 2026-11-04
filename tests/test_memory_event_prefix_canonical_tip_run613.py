"""Retained Memory event witness must be a dense v1 ID prefix.

All SQLite state is disposable; a local prefix cannot authenticate a writer,
grant disclosure, or release an ambiguous operation for retry.
"""

from dataclasses import replace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_prefix_review as prefix


@pytest.mark.parametrize(
    ("event_count", "last_event_id"),
    ((0, 1), (1, 2), (2, 3), (2, 1), (0, 7), (3, 2)),
)
def test_noncanonical_witness_rejected_before_database_scan(
    tmp_path, monkeypatch, event_count, last_event_id,
):
    store = SQLiteMemoryStore(
        tmp_path / "prefix-local.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("owner", "local")
    store.put(MemoryWrite(scope, "one", "private fixture"))
    witness = prefix.capture_local_memory_event_prefix(store)
    modified = replace(
        witness, event_count=event_count, last_event_id=last_event_id,
    )

    def forbidden_scan(*args, **kwargs):
        pytest.fail("invalid retained prefix must fail before any scan")

    monkeypatch.setattr(prefix, "_scan", forbidden_scan)
    with pytest.raises(prefix.MemoryEventPrefixRejected, match="prefix shape"):
        prefix.compare_local_memory_event_prefix(store, modified)


def test_empty_genesis_and_dense_append_still_compare(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "valid-prefix.sqlite", clock_ms=lambda: 1000,
    )
    genesis = prefix.capture_local_memory_event_prefix(store)
    assert genesis.event_count == genesis.last_event_id == 0
    scope = MemoryScope("owner", "local")
    store.put(MemoryWrite(scope, "one", "private fixture 1"))
    first = prefix.capture_local_memory_event_prefix(store)
    assert first.event_count == first.last_event_id == 1
    store.put(MemoryWrite(scope, "two", "private fixture 2"))
    report = prefix.compare_local_memory_event_prefix(store, first)
    assert report.previous_event_count == 1
    assert report.current_event_count == 2
    assert report.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    empty_report = prefix.compare_local_memory_event_prefix(store, genesis)
    assert empty_report.previous_event_count == 0
    assert empty_report.current_event_count == 2
    assert empty_report.memory_disclosure_authorized is False
    assert empty_report.action_authorized is False
