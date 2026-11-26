"""Run966: global Memory event high-water is a bounded diagnostic check.

No private content leaves disposable SQLite. A local sequence marker neither
authenticates event provenance nor justifies automatic retry of an uncertain CAS.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as outcome


@pytest.mark.parametrize("case", (
    "duplicate",
    "missing",
    "regressed",
    "oversized-blob",
))
def test_global_sequence_marker_quarantined_without_row_event_mutation(
    tmp_path, case: str,
) -> None:
    path = tmp_path / "sequence.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("owner", "private")
    record = store.put(MemoryWrite(scope, "source", "fixture"))
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchall() == [(1,)]
        outcome._check_global_memory_event_highwater(conn)
        if case == "duplicate":
            conn.execute(
                "INSERT INTO sqlite_sequence(name, seq) VALUES (?,?)",
                ("memory_events", 1),
            )
        elif case == "missing":
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='memory_events'",
            )
        elif case == "regressed":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=0 WHERE name='memory_events'",
            )
        else:
            conn.execute(
                "UPDATE sqlite_sequence SET seq=? WHERE name='memory_events'",
                (sqlite3.Binary(b"x" * 4096),),
            )
    with sqlite3.connect(path) as conn:
        with pytest.raises(outcome.MemoryCASOutcomeRejected):
            outcome._check_global_memory_event_highwater(conn)
        assert conn.execute(
            "SELECT event_id,operation FROM memory_events ORDER BY event_id",
        ).fetchall() == [(1, "create")]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert store.get(record.memory_id, scope).content == "fixture"
