"""A Memory ABA diagnostic cannot trust the first of duplicate SQLite markers.

All fixtures are local, synthetic, content-minimized and read-only in review.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.cas_generation_review import (
    MemoryGenerationReviewRejected,
    review_memory_revision_reuse,
)


@pytest.mark.parametrize("observed", ("current", "foreign", "missing_source"))
def test_memory_generation_review_denies_duplicate_global_highwater(
    tmp_path, observed,
):
    store = SQLiteMemoryStore(
        tmp_path / "aba.sqlite", clock_ms=lambda: 1000,
    )
    owner = MemoryScope("owner", "notes")
    foreign = MemoryScope("foreign", "notes")
    if observed == "current":
        store.put(MemoryWrite(owner, "source", "local private value"))
    else:
        store.put(MemoryWrite(foreign, "foreign-source", "foreign private value"))
    source = "never-existed" if observed == "missing_source" else "source"
    initial = review_memory_revision_reuse(
        store, owner, source, expected_revision=1,
    )
    assert initial.write_authorized is False
    assert initial.erase_authorized is False
    with sqlite3.connect(store.path) as conn:
        last = conn.execute(
            "SELECT MAX(event_id) FROM memory_events",
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)",
            ("memory_events", last),
        )
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0] == 2

    with pytest.raises(
        MemoryGenerationReviewRejected, match="global event high-water",
    ):
        review_memory_revision_reuse(
            store, owner, source, expected_revision=1,
        )
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0] == 2
