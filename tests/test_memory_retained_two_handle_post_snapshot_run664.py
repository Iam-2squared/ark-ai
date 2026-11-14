"""Retained Memory row/event reconciliation uses one pre-commit WAL image.

The second handle changes real disposable SQLite rows after the reader's
snapshot opens. New commits must not leak into its earlier event prefix.
Neither consistency nor exact data matching proves a writer or consent.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix


@pytest.mark.parametrize(
    ("mutation", "extra_events"),
    (("target_update", 1), ("target_delete_recreate", 2), ("other_update", 1)),
)
def test_separate_writer_commit_after_first_row_cannot_mix_wal_images(
    tmp_path, monkeypatch, mutation, extra_events,
):
    path = tmp_path / "retained-coherent-two-handle.sqlite"
    scope = MemoryScope("local-owner", "private")
    initial_reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    target = initial_reader.put(MemoryWrite(scope, "target", "old target"))
    initial_reader.put(MemoryWrite(scope, "other", "old other"))
    retained = (
        capture_local_memory_event_prefix(initial_reader),
        review_memory_event_alignment(initial_reader),
    )
    baseline = coherent.review_retained_coherent_memory(initial_reader, *retained)
    assert (baseline.row_count, baseline.current_event_count) == (2, 2)

    second_handle = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    original_record = coherent._record
    fired = []

    def write_between_row_and_event_scan(row):
        record = original_record(row)
        if not fired:
            fired.append(mutation)
            if mutation == "target_update":
                changed = second_handle.put(
                    MemoryWrite(scope, "target", "new target"),
                    expected_revision=1,
                )
                assert changed.revision == 2
            elif mutation == "target_delete_recreate":
                assert second_handle.delete(
                    target.memory_id, scope, expected_revision=1,
                )
                replacement = second_handle.put(
                    MemoryWrite(scope, "target", "new target"),
                    expected_revision=0,
                )
                assert replacement.memory_id == target.memory_id
                assert replacement.revision == 1
            else:
                changed = second_handle.put(
                    MemoryWrite(scope, "other", "new other"),
                    expected_revision=1,
                )
                assert changed.revision == 2
        return record

    monkeypatch.setattr(coherent, "_record", write_between_row_and_event_scan)
    old_image = coherent.review_retained_coherent_memory(initial_reader, *retained)
    assert fired == [mutation]
    assert old_image == baseline
    assert old_image.action_authorized is False
    assert old_image.cross_store_atomicity_proven is False

    # A subsequent transaction sees the entire new event tail, never a
    # partial post-commit row image with its pre-commit event count.
    new_image = coherent.review_retained_coherent_memory(initial_reader, *retained)
    assert new_image.previous_event_count == 2
    assert new_image.current_event_count == 2 + extra_events
    assert new_image.row_count == 2
    assert new_image.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert new_image.current_event_sha256 != baseline.current_event_sha256
    assert new_image.review_sha256 != baseline.review_sha256
    assert new_image.independently_authenticated is False
    assert new_image.historical_writer_authenticated is False
    assert new_image.consent_verified is False
    assert new_image.memory_disclosure_authorized is False
