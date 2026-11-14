"""Generation CAS must probe at most two sqlite_sequence witnesses.

The malformed catalog is in-memory and never becomes a real Memory v1 store.
"""
import sqlite3

import pytest

from ark.memory import generation_fenced_cas as cas
from ark.memory.contracts import MemoryScope


@pytest.mark.parametrize("extra_markers", [1, 16, 256])
def test_generation_cas_rejects_duplicate_sequence_with_two_row_probe(
    monkeypatch: pytest.MonkeyPatch, extra_markers: int,
) -> None:
    # Isolate the prefix query: the legitimate v1 schema verifier is
    # intentionally bypassed ONLY for this disposable malformed fixture.
    monkeypatch.setattr(cas, "_validate_v1_schema", lambda connection: None)
    statements: list[str] = []
    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE memory_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        connection.execute("INSERT INTO memory_events DEFAULT VALUES")
        connection.executemany(
            "INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)",
            [("memory_events", 1)] * extra_markers,
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone() == (extra_markers + 1,)
        connection.set_trace_callback(statements.append)
        with pytest.raises(
            cas.MemoryGenerationCASRejected, match="global event high-water mismatch",
        ):
            cas._snapshot(
                connection, "mem_" + "0" * 64, MemoryScope("owner", "notes"), "source",
            )
    marker_reads = [
        statement for statement in statements
        if "SELECT seq FROM sqlite_sequence" in statement
    ]
    assert len(marker_reads) == 1
    assert "LIMIT 2" in marker_reads[0]


def test_generation_cas_rejects_missing_sequence_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cas, "_validate_v1_schema", lambda connection: None)
    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE memory_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        connection.execute("INSERT INTO memory_events DEFAULT VALUES")
        connection.execute("DELETE FROM sqlite_sequence WHERE name='memory_events'")
        with pytest.raises(
            cas.MemoryGenerationCASRejected, match="global event high-water mismatch",
        ):
            cas._snapshot(
                connection, "mem_" + "0" * 64, MemoryScope("owner", "notes"), "source",
            )
