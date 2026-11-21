"""A retained local Memory event prefix remains scope- and file-specific.

Two SQLite handles and disposable files simulate post-COMMIT observations;
this evidence cannot identify a writer, authorize read access, or retry writes.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixRejected,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)


def _handles(path):
    return (
        SQLiteMemoryStore(path, clock_ms=lambda: 1200),
        SQLiteMemoryStore(path, clock_ms=lambda: 1300),
    )


@pytest.mark.parametrize("owner", ("offline-owner", "日本語"))
def test_other_handle_appends_without_authenticating_writer(tmp_path, owner):
    first, second = _handles(tmp_path / "shared.sqlite")
    own = MemoryScope(owner, "private")
    other = MemoryScope("other-owner", "separate")
    first.put(MemoryWrite(own, "source", "not for disclosure"))
    retained = capture_local_memory_event_prefix(first)
    second.put(MemoryWrite(other, "source", "independent writer"))
    with sqlite3.connect(first.path) as conn:
        before = tuple(conn.iterdump())

    result = compare_local_memory_event_prefix(first, retained)
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.historical_writer_authenticated is False
    assert result.independent_witness_custody_proven is False
    assert result.memory_disclosure_authorized is False
    assert result.action_authorized is False
    with sqlite3.connect(first.path) as conn:
        assert tuple(conn.iterdump()) == before


def test_historical_event_rewrite_rejected_despite_new_valid_append(tmp_path):
    first, second = _handles(tmp_path / "tampered.sqlite")
    scope = MemoryScope("owner", "private")
    first.put(MemoryWrite(scope, "first", "private"))
    retained = capture_local_memory_event_prefix(first)
    second.put(MemoryWrite(scope, "second", "private"))
    with sqlite3.connect(first.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=occurred_at_ms + 1 "
            "WHERE event_id=1"
        )
    # The current tail is locally well-formed, but the retained original
    # prefix no longer matches. A later append must not mask this rewrite.
    assert capture_local_memory_event_prefix(second).event_count == 2
    with pytest.raises(
        MemoryEventPrefixRejected,
        match="retained event prefix changed",
    ):
        compare_local_memory_event_prefix(first, retained)


def test_foreign_database_same_length_witness_is_not_transferable(tmp_path):
    first, _ = _handles(tmp_path / "first.sqlite")
    other, _ = _handles(tmp_path / "other.sqlite")
    first.put(MemoryWrite(MemoryScope("owner-a"), "source", "private a"))
    other.put(MemoryWrite(MemoryScope("owner-b"), "source", "private b"))
    retained = capture_local_memory_event_prefix(first)
    assert capture_local_memory_event_prefix(other).event_count == 1
    with pytest.raises(
        MemoryEventPrefixRejected,
        match="retained event prefix changed",
    ):
        compare_local_memory_event_prefix(other, retained)
