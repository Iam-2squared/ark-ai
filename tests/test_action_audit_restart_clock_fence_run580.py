"""Fail-closed, restart-safe synthetic action audit timestamp ordering.

Uses only temporary local SQLite, no real tool/backend execution or trusted clock.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(index):
    return ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": index})


def test_restarted_writer_refuses_earlier_clock_and_rolls_back(tmp_path):
    path = tmp_path / "audit.sqlite"
    first = SQLiteActionAudit(path, clock_ms=lambda: 300)
    earlier = first.append(_call(1), outcome="synthetic")
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 299)
    with pytest.raises(ActionAuditSchemaError, match="clock regressed"):
        restarted.append(_call(2), outcome="synthetic")
    assert restarted.events() == [earlier]
    recovered = SQLiteActionAudit(path, clock_ms=lambda: 300)
    accepted = recovered.append(_call(3), outcome="synthetic")
    assert [entry.event_id for entry in recovered.events()] == [1, 2]
    assert accepted.occurred_at_ms == earlier.occurred_at_ms == 300


def test_equal_clocks_across_independent_writer_instances_are_allowed(tmp_path):
    path = tmp_path / "audit.sqlite"
    left = SQLiteActionAudit(path, clock_ms=lambda: 400)
    right = SQLiteActionAudit(path, clock_ms=lambda: 400)
    left.append(_call(1), outcome="synthetic")
    right.append(_call(2), outcome="synthetic")
    assert [row.occurred_at_ms for row in right.events()] == [400, 400]


def test_last_persisted_future_timestamp_blocks_new_append(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 500)
    audit.append(_call(1), outcome="synthetic")
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE action_events SET occurred_at_ms=900 WHERE event_id=1")
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 600)
    with pytest.raises(ActionAuditSchemaError, match="clock regressed"):
        restarted.append(_call(2), outcome="synthetic")
    assert [(row.event_id, row.occurred_at_ms) for row in restarted.events()] == [(1, 900)]


def test_bad_persisted_clock_type_is_not_silently_coerced(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 1000)
    audit.append(_call(1), outcome="synthetic")
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE action_events SET occurred_at_ms=? WHERE event_id=1", ("not-a-clock",))
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 1001)
    with pytest.raises(ActionAuditSchemaError, match="clock regressed"):
        restarted.append(_call(2), outcome="synthetic")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone()[0] == 1
