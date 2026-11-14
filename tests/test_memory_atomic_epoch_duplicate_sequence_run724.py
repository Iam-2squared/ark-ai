"""Atomic Memory epoch refuses ambiguous AUTOINCREMENT markers.

Synthetic local SQLite only; global high-water checks cannot authenticate
writers or prove provenance, even when the observed snapshots are coherent.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.atomic_epoch_review import review_atomic_memory_epoch
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize("layout", ("selected", "foreign", "both"))
def test_duplicated_event_sequence_refuses_atomic_epoch(
    tmp_path, layout,
):
    store = SQLiteMemoryStore(
        tmp_path / "atomic-epoch.sqlite", clock_ms=lambda: 1000,
    )
    selected = MemoryScope("owner", "a")
    foreign = MemoryScope("another-owner", "a")
    if layout in ("selected", "both"):
        store.put(MemoryWrite(selected, "one", "private local text"))
    if layout in ("foreign", "both"):
        store.put(MemoryWrite(foreign, "two", "private foreign text"))
    before = review_atomic_memory_epoch(store, (selected,))
    assert before.memory_disclosure_authorized is False
    assert before.dispatch_authorized is False

    with sqlite3.connect(store.path) as conn:
        highwater = conn.execute(
            "SELECT MAX(event_id) FROM memory_events",
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)",
            ("memory_events", highwater),
        )
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0] == 2

    with pytest.raises(MemorySchemaError, match="global event high-water"):
        review_atomic_memory_epoch(store, (selected,))
    with sqlite3.connect(store.path) as conn:
        # The read-only rejection must not attempt a destructive repair.
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0] == 2
