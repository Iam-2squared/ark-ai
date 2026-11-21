"""One SQLite read epoch across multiple private Memory namespaces.

A callback commits another process/handle's WAL changes after the reader's
BEGIN was anchored. These are disposable local fixtures, never consent or
permission to disclose data outside the selected owner.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)


@pytest.mark.parametrize("concurrent", ["update", "delete_create", "other_owner"])
def test_coherent_memory_ignores_wal_commits_after_snapshot_anchor(
    tmp_path: Path,
    concurrent: str,
) -> None:
    path = tmp_path / "memory-coherent.sqlite"
    private = MemoryScope("fixture-owner", "private")
    work = MemoryScope("fixture-owner", "work")
    other = MemoryScope("different-owner", "private")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 120)
    old_private = writer.put(MemoryWrite(private, "private-src", "before-private"))
    old_work = writer.put(MemoryWrite(work, "work-src", "before-work"))
    other_row = writer.put(MemoryWrite(other, "other-src", "other-secret"))
    changed = False

    def concurrent_clock() -> int:
        nonlocal changed
        if not changed:
            changed = True
            if concurrent == "update":
                writer.put(
                    MemoryWrite(private, "private-src", "after-private"),
                    expected_revision=old_private.revision,
                )
                writer.put(
                    MemoryWrite(work, "work-src", "after-work"),
                    expected_revision=old_work.revision,
                )
            elif concurrent == "delete_create":
                assert writer.delete(
                    old_private.memory_id, private,
                    expected_revision=old_private.revision,
                )
                writer.put(MemoryWrite(work, "new-src", "new-work"))
            else:
                writer.put(
                    MemoryWrite(other, "other-src", "changed-other-secret"),
                    expected_revision=other_row.revision,
                )
        return 500

    reader = SQLiteMemoryStore(path, clock_ms=concurrent_clock)
    request = CoherentSnapshotRequest(
        "fixture-owner", ("private", "work"), per_namespace_limit=10,
    )
    old = review_coherent_snapshot(reader, request)
    assert changed is True
    assert old.read_at_ms == 500
    assert old.scopes == (private, work)
    assert [r.content for r in old.records[0]] == ["before-private"]
    assert [r.content for r in old.records[1]] == ["before-work"]
    assert all(
        r.scope.owner_id == "fixture-owner"
        for group in old.records for r in group
    )
    assert all(
        r.content not in {"other-secret", "changed-other-secret"}
        for group in old.records for r in group
    )
    # A subsequent fresh snapshot sees the writer's completed mutations,
    # never a mixture from the old snapshot's two SELECTs.
    newer = review_coherent_snapshot(reader, request)
    if concurrent == "update":
        assert [r.content for r in newer.records[0]] == ["after-private"]
        assert [r.content for r in newer.records[1]] == ["after-work"]
    elif concurrent == "delete_create":
        assert newer.records[0] == ()
        assert {r.content for r in newer.records[1]} == {
            "before-work", "new-work",
        }
    else:
        assert [r.content for r in newer.records[0]] == ["before-private"]
        assert [r.content for r in newer.records[1]] == ["before-work"]
    if concurrent != "other_owner":
        assert old.provenance_sha256 != newer.provenance_sha256
