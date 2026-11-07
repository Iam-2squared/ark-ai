"""A transient SQLite setup callback must not retarget a Memory snapshot.

Only disposable local SQLite fixtures are used; the Memory v1 schema stays frozen.
"""

import sqlite3

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-user", "fixture")
    store.put(MemoryWrite(scope, "record-one", "synthetic only"))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), per_namespace_limit=1,
    )
    return store, request


@pytest.mark.parametrize("mutate_at", (1, 2, 3, 4))
def test_setup_callbacks_cannot_temporarily_retarget_snapshot(
    tmp_path, monkeypatch, mutate_at,
):
    store, request = _fixture(tmp_path)
    original_connect = sqlite3.connect
    opened = []
    expected_text = request.text

    class ReentrantConnection(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            index = getattr(self, "_review_sql_count", 0) + 1
            self._review_sql_count = index
            cursor = super().execute(sql, *args, **kwargs)
            if index == mutate_at:
                object.__setattr__(request, "text", "retargeted during setup")
            elif index == mutate_at + 1:
                # Before the fix a later SQLite callback could erase evidence
                # of the transient change before the next epoch assertion.
                object.__setattr__(request, "text", expected_text)
            return cursor

    def connecting(*args, **kwargs):
        if kwargs.get("uri") and "mode=ro" in str(args[0]):
            connection = original_connect(
                *args, **kwargs, factory=ReentrantConnection,
            )
            opened.append(connection)
            return connection
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(snapshot.sqlite3, "connect", connecting)
    with pytest.raises(MemorySchemaError, match="request changed during review"):
        snapshot.review_coherent_snapshot(store, request)

    assert len(opened) == 1
    assert opened[0]._review_sql_count == mutate_at
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        opened[0].execute("SELECT 1")


def test_unmodified_setup_still_returns_one_coherent_snapshot(tmp_path):
    store, request = _fixture(tmp_path)
    result = snapshot.review_coherent_snapshot(store, request)
    assert len(result.records) == 1
    assert result.records[0][0].source_id == "record-one"
    assert len(result.provenance_sha256) == 64
