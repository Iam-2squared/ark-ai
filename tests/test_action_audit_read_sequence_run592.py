"""The audit READ API must reject local deleted-prefix/suffix evidence.

All fixtures use isolated SQLite and synthetic action identities. sqlite_sequence
is mutable local metadata, not an independently authenticated audit tip.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _seed(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    for number in (1, 2, 3):
        audit.append(
            ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": number}),
            outcome="synthetic",
        )
    return path


@pytest.mark.parametrize("deleted", (1, 2, 3, "all"))
@pytest.mark.parametrize("after_event_id,limit", ((0, 100), (1, 1)))
def test_read_refuses_deleted_first_middle_tail_or_entire_history(
    tmp_path, deleted, after_event_id, limit,
):
    path = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        if deleted == "all":
            conn.execute("DELETE FROM action_events")
        else:
            conn.execute("DELETE FROM action_events WHERE event_id=?", (deleted,))
        persisted = conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall()
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    with pytest.raises(ActionAuditSchemaError, match="append-only"):
        audit.events(after_event_id=after_event_id, limit=limit)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall() == persisted


def test_read_refuses_corrupt_high_water_mark(tmp_path):
    path = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE sqlite_sequence SET seq=2 WHERE name='action_events'")
    with pytest.raises(ActionAuditSchemaError, match="append-only"):
        SQLiteActionAudit(path).events(limit=1)


def test_read_accepts_dense_history_across_pagination(tmp_path):
    path = _seed(tmp_path)
    audit = SQLiteActionAudit(path)
    assert [event.event_id for event in audit.events(limit=2)] == [1, 2]
    assert [event.event_id for event in audit.events(after_event_id=2, limit=2)] == [3]
    assert audit.events(after_event_id=3, limit=2) == []
