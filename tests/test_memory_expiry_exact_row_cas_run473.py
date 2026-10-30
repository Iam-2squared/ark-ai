"""Expiry deletion must fence the *selected row*, not just eligible age/revision.

The fault fixture modifies a row from the same SQLite write transaction. No
concurrent second writer or paid service is needed; this is detached testing.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError


class _ReentrantRowRewrite:
    def __init__(self, connection, target_id: str, column: str, replacement: object):
        self.connection = connection
        self.target_id = target_id
        self.column = column
        self.replacement = replacement
        self.injected = False

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, *args):
        return self.connection.__exit__(*args)

    def close(self):
        self.connection.close()

    def execute(self, statement, parameters=()):
        if statement.lstrip().startswith("DELETE FROM memories") and not self.injected:
            self.injected = True
            # column is fixed by the test, never untrusted runtime input.
            self.connection.execute(
                f"UPDATE memories SET {self.column}=? WHERE memory_id=?",
                (self.replacement, self.target_id),
            )
        return self.connection.execute(statement, parameters)


def _fixture(tmp_path, count=1):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    records = [
        store.put(
            MemoryWrite(
                scope, f"source-{i}", f"content-{i}",
                {"label": "original"}, expires_at_ms=900,
            )
        )
        for i in range(count)
    ]
    return store, scope, records


def _inject(monkeypatch, store, target, column, replacement):
    connect = store._connect
    seen = []

    def poisoned_connect(*, create=False):
        wrapper = _ReentrantRowRewrite(
            connect(create=create), target.memory_id, column, replacement,
        )
        seen.append(wrapper)
        return wrapper

    monkeypatch.setattr(store, "_connect", poisoned_connect)
    return seen


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("expires_at_ms", 950),
        ("content", "other-content"),
        ("metadata_json", '{"label":"changed"}'),
        ("updated_at_ms", 999),
        ("created_at_ms", 999),
        ("content_sha256", "a" * 64),
    ),
)
def test_bounded_purge_rejects_reentrant_same_revision_row_rewrite(
    tmp_path, monkeypatch, column, replacement,
):
    store, scope, (record,) = _fixture(tmp_path)
    seen = _inject(monkeypatch, store, record, column, replacement)

    with pytest.raises(MemoryConflictError, match="expired memory changed"):
        store.purge_expired(scope=scope, limit=1)

    assert seen and seen[0].injected
    unchanged = store.get(record.memory_id, scope, include_expired=True)
    assert unchanged == record
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_failure_on_second_row_rolls_back_first_delete_and_both_events(
    tmp_path, monkeypatch,
):
    store, scope, records = _fixture(tmp_path, count=2)
    target = max(records, key=lambda record: record.memory_id)
    seen = _inject(monkeypatch, store, target, "expires_at_ms", 950)

    with pytest.raises(MemoryConflictError, match="expired memory changed"):
        store.purge_expired(scope=scope, limit=2)

    assert seen and seen[0].injected
    assert all(
        store.get(record.memory_id, scope, include_expired=True) == record
        for record in records
    )
    assert [event.operation for event in store.events(scope)] == ["create", "create"]


def test_unmodified_bounded_purge_still_commits_corresponding_events(tmp_path):
    store, scope, records = _fixture(tmp_path, count=2)
    assert store.purge_expired(scope=scope, limit=2) == 2
    assert all(store.get(record.memory_id, scope, include_expired=True) is None
               for record in records)
    assert [event.operation for event in store.events(scope)].count("expire") == 2
