"""Chronological paging checks for disconnected SQLite action-audit evidence.

All probes use a temporary local SQLite database and synthetic actions only.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(index: int) -> ToolCall:
    return ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": index})


def _seed(path) -> SQLiteActionAudit:
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    audit.append(_call(1), outcome="synthetic")
    audit.append(_call(2), outcome="synthetic")
    audit.append(_call(3), outcome="synthetic")
    return audit


def test_full_read_rejects_historical_timestamp_rollback(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = _seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE action_events SET occurred_at_ms=99 WHERE event_id=2"
        )
    with pytest.raises(ActionAuditSchemaError, match="stored clocks regressed"):
        audit.events()
    # The failed read must not change any persisted event.
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT occurred_at_ms FROM action_events ORDER BY event_id"
        ).fetchall() == [(100,), (99,), (100,)]


def test_paged_read_rejects_clock_rollback_against_predecessor(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = _seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE action_events SET occurred_at_ms=99 WHERE event_id=2"
        )
    with pytest.raises(ActionAuditSchemaError, match="stored clocks regressed"):
        audit.events(after_event_id=1, limit=1)


def test_paged_read_rejects_malformed_predecessor_even_if_page_empty(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = _seed(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE action_events SET occurred_at_ms=? WHERE event_id=3",
            ("invalid-time",),
        )
    with pytest.raises(ActionAuditSchemaError, match="preceding clock is malformed"):
        audit.events(after_event_id=3, limit=1)


def test_equal_persisted_timestamps_remain_valid_across_pages(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = _seed(path)
    first = audit.events(limit=1)
    next_page = audit.events(after_event_id=first[-1].event_id, limit=2)
    assert [item.event_id for item in first + next_page] == [1, 2, 3]
    assert [item.occurred_at_ms for item in first + next_page] == [100, 100, 100]
