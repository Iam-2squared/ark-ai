"""Cross-scope WAL commits cannot splice retained Memory row/event epochs.

All stores and clocks are synthetic local fixtures. Even exact coherent
snapshots do not authenticate writer identity, user consent, or execution.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_row_delta_review import capture_local_memory_row_delta


@pytest.mark.parametrize(
    ("interleaving", "expected_rows", "expected_scopes", "expected_events"),
    (
        ("update_and_append", 3, 3, 4),
        ("delete_recreate", 2, 2, 4),
        ("append_disjoint_scope", 3, 3, 3),
    ),
)
def test_retained_row_event_snapshot_is_one_wal_epoch_across_scopes(
    tmp_path, monkeypatch, interleaving, expected_rows, expected_scopes,
    expected_events,
):
    path = tmp_path / "cross-scope-wal.sqlite"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    scope_a = MemoryScope("offline-owner", "private")
    scope_b = MemoryScope("offline-owner", "tasks")
    scope_c = MemoryScope("unrelated-owner", "private")
    reader.put(MemoryWrite(scope_a, "alpha", "private A"))
    second = reader.put(MemoryWrite(scope_b, "beta", "private B"))
    retained_prefix = capture_local_memory_event_prefix(reader)
    retained_alignment = review_memory_event_alignment(reader)
    retained_rows = capture_local_memory_row_delta(reader)
    original_commitment = coherent.row_delta._commitment
    fired = []

    def interleave_on_first_row(row):
        digest = original_commitment(row)
        if not fired:
            fired.append(interleaving)
            if interleaving == "update_and_append":
                writer.put(
                    MemoryWrite(scope_b, "beta", "new B"), expected_revision=1,
                )
                writer.put(MemoryWrite(scope_c, "gamma", "new C"))
            elif interleaving == "delete_recreate":
                assert writer.delete(
                    second.memory_id, scope_b, expected_revision=1,
                )
                replacement = writer.put(
                    MemoryWrite(scope_b, "beta", "second lifetime B"),
                    expected_revision=0,
                )
                assert replacement.memory_id == second.memory_id
                assert replacement.revision == 1
            else:
                writer.put(MemoryWrite(scope_c, "gamma", "new C"))
        return digest

    monkeypatch.setattr(coherent.row_delta, "_commitment", interleave_on_first_row)
    old = coherent.review_retained_coherent_memory(
        reader, retained_prefix, retained_alignment, prior_rows=retained_rows,
    )
    assert fired == [interleaving]
    assert (old.previous_event_count, old.current_event_count) == (2, 2)
    assert (old.row_count, old.scope_count, old.last_event_id) == (2, 2, 2)
    assert old.status == "UNCHANGED_LOCAL_HISTORY"
    assert old.retained_row_delta_checked is True

    new = coherent.review_retained_coherent_memory(
        reader, retained_prefix, retained_alignment, prior_rows=retained_rows,
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
    assert new.retained_row_delta_checked is True
    for report in (old, new):
        assert report.independently_authenticated is False
        assert report.historical_writer_authenticated is False
        assert report.consent_verified is False
        assert report.memory_disclosure_authorized is False
        assert report.action_authorized is False
        assert report.cross_store_atomicity_proven is False
