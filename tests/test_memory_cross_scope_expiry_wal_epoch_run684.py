"""A concurrent expiry transaction cannot splice two Memory WAL epochs.

Read-only retained row/event witness snapshots remain local and do not prove
the historical writer, consent, authenticated time or automatic retry rights.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_row_delta_review import capture_local_memory_row_delta


@pytest.mark.parametrize(
    ("change", "expected_events", "expected_rows", "expected_scopes"),
    (
        ("expire", 3, 1, 2),
        ("expire_recreate", 4, 2, 2),
        ("expire_append_other", 4, 2, 3),
    ),
)
def test_coherent_wal_read_does_not_mix_expiry_and_recreated_rows(
    tmp_path, monkeypatch, change, expected_events, expected_rows, expected_scopes,
):
    path = tmp_path / "memory-expiry-wal.sqlite"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    private = MemoryScope("fixture-owner", "private")
    tasks = MemoryScope("fixture-owner", "tasks")
    disjoint = MemoryScope("other-owner", "private")
    reader.put(MemoryWrite(private, "alpha", "expiring", expires_at_ms=1100))
    reader.put(MemoryWrite(tasks, "beta", "retained"))
    prefix = capture_local_memory_event_prefix(reader)
    alignment = review_memory_event_alignment(reader)
    rows = capture_local_memory_row_delta(reader)
    original = coherent.row_delta._commitment
    intervened: list[str] = []

    def first_row_commitment(row):
        digest = original(row)
        if not intervened:
            intervened.append(change)
            assert writer.purge_expired(scope=private) == 1
            if change == "expire_recreate":
                writer.put(MemoryWrite(private, "alpha", "new private lifetime"))
            elif change == "expire_append_other":
                writer.put(MemoryWrite(disjoint, "gamma", "new unrelated row"))
        return digest

    monkeypatch.setattr(coherent.row_delta, "_commitment", first_row_commitment)
    old = coherent.review_retained_coherent_memory(
        reader, prefix, alignment, prior_rows=rows,
    )
    assert intervened == [change]
    assert (old.previous_event_count, old.current_event_count) == (2, 2)
    assert (old.row_count, old.scope_count, old.last_event_id) == (2, 2, 2)
    assert old.status == "UNCHANGED_LOCAL_HISTORY"

    new = coherent.review_retained_coherent_memory(
        reader, prefix, alignment, prior_rows=rows,
    )
    assert (new.previous_event_count, new.current_event_count) == (
        2, expected_events,
    )
    assert (new.row_count, new.scope_count, new.last_event_id) == (
        expected_rows, expected_scopes, expected_events,
    )
    assert new.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert new.current_event_sha256 != old.current_event_sha256
    assert new.current_alignment_sha256 != old.current_alignment_sha256
    for report in (old, new):
        assert report.independently_authenticated is False
        assert report.historical_writer_authenticated is False
        assert report.consent_verified is False
        assert report.memory_disclosure_authorized is False
        assert report.action_authorized is False
        assert report.cross_store_atomicity_proven is False
