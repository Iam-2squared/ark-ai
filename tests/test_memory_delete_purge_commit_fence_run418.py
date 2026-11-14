"""Post-COMMIT Memory deletion/expiry must never claim rollback or safe retry.

These fixtures use only local disposable SQLite. A late caller/source swap is
rejected after durable row+event effects, not turned into a second operation.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest

import ark.memory.sqlite_store as memory
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite


def _distinct_equal(value: str) -> str:
    other = ("!" + value)[1:]
    assert other == value and other is not value
    return other


@pytest.mark.parametrize("operation", ("delete", "purge"))
@pytest.mark.parametrize(
    "drift", ("path", "owner", "namespace", "equal_owner", "equal_namespace"),
)
def test_durable_delete_or_purge_refuses_late_carrier_drift(
    tmp_path, monkeypatch, operation, drift,
):
    db = tmp_path / "memory.sqlite"
    store = memory.SQLiteMemoryStore(db, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    record = store.put(MemoryWrite(
        scope, "fixture", "local-private-data", expires_at_ms=99,
    ))
    original_closing = memory.closing
    original_path = store.path
    mutated = []

    def change_after_commit():
        mutated.append(True)
        if drift == "path":
            store.path = Path(str(store.path))
            assert store.path is not original_path
        elif drift == "owner":
            object.__setattr__(scope, "owner_id", "different-owner")
        elif drift == "namespace":
            object.__setattr__(scope, "namespace", "different-namespace")
        elif drift == "equal_owner":
            object.__setattr__(
                scope, "owner_id", _distinct_equal(scope.owner_id),
            )
        else:
            object.__setattr__(
                scope, "namespace", _distinct_equal(scope.namespace),
            )

    @contextmanager
    def closing_after_sqlite_commit(connection):
        # The nested SQLite connection __exit__ has already committed when
        # the outer closing context resumes after yield.
        with original_closing(connection) as handle:
            yield handle
            change_after_commit()

    with monkeypatch.context() as patch:
        patch.setattr(memory, "closing", closing_after_sqlite_commit)
        with pytest.raises(MemorySchemaError, match="changed after commit"):
            if operation == "delete":
                store.delete(record.memory_id, scope, expected_revision=1)
            else:
                store.purge_expired(scope=scope)

    assert mutated == [True]
    with sqlite3.connect(db) as conn:
        assert conn.execute(
            "SELECT memory_id FROM memories",
        ).fetchall() == []
        rows = conn.execute(
            "SELECT operation, revision FROM memory_events ORDER BY event_id",
        ).fetchall()
    assert rows == [("create", 1), (operation if operation == "delete" else "expire", 1)]


@pytest.mark.parametrize("operation", ("delete", "purge"))
def test_unchanged_deletion_is_single_commit_and_event(tmp_path, operation):
    db = tmp_path / "memory.sqlite"
    store = memory.SQLiteMemoryStore(db, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    record = store.put(MemoryWrite(
        scope, "fixture", "local-private-data", expires_at_ms=99,
    ))
    if operation == "delete":
        assert store.delete(record.memory_id, scope, expected_revision=1) is True
    else:
        assert store.purge_expired(scope=scope) == 1
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0
        assert conn.execute(
            "SELECT operation FROM memory_events ORDER BY event_id",
        ).fetchall() == [("create",), (operation if operation == "delete" else "expire",)]
