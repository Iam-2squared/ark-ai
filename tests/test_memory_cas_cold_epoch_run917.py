"""Cold cross-handle Memory CAS and revision reuse remain distinguishable.

All rows are disposable synthetic data; a matching numeric revision is not
independent retention, deletion authority or authenticated provenance.
"""

from __future__ import annotations

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.cas_generation_review import review_memory_revision_reuse


@pytest.mark.parametrize("stale_operation", ("update", "delete"))
def test_cold_handle_rejects_stale_cas_without_appending_event(
    tmp_path, stale_operation,
):
    path = tmp_path / "memory-cas-cold.sqlite"
    scope = MemoryScope("fixture-owner", "offline")
    old = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    created = old.put(MemoryWrite(scope, "source", "version-one"))
    stale_revision = created.revision
    current = SQLiteMemoryStore(path, clock_ms=lambda: 2_000)
    updated = current.put(
        MemoryWrite(scope, "source", "version-two"),
        expected_revision=stale_revision,
    )
    assert updated.revision == stale_revision + 1
    before = tuple(current.events(scope))
    with pytest.raises(MemoryConflictError):
        if stale_operation == "update":
            old.put(
                MemoryWrite(scope, "source", "stale-write"),
                expected_revision=stale_revision,
            )
        else:
            old.delete(
                created.memory_id, scope, expected_revision=stale_revision,
            )
    after = tuple(SQLiteMemoryStore(path, clock_ms=lambda: 3_000).events(scope))
    assert after == before
    assert [event.operation for event in after] == ["create", "update"]
    assert current.get(created.memory_id, scope).content == "version-two"


@pytest.mark.parametrize("expected_revision", (0, 1))
def test_generation_reuse_is_reported_without_authorizing_cas(
    tmp_path, expected_revision,
):
    path = tmp_path / "memory-cas-aba.sqlite"
    scope = MemoryScope("fixture-owner", "offline")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    created = first.put(MemoryWrite(scope, "source", "first"))
    assert first.delete(created.memory_id, scope, expected_revision=1)
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 2_000)
    recreated = cold.put(MemoryWrite(scope, "source", "second"))
    assert recreated.memory_id == created.memory_id
    assert recreated.revision == 1

    reviewed = review_memory_revision_reuse(
        SQLiteMemoryStore(path, clock_ms=lambda: 3_000),
        scope, "source", expected_revision=expected_revision,
    )
    assert reviewed.generation_count == 2
    assert reviewed.event_count == 3
    assert reviewed.live_revision == 1
    assert reviewed.revision_reuse_possible is (expected_revision == 1)
    assert reviewed.write_authorized is False
    assert reviewed.erase_authorized is False
    assert reviewed.generation_authenticated is False
