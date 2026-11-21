"""Over-capacity proactive marker tables fail before per-row SQL integrity scans.

Temporary synthetic SQLite only: these counts are not trusted clocks,
consent, notification permission, historical completeness or action authority.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.proactive_synthetic_review as proactive


@pytest.mark.parametrize("row_count", (4, 12))
def test_oversized_marker_table_denied_before_row_sweep(
    tmp_path, monkeypatch: pytest.MonkeyPatch, row_count: int,
) -> None:
    path = tmp_path / "oversized-preparations.sqlite"
    proactive.SyntheticProactiveLedger(path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO synthetic_prepared_triggers VALUES (?,?,?,?,?,?,?)",
            (
                ("trigger_" + f"{i:064x}", "a" * 64, "b" * 64,
                 "c" * 64, "d" * 64, 10, 10)
                for i in range(row_count)
            ),
        )
    # Exercise the production admission order with a small test-only cap.
    # The database has the exact frozen fixture schema.
    monkeypatch.setattr(proactive, "_MAX_PREPARATIONS", 3)
    statements: list[str] = []
    with closing(sqlite3.connect(path)) as conn:
        conn.set_trace_callback(statements.append)
        conn.execute("BEGIN")
        with pytest.raises(
            proactive.SyntheticTriggerRejected, match="review budget exceeded",
        ):
            proactive._validate(conn)

    sql = " ".join(statements).lower()
    assert "select count(*) from synthetic_prepared_triggers" in sql
    assert "coalesce(sum(case when" not in sql
    assert "select trigger_id,scope_digest" not in sql

    # Cold reopen must quarantine, not repair or prune the excess markers.
    with pytest.raises(
        proactive.SyntheticTriggerRejected, match="review budget exceeded",
    ):
        proactive.SyntheticProactiveLedger(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers",
        ).fetchone() == (row_count,)


def test_below_limit_still_reaches_storage_class_admission(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "malformed-preparation.sqlite"
    proactive.SyntheticProactiveLedger(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO synthetic_prepared_triggers VALUES (?,?,?,?,?,?,?)",
            ("trigger_" + "a" * 64, sqlite3.Binary(b"a" * 64),
             "b" * 64, "c" * 64, "d" * 64, 10, 10),
        )
    monkeypatch.setattr(proactive, "_MAX_PREPARATIONS", 3)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("BEGIN")
        with pytest.raises(
            proactive.SyntheticTriggerRejected,
            match="persisted trigger row integrity failed",
        ):
            proactive._validate(conn)
