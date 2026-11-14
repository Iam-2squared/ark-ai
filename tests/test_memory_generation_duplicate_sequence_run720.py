"""Generation CAS rejects duplicate SQLite event high-water rows.

These disposable fixtures are not independently authenticated evidence.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "duplicate-sequence.sqlite", clock_ms=lambda: 1000,
    )
    primary_scope = MemoryScope("primary-owner", "private")
    foreign_scope = MemoryScope("other-owner", "private")
    primary = store.put(MemoryWrite(primary_scope, "primary", "original"))
    store.put(MemoryWrite(foreign_scope, "foreign", "foreign content"))
    token = cas.observe_memory_generation_for_cas(store, primary_scope, "primary")
    return store, primary_scope, foreign_scope, primary, token


@pytest.mark.parametrize("forged_seq", (0, 2, 99))
def test_duplicate_memory_sequence_refuses_read_and_write_without_mutation(
    tmp_path, forged_seq,
):
    store, scope, _foreign, primary, token = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        original = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchall()
        assert original == [(2,)]
        conn.execute(
            "INSERT INTO sqlite_sequence(name, seq) VALUES('memory_events', ?)",
            (forged_seq,),
        )

    with pytest.raises(cas.MemoryGenerationCASRejected, match="high-water"):
        cas.observe_memory_generation_for_cas(store, scope, "primary")
    with pytest.raises(cas.MemoryGenerationCASRejected, match="high-water"):
        cas.generation_fenced_memory_update(
            store, MemoryWrite(scope, "primary", "must not commit"), retained=token,
        )

    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT revision,content FROM memories WHERE memory_id=?",
            (primary.memory_id,),
        ).fetchone() == (1, "original")
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone() == (2,)
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchall() == [(2,), (forged_seq,)]


def test_valid_foreign_owner_append_remains_compatible_with_generation_cas(tmp_path):
    store, scope, foreign, primary, token = _fixture(tmp_path)
    store.put(MemoryWrite(foreign, "second", "unrelated"))
    updated = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "primary", "properly updated"), retained=token,
    )
    assert updated.memory_id == primary.memory_id
    assert updated.revision == 2
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchall() == [(4,)]
