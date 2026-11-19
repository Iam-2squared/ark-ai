"""Memory lifetime review bounds forged sequence reads and hidden identities.

Synthetic SQLite only; this is no consent, trusted-clock or write authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
    cas_generation_review as review,
)


_HIDDEN = (
    "\x00", "\n", "\x7f", "\x85", "\u00ad", "\u034f",
    "\u061c", "\u200b", "\u200d", "\u2028", "\u202e",
    "\u2066", "\u206f", "\ufeff",
)


@pytest.mark.parametrize("control", _HIDDEN)
@pytest.mark.parametrize("field", ("owner_id", "namespace", "source_id"))
def test_generation_review_denies_hidden_identity_before_database_path(
    control: str, field: str,
) -> None:
    # An uninitialized exact store has no path: a missing admission fails
    # distinctly rather than reading a private SQLite database.
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("synthetic-owner", "private")
    source = "synthetic-source"
    if field == "source_id":
        source += control + "suffix"
    else:
        object.__setattr__(scope, field, getattr(scope, field) + control + "suffix")
    with pytest.raises(
        review.MemoryGenerationReviewRejected, match="bounded UTF-8",
    ):
        review.review_memory_revision_reuse(
            store, scope, source, expected_revision=1,
        )


def test_generation_review_multilingual_identity_remains_admissible() -> None:
    assert review._strict_utf8_identity("東京の所有者", 256)
    assert review._strict_utf8_identity("個人の記録", 256)
    assert review._strict_utf8_identity("記憶-端末-大阪", 512)


def test_duplicate_sqlite_sequence_marker_probe_is_bounded(tmp_path, monkeypatch):
    path = tmp_path / "memory-generation-review.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "source", "synthetic-only"), expected_revision=0)

    # sqlite_sequence has no UNIQUE constraint on its name. Forged copies
    # must fail without fetching the entire attacker-controlled marker set.
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO sqlite_sequence(name, seq) VALUES(?, ?)",
            [("memory_events", 1)] * 1500,
        )

    sql: list[str] = []
    original = SQLiteMemoryStore._connect_readonly

    def traced_connect(self):
        conn = original(self)
        conn.set_trace_callback(sql.append)
        return conn

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", traced_connect)
    with pytest.raises(
        review.MemoryGenerationReviewRejected, match="high-water",
    ):
        review.review_memory_revision_reuse(
            store, scope, "source", expected_revision=1,
        )
    probes = [
        statement.upper() for statement in sql
        if "FROM SQLITE_SEQUENCE" in statement.upper()
    ]
    assert len(probes) == 1
    assert "LIMIT 2" in probes[0]
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone()[0] == 1501
