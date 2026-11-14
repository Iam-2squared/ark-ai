"""Memory manual COMMIT-UNKNOWN triage observes one SQLite WAL snapshot.

A separate handle commits between the triage row snapshot and subsequent
event scan. The old reader must not splice the new event tail into its old
row image. These diagnostic hashes do not authenticate actor or permission.
"""

import pytest

import ark.memory.postcommit_uncertainty_review as triage
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas


@pytest.mark.parametrize("write_kind", (
    "matching", "other_content", "delete_recreate",
))
def test_manual_triage_wal_writer_after_row_snapshot_is_coherent(
    tmp_path, monkeypatch, write_kind: str,
):
    path = tmp_path / "triage-wal.sqlite"
    scope = MemoryScope("local-owner", "private")
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    old = reader.put(
        MemoryWrite(scope, "same-source", "original"), expected_revision=0,
    )
    retained = observe_memory_generation_for_cas(reader, scope, "same-source")
    proposed = MemoryWrite(
        scope, "same-source", "target", metadata={"fixture": "yes"},
    )
    baseline = triage.review_uncertain_memory_commit(
        reader, proposed, retained_before=retained,
    )
    assert baseline.disposition == "LOCAL_UNCHANGED"
    original_hash = triage._row_hash
    writes = []

    def commit_after_row_snapshot(record):
        if not writes:
            writes.append(write_kind)
            if write_kind == "matching":
                writer.put(proposed, expected_revision=old.revision)
            elif write_kind == "other_content":
                writer.put(
                    MemoryWrite(scope, "same-source", "different"),
                    expected_revision=old.revision,
                )
            else:
                assert writer.delete(
                    old.memory_id, scope, expected_revision=old.revision,
                )
                writer.put(proposed, expected_revision=0)
        return original_hash(record)

    monkeypatch.setattr(triage, "_row_hash", commit_after_row_snapshot)
    during = triage.review_uncertain_memory_commit(
        reader, proposed, retained_before=retained,
    )
    assert writes == [write_kind]
    assert during == baseline
    assert during.automatic_retry_authorized is False
    assert during.write_authorized is False
    assert during.caller_attribution_proven is False
    assert during.trusted_clock_proven is False

    # On a *new* read-only snapshot, the observed history advances.
    fresh = triage.review_uncertain_memory_commit(
        reader, proposed, retained_before=retained,
    )
    assert fresh.observed_event_id > during.observed_event_id
    assert fresh.observed_prefix_sha256 != during.observed_prefix_sha256
    expected = (
        "ONE_MATCHING_UPDATE_VISIBLE"
        if write_kind == "matching" else "INDETERMINATE"
    )
    assert fresh.disposition == expected
    assert fresh.automatic_retry_authorized is False
    assert fresh.caller_attribution_proven is False
