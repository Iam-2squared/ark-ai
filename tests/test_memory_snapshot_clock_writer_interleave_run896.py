"""Single-clock, single-snapshot multi-scope Memory review during a WAL writer.

The clock callback commits synthetic changes after the reader's first
SELECT. Neither the read digest nor callback time grants consent/provenance.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)


@pytest.mark.parametrize("include_expired", (False, True))
def test_clock_callback_writer_cannot_mix_old_and_new_namespaces(
    tmp_path, include_expired,
):
    path = tmp_path / "snapshot-writer-clock.sqlite"
    notes = MemoryScope("synthetic-owner", "notes")
    private = MemoryScope("synthetic-owner", "private")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    for scope in (notes, private):
        original = writer.put(
            MemoryWrite(scope, "shared", "original", expires_at_ms=150),
            expected_revision=0,
        )
        assert original.revision == 1

    calls = []

    def clock_during_snapshot():
        calls.append("clock")
        later_writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
        for scope in (notes, private):
            refreshed = later_writer.put(
                MemoryWrite(scope, "shared", "refreshed"),
                expected_revision=1,
            )
            assert refreshed.revision == 2
        return 300

    reader = SQLiteMemoryStore(path, clock_ms=clock_during_snapshot)
    request = CoherentSnapshotRequest(
        "synthetic-owner", ("notes", "private"),
        include_expired=include_expired,
    )
    snapshot = review_coherent_snapshot(reader, request)
    assert calls == ["clock"]
    assert snapshot.read_at_ms == 300
    assert len(snapshot.records) == 2
    if include_expired:
        assert [[row.content for row in group] for group in snapshot.records] == [
            ["original"], ["original"],
        ]
        assert [[row.revision for row in group] for group in snapshot.records] == [
            [1], [1],
        ]
    else:
        assert snapshot.records == ((), ())
    assert len(snapshot.provenance_sha256) == 64

    cold_reader = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    cold = review_coherent_snapshot(cold_reader, request)
    assert [[row.content for row in group] for group in cold.records] == [
        ["refreshed"], ["refreshed"],
    ]
    assert [[row.revision for row in group] for group in cold.records] == [
        [2], [2],
    ]
    assert cold.provenance_sha256 != snapshot.provenance_sha256
