"""Memory event audits must not mix old rows with new WAL event suffixes.

One independent writer commits *during* the event scan, not just between
row and event scans. Results are local diagnostics, never writer provenance,
erasure evidence, context access or authorization to execute tools.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_event_alignment as alignment
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize(
    "mutation,expected_rows,expected_events",
    (
        ("other_scope_create", 2, 2),
        ("update", 1, 2),
        ("delete", 0, 2),
        ("delete_and_recreate", 1, 3),
    ),
)
def test_event_scan_keeps_one_wal_snapshot_across_writer_commit(
    tmp_path, monkeypatch, mutation, expected_rows, expected_events,
):
    path = tmp_path / "event-midscan.sqlite"
    scope = MemoryScope("owner-fixture", "private")
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    initial = reader.put(MemoryWrite(scope, "source-1", "private fixture content"))
    before = alignment.review_memory_event_alignment(reader)
    assert (before.row_count, before.event_count, before.last_event_id) == (1, 1, 1)

    original_charge = alignment._charge
    committed = []

    def commit_during_event(digest, entry):
        original_charge(digest, entry)
        if entry[0] != "event" or committed:
            return
        # This write uses a separately opened SQLite handle while the reader
        # holds its original read transaction and has already scanned rows.
        if mutation == "other_scope_create":
            writer.put(MemoryWrite(
                MemoryScope("other-fixture", "private"),
                "other-source", "unrelated private fixture",
            ))
        elif mutation == "update":
            writer.put(
                MemoryWrite(scope, "source-1", "new fixture contents"),
                expected_revision=initial.revision,
            )
        else:
            assert writer.delete(
                initial.memory_id, scope,
                expected_revision=initial.revision,
            )
            if mutation == "delete_and_recreate":
                recreated = writer.put(
                    MemoryWrite(scope, "source-1", "new lifetime"),
                )
                assert recreated.revision == 1
        committed.append(mutation)

    monkeypatch.setattr(alignment, "_charge", commit_during_event)
    during = alignment.review_memory_event_alignment(reader)
    assert committed == [mutation]
    assert during == before
    assert during.action_authorized is False
    assert during.deletion_or_erasure_proven is False
    assert "private fixture content" not in repr(during)

    fresh = alignment.review_memory_event_alignment(reader)
    assert fresh != before
    assert fresh.row_count == expected_rows
    assert fresh.event_count == expected_events
    assert fresh.last_event_id == expected_events
    assert fresh.digest != before.digest
    assert fresh.independently_authenticated is False
    assert fresh.user_consent_verified is False
