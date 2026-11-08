"""Audit append and paged read refuse duplicated SQLite AUTOINCREMENT markers.

The SQLite sequence is a mutable *local* consistency signal, not an
independent anchor or evidence of real backend effects.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path, *, populated=True):
    audit = SQLiteActionAudit(tmp_path / "audit-sequence.sqlite", clock_ms=lambda: 100)
    if populated:
        audit.append(
            ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"value": 1}),
            outcome="synthetic",
        )
    return audit


def _markers(path):
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(
            "SELECT name,seq FROM sqlite_sequence ORDER BY rowid"
        ).fetchall()


@pytest.mark.parametrize("operation", ("append", "read", "paged_read"))
def test_correct_first_highwater_cannot_hide_forged_second_marker(
    tmp_path, operation,
):
    audit = _audit(tmp_path)
    with closing(sqlite3.connect(audit.path)) as conn, conn:
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES('action_events', 88)"
        )
    before = _markers(audit.path)
    assert before == [("action_events", 1), ("action_events", 88)]
    recovered = SQLiteActionAudit(audit.path, clock_ms=lambda: 100)
    with pytest.raises(ActionAuditSchemaError, match="append-only"):
        if operation == "append":
            recovered.append(
                ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"value": 2}),
                outcome="synthetic",
            )
        elif operation == "paged_read":
            recovered.events(after_event_id=1, limit=1)
        else:
            recovered.events(limit=1)
    assert _markers(audit.path) == before


def test_empty_history_rejects_orphan_sequence_rows(tmp_path):
    audit = _audit(tmp_path, populated=False)
    assert audit.events() == []
    with closing(sqlite3.connect(audit.path)) as conn, conn:
        conn.execute("INSERT INTO sqlite_sequence(name,seq) VALUES('action_events', 0)")
        conn.execute("INSERT INTO sqlite_sequence(name,seq) VALUES('action_events', 0)")
    with pytest.raises(ActionAuditSchemaError, match="truncated"):
        audit.events()


def test_valid_restart_append_and_paginated_reads_remain_allowed(tmp_path):
    audit = _audit(tmp_path)
    recovered = SQLiteActionAudit(audit.path, clock_ms=lambda: 101)
    event = recovered.append(
        ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"value": 2}),
        outcome="synthetic",
    )
    assert event.event_id == 2
    assert [row.event_id for row in recovered.events(limit=1)] == [1]
    assert [row.event_id for row in recovered.events(after_event_id=1, limit=1)] == [2]
    assert _markers(audit.path) == [("action_events", 2)]
