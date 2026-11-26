"""A clock callback committing to WAL cannot splice two Memory snapshots.

This exercises the real SQLite read transaction with a second local writer.
No network, connector, authorization, or real user data is involved.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize(
    "namespaces",
    [("private", "tasks"), ("tasks", "private")],
)
def test_concurrent_wal_writer_during_clock_cannot_mix_namespace_eras(
    tmp_path, namespaces,
):
    path = tmp_path / "snapshot # private %.sqlite"
    write_time = {"value": 10}
    writer = SQLiteMemoryStore(path, clock_ms=lambda: write_time["value"])
    scopes = {
        name: MemoryScope("local-person", name) for name in namespaces
    }
    originals = {
        name: writer.put(MemoryWrite(scopes[name], "source", "old " + name))
        for name in namespaces
    }
    callback = {"armed": False, "fired": False, "samples": 0}

    def snapshot_clock():
        callback["samples"] += 1
        if callback["armed"] and not callback["fired"]:
            # This executes after the reader's BEGIN and initial schema
            # SELECT. In WAL mode the writer can commit even while the reader
            # keeps its pre-write transaction open.
            callback["fired"] = True
            write_time["value"] = 20
            for name in namespaces:
                updated = writer.put(
                    MemoryWrite(scopes[name], "source", "new " + name),
                    expected_revision=1,
                )
                assert updated.revision == 2
        return 30

    reader = SQLiteMemoryStore(path, clock_ms=snapshot_clock)
    request = CoherentSnapshotRequest(
        "local-person", namespaces, per_namespace_limit=2,
    )
    callback["armed"] = True
    old_view = review_coherent_snapshot(reader, request)
    assert callback["fired"]
    assert callback["samples"] == 1
    assert old_view.read_at_ms == 30
    assert tuple(scope.namespace for scope in old_view.scopes) == namespaces
    assert tuple(
        records[0].content for records in old_view.records
    ) == tuple("old " + name for name in namespaces)
    assert all(len(records) == 1 for records in old_view.records)
    assert tuple(
        records[0].revision for records in old_view.records
    ) == (1, 1)
    assert tuple(
        records[0].memory_id for records in old_view.records
    ) == tuple(originals[name].memory_id for name in namespaces)

    new_view = review_coherent_snapshot(reader, request)
    assert callback["samples"] == 2
    assert tuple(
        records[0].content for records in new_view.records
    ) == tuple("new " + name for name in namespaces)
    assert tuple(
        records[0].revision for records in new_view.records
    ) == (2, 2)
    assert old_view.provenance_sha256 != new_view.provenance_sha256
    assert review_memory_event_alignment(reader).event_count == 4
