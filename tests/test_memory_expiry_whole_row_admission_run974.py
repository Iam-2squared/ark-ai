"""A due row's identity/numeric fields must pass SQL admission before SELECT *.

Corrupt, temporary local v1 files only. This does not change legacy expiry
semantics, make a clock trusted, or authorize automatic retention changes.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_store as memory_module
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize(
    ("column", "corruption"),
    (
        ("memory_id", sqlite3.Binary(b"mem_" + b"f" * 64)),
        ("owner_id", sqlite3.Binary(b"synthetic-owner")),
        ("namespace", "x" * 1025),
        ("content_sha256", sqlite3.Binary(b"a" * 64)),
        ("created_at_ms", sqlite3.Binary(b"100")),
        ("updated_at_ms", 100.25),
        ("revision", sqlite3.Binary(b"1")),
    ),
    ids=(
        "memory-identity-blob", "owner-blob", "namespace-oversize",
        "digest-blob", "created-int-blob", "updated-real", "revision-blob",
    ),
)
def test_corrupt_due_row_denied_before_python_hydration(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
    column: str, corruption: object,
) -> None:
    path = tmp_path / "expiry-prehydration.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = store.put(
        MemoryWrite(scope, "source", "private fixture", expires_at_ms=150),
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (corruption, row.memory_id),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 200)

    def forbidden_hydration(_row: object) -> None:
        pytest.fail("corrupted due row reached private Python hydration")

    with monkeypatch.context() as patch:
        patch.setattr(memory_module, "_record", forbidden_hydration)
        with pytest.raises(
            MemorySchemaError, match="memory expiry page hydration admission failed",
        ):
            reopened.purge_expired(limit=1)

    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)
        assert conn.execute(
            "SELECT operation FROM memory_events ORDER BY event_id",
        ).fetchall() == [("create",)]


def test_bounded_scope_stays_isolated_from_corrupt_other_scope(tmp_path) -> None:
    path = tmp_path / "scope-expiry.sqlite"
    good_scope = MemoryScope("synthetic-owner", "good")
    bad_scope = MemoryScope("synthetic-owner", "bad")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    good = store.put(
        MemoryWrite(good_scope, "source", "safe", expires_at_ms=150),
    )
    bad = store.put(
        MemoryWrite(bad_scope, "source", "corrupt", expires_at_ms=150),
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET content_sha256=? WHERE memory_id=?",
            (sqlite3.Binary(b"f" * 64), bad.memory_id),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert reopened.purge_expired(scope=good_scope, limit=1) == 1
    with pytest.raises(
        MemorySchemaError, match="memory expiry page hydration admission failed",
    ):
        reopened.purge_expired(scope=bad_scope, limit=1)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT memory_id FROM memories",
        ).fetchall() == [(bad.memory_id,)]
        assert conn.execute(
            "SELECT operation FROM memory_events ORDER BY event_id",
        ).fetchall() == [("create",), ("create",), ("expire",)]
    assert good.memory_id != bad.memory_id
