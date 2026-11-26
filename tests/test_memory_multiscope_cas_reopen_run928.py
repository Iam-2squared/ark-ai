"""Cross-scope SQLite Memory identity and CAS rejection survive a cold reopen.

All rows are synthetic. This checks local isolation and event durability only;
it does not attest privacy consent, remote provenance, or external actions.
"""

from __future__ import annotations

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


@pytest.mark.parametrize(
    ("other_owner", "other_namespace"),
    (
        ("second-owner", "private"),
        ("first-owner", "separate"),
    ),
)
def test_same_source_id_in_distinct_scope_cannot_cross_read_or_delete(
    tmp_path, other_owner: str, other_namespace: str,
):
    store = SQLiteMemoryStore(tmp_path / "scope-isolation.sqlite", clock_ms=lambda: 2000)
    protected = MemoryScope("first-owner", "private")
    other = MemoryScope(other_owner, other_namespace)
    private = store.put(MemoryWrite(protected, "same-source", "private-alpha"))
    unrelated = store.put(MemoryWrite(other, "same-source", "private-beta"))
    assert private.memory_id != unrelated.memory_id
    assert store.get(private.memory_id, other) is None
    assert store.get(unrelated.memory_id, protected) is None
    assert store.delete(private.memory_id, other, expected_revision=1) is False
    assert store.delete(unrelated.memory_id, protected, expected_revision=1) is False

    reopened = SQLiteMemoryStore(store.path, clock_ms=lambda: 2000)
    assert reopened.get(private.memory_id, protected).content == "private-alpha"
    assert reopened.get(unrelated.memory_id, other).content == "private-beta"
    assert [(event.operation, event.revision) for event in reopened.events(protected)] == [
        ("create", 1),
    ]
    assert [(event.operation, event.revision) for event in reopened.events(other)] == [
        ("create", 1),
    ]


def test_reopened_writer_invalidates_stale_update_and_delete_without_new_events(
    tmp_path,
):
    path = tmp_path / "cas-restart.sqlite"
    scope = MemoryScope("owner", "notes")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    created = first.put(MemoryWrite(scope, "source", "initial"))
    second = SQLiteMemoryStore(path, clock_ms=lambda: 1100)
    updated = second.put(
        MemoryWrite(scope, "source", "new-value"), expected_revision=1,
    )
    assert created.memory_id == updated.memory_id
    assert updated.revision == 2

    with pytest.raises(MemoryConflictError):
        first.put(MemoryWrite(scope, "source", "stale-update"), expected_revision=1)
    with pytest.raises(MemoryConflictError):
        first.delete(created.memory_id, scope, expected_revision=1)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    assert cold.get(created.memory_id, scope).content == "new-value"
    assert cold.get(created.memory_id, scope).revision == 2
    assert [(event.operation, event.revision) for event in cold.events(scope)] == [
        ("create", 1),
        ("update", 2),
    ]
