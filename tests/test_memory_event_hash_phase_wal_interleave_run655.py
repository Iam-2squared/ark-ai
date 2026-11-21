"""Memory event reconciliation cannot splice epochs at the first event hash.

A separate SQLite WAL writer commits after the reader has already scanned
the persisted rows and begun checking events. This is a diagnostic snapshot,
not writer authentication, consent, secure deletion, or action authorization.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_event_alignment as alignment
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("mutation", ("append_other", "update", "delete_recreate"))
def test_wal_commit_inside_event_hash_keeps_one_row_event_snapshot(
    tmp_path, monkeypatch, mutation,
):
    path = tmp_path / "event-phase-interleave.sqlite"
    scope = MemoryScope("private-owner", "private")
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    original = reader.put(MemoryWrite(scope, "source", "before"))
    baseline = alignment.review_memory_event_alignment(reader)
    assert (baseline.row_count, baseline.event_count, baseline.last_event_id) == (1, 1, 1)
    old_charge = alignment._charge
    event_callbacks = []

    def commit_during_event_charge(digest, entry):
        if entry[0] == "event" and not event_callbacks:
            event_callbacks.append(entry[1])
            if mutation == "append_other":
                writer.put(MemoryWrite(
                    MemoryScope("another-owner", "private"), "source", "separate",
                ))
            elif mutation == "update":
                updated = writer.put(
                    MemoryWrite(scope, "source", "after"),
                    expected_revision=original.revision,
                )
                assert updated.revision == 2
            else:
                assert writer.delete(
                    original.memory_id, scope, expected_revision=original.revision,
                )
                assert writer.put(
                    MemoryWrite(scope, "source", "new-lifetime"),
                ).revision == 1
        return old_charge(digest, entry)

    monkeypatch.setattr(alignment, "_charge", commit_during_event_charge)
    during = alignment.review_memory_event_alignment(reader)
    assert event_callbacks == [1]
    assert during == baseline
    assert during.user_consent_verified is False
    assert during.independently_authenticated is False
    assert during.action_authorized is False
    assert during.deletion_or_erasure_proven is False

    fresh = alignment.review_memory_event_alignment(reader)
    assert fresh.digest != baseline.digest
    assert fresh.last_event_id == (3 if mutation == "delete_recreate" else 2)
    assert fresh.event_count == (3 if mutation == "delete_recreate" else 2)
    assert fresh.row_count == (2 if mutation == "append_other" else 1)
    assert fresh.action_authorized is False
