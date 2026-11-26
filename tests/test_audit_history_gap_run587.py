"""Missing local audit events must not be mistaken for a coherent prefix.

All cases use synthetic local SQLite. A gap-free sequence does not prove
an authenticated writer, retained witness, trusted clock or real execution.
"""

import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _history(tmp_path: Path) -> SQLiteActionAudit:
    audit = SQLiteActionAudit(tmp_path / "local-audit.sqlite", clock_ms=lambda: 50)
    for value in range(3):
        audit.append(
            ToolCall("mock.read", "mock.read", "synthetic:only", {"seq": value}),
            outcome="synthetic-only",
        )
    return audit


@pytest.mark.parametrize("lost_id", (1, 2))
def test_missing_first_or_middle_event_fails_without_retained_witness(
    tmp_path: Path, lost_id: int,
):
    audit = _history(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("DELETE FROM action_events WHERE event_id=?", (lost_id,))
        rows = conn.execute(
            "SELECT event_id FROM action_events ORDER BY event_id"
        ).fetchall()
    assert len(rows) == 2
    with pytest.raises(ActionAuditSchemaError, match="event ID gap"):
        review_audit_continuity(audit)
    with sqlite3.connect(audit.path) as conn:
        assert conn.execute(
            "SELECT event_id FROM action_events ORDER BY event_id"
        ).fetchall() == rows


def test_rewritten_event_id_is_not_a_valid_continuous_history(tmp_path: Path):
    audit = _history(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("UPDATE action_events SET event_id=20 WHERE event_id=3")
    with pytest.raises(ActionAuditSchemaError, match="event ID gap"):
        review_audit_continuity(audit)


def test_ordinary_append_after_restart_preserves_continuous_sequence(tmp_path: Path):
    original = _history(tmp_path)
    initial = review_audit_continuity(original, require_monotonic_time=True)
    assert (initial.event_count, initial.tail_event_id) == (3, 3)
    restarted = SQLiteActionAudit(original.path, clock_ms=lambda: 50)
    restarted.append(
        ToolCall("mock.read", "mock.read", "synthetic:only", {"seq": 3}),
        outcome="synthetic-only",
    )
    later = review_audit_continuity(
        restarted, retained=initial, require_monotonic_time=True,
    )
    assert (later.event_count, later.tail_event_id) == (4, 4)
    assert later.chain_sha256 != initial.chain_sha256
