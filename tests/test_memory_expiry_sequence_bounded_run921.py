"""Bounded high-water metadata reads for disposable Memory expiry fixtures.

Synthetic SQLite only; no persisted user store is opened or modified.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory.expiry_candidate_preview import (
    MemoryExpiryPreviewRejected,
    _check_global_event_highwater,
)


def _connection(*, with_event: bool = True) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE memory_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT)"
    )
    if with_event:
        conn.execute("INSERT INTO memory_events DEFAULT VALUES")
    return conn


def test_empty_autoincrement_event_table_has_no_highwater() -> None:
    with _connection(with_event=False) as conn:
        _check_global_event_highwater(conn)


def test_single_native_sequence_marker_is_consistent() -> None:
    with _connection() as conn:
        _check_global_event_highwater(conn)


@pytest.mark.parametrize("extra_markers", (1, 3, 16))
def test_duplicate_sequence_markers_are_rejected(extra_markers: int) -> None:
    with _connection() as conn:
        conn.executemany(
            "INSERT INTO sqlite_sequence (name, seq) VALUES ('memory_events', 1)",
            ((),) * extra_markers,
        )
        with pytest.raises(MemoryExpiryPreviewRejected, match="high-water mismatch"):
            _check_global_event_highwater(conn)


def test_forged_text_sequence_marker_rejected() -> None:
    with _connection() as conn:
        conn.execute(
            "UPDATE sqlite_sequence SET seq='forged' WHERE name='memory_events'"
        )
        with pytest.raises(MemoryExpiryPreviewRejected, match="high-water mismatch"):
            _check_global_event_highwater(conn)


def test_event_id_gap_still_rejected() -> None:
    with _connection() as conn:
        conn.execute("INSERT INTO memory_events DEFAULT VALUES")
        conn.execute("DELETE FROM memory_events WHERE event_id=1")
        with pytest.raises(MemoryExpiryPreviewRejected, match="high-water mismatch"):
            _check_global_event_highwater(conn)


def test_sequence_scan_sql_has_a_hard_row_limit() -> None:
    with _connection() as conn:
        observed: list[str] = []
        conn.set_trace_callback(observed.append)
        _check_global_event_highwater(conn)
        scans = [sql.upper() for sql in observed if "SQLITE_SEQUENCE" in sql.upper()]
        assert len(scans) == 1
        assert "LIMIT 2" in scans[0]
