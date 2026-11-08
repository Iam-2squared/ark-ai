"""An intact audit tail must not conceal older overwritten local evidence.

All samples use synthetic ToolCalls and temporary SQLite. The local prefix
check is not authenticated custody and cannot detect coordinated rewrites of
SQLite rows plus independently mutable metadata.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(number: int) -> ToolCall:
    return ToolCall(
        "fixture.read", "fixture.read", "synthetic:scope",
        {"number": number},
    )


def _seed(path) -> None:
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    for number in (1, 2, 3):
        audit.append(_call(number), outcome="synthetic")


@pytest.mark.parametrize("event_id", (1, 2))
@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("outcome", ""),
        ("tool", sqlite3.Binary(b"not-text")),
        ("request_id", "act_" + "e" * 64),
        ("arguments_sha256", "f" * 64),
        ("scope", "changed:scope"),
        ("occurred_at_ms", -1),
    ),
)
def test_append_refuses_corrupt_historical_row_before_clock_callback(
    tmp_path, event_id, column, replacement,
):
    path = tmp_path / "audit.sqlite"
    _seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=?",
            (replacement, event_id),
        )
        before = conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall()
    sampled: list[bool] = []

    def clock() -> int:
        sampled.append(True)
        return 101

    restarted = SQLiteActionAudit(path, clock_ms=clock)
    with pytest.raises(ActionAuditSchemaError):
        restarted.append(_call(4), outcome="synthetic")
    assert sampled == []
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall() == before
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
        ).fetchone() == (3,)


def test_append_refuses_older_clock_regression_hidden_by_valid_tail(tmp_path):
    path = tmp_path / "audit.sqlite"
    _seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE action_events SET occurred_at_ms=101 WHERE event_id=1"
        )
    sampled: list[bool] = []
    audit = SQLiteActionAudit(path, clock_ms=lambda: sampled.append(True) or 102)
    with pytest.raises(
        ActionAuditSchemaError, match="clock regressed relative to persisted",
    ):
        audit.append(_call(4), outcome="synthetic")
    assert sampled == []
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone() == (3,)


def test_valid_historical_prefix_still_allows_restart_and_append(tmp_path):
    path = tmp_path / "audit.sqlite"
    _seed(path)
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 101)
    event = restarted.append(_call(4), outcome="synthetic")
    assert event.event_id == 4
    assert event.occurred_at_ms == 101
    assert [row.event_id for row in restarted.events()] == [1, 2, 3, 4]
