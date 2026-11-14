"""Local audit appends must not extend an incomplete AUTOINCREMENT history.

All scenarios use isolated SQLite and synthetic ToolCall identities. An
unaltered SQLite sequence is not an authenticated independent witness.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(number: int) -> ToolCall:
    return ToolCall(
        "fixture.read", "fixture.read", "synthetic:scope", {"number": number}
    )


def _seed(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    for number in (1, 2, 3):
        audit.append(_call(number), outcome="synthetic")
    return path


@pytest.mark.parametrize("deleted", (1, 2, 3, "all"))
def test_restarted_append_refuses_missing_first_middle_tail_or_entire_history(
    tmp_path, deleted,
):
    path = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        if deleted == "all":
            conn.execute("DELETE FROM action_events")
        else:
            conn.execute("DELETE FROM action_events WHERE event_id=?", (deleted,))
        original = conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall()
        high_water = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
        ).fetchone()
    assert high_water == (3,)
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 100)
    with pytest.raises(ActionAuditSchemaError, match="append-only"):
        restarted.append(_call(4), outcome="synthetic")
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall() == original
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
        ).fetchone() == high_water


def test_append_refuses_rewritten_event_id_without_touching_history(tmp_path):
    path = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE action_events SET event_id=40 WHERE event_id=3")
        before = conn.execute("SELECT event_id FROM action_events ORDER BY event_id").fetchall()
    with pytest.raises(ActionAuditSchemaError, match="append-only"):
        SQLiteActionAudit(path, clock_ms=lambda: 100).append(
            _call(4), outcome="synthetic"
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT event_id FROM action_events ORDER BY event_id"
        ).fetchall() == before


def test_restarted_append_accepts_valid_contiguous_history(tmp_path):
    path = _seed(tmp_path)
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 100)
    event = restarted.append(_call(4), outcome="synthetic")
    assert event.event_id == 4
    assert [row.event_id for row in restarted.events()] == [1, 2, 3, 4]
