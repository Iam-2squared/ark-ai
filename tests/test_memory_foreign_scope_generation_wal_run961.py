"""Run961: foreign-scoped ABA cannot invalidate an unrelated Memory lifetime.

Disposable SQLite WAL and synthetic scopes only; generation tokens are not
consent, a real authorization, or independently authenticated provenance.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("foreign_kind", ("other-owner", "other-namespace"))
@pytest.mark.parametrize("replacement", ("same", "changed"))
@pytest.mark.parametrize("query_only", (False, True))
def test_unrelated_generation_survives_foreign_delete_recreate_wal_snapshot(
    tmp_path, foreign_kind: str, replacement: str, query_only: bool,
) -> None:
    path = tmp_path / "foreign-aba.sqlite3"
    primary = MemoryScope("owner-A", "private")
    foreign = (
        MemoryScope("owner-B", "private")
        if foreign_kind == "other-owner"
        else MemoryScope("owner-A", "other")
    )
    initial_a = SQLiteMemoryStore(path, clock_ms=lambda: 100).put(
        MemoryWrite(primary, "shared-source", "primary-before"),
    )
    initial_b = SQLiteMemoryStore(path, clock_ms=lambda: 101).put(
        MemoryWrite(foreign, "shared-source", "foreign-before"),
    )
    assert initial_a.memory_id != initial_b.memory_id
    token_a = observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 102), primary, "shared-source",
    )
    token_b = observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 102), foreign, "shared-source",
    )
    assert (token_a.create_event_id, token_b.create_event_id) == (1, 2)

    with closing(sqlite3.connect(path, isolation_level=None, timeout=5)) as reader:
        if query_only:
            reader.execute("PRAGMA query_only=ON")
        reader.execute("BEGIN")
        assert reader.execute(
            "SELECT memory_id,content FROM memories ORDER BY memory_id"
        ).fetchall() == sorted([
            (initial_a.memory_id, "primary-before"),
            (initial_b.memory_id, "foreign-before"),
        ])

        assert SQLiteMemoryStore(path, clock_ms=lambda: 110).delete(
            initial_b.memory_id, foreign, expected_revision=1,
        )
        recreated = SQLiteMemoryStore(path, clock_ms=lambda: 120).put(
            MemoryWrite(
                foreign, "shared-source",
                "foreign-before" if replacement == "same" else "foreign-after",
            ),
        )
        assert recreated.memory_id == initial_b.memory_id
        assert recreated.revision == 1
        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                SQLiteMemoryStore(path, clock_ms=lambda: 130),
                MemoryWrite(foreign, "shared-source", "foreign-replay-denied"),
                retained=token_b,
            )

        # Foreign events must not accidentally revoke a still-current
        # *different* lifetime. All write/event comparisons are inside the
        # independent writer's own SQLite transaction, never this reader.
        updated = generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 140),
            MemoryWrite(primary, "shared-source", "primary-after"),
            retained=token_a,
        )
        assert updated.revision == 2
        assert updated.content == "primary-after"
        assert reader.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (initial_a.memory_id,),
        ).fetchone() == ("primary-before", 1)
        reader.execute("ROLLBACK")

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 150)
    assert cold.get(initial_a.memory_id, primary).content == "primary-after"
    assert cold.get(initial_b.memory_id, foreign).content == (
        "foreign-before" if replacement == "same" else "foreign-after"
    )
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            "SELECT event_id,owner_id,namespace,operation,revision "
            "FROM memory_events ORDER BY event_id"
        ).fetchall() == [
            (1, primary.owner_id, primary.namespace, "create", 1),
            (2, foreign.owner_id, foreign.namespace, "create", 1),
            (3, foreign.owner_id, foreign.namespace, "delete", 1),
            (4, foreign.owner_id, foreign.namespace, "create", 1),
            (5, primary.owner_id, primary.namespace, "update", 2),
        ]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert token_a.external_action_authorized is False
    assert token_a.consent_authenticated is False
