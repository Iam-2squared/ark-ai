"""Read-only audit continuity rejects a missing local terminal event.

The sqlite_sequence check is local corruption evidence, not a tamper-proof
writer, externally trusted clock or real tool execution receipt.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _fixture(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "synthetic-audit.db", clock_ms=lambda: 100)
    for index in range(3):
        audit.append(
            ToolCall(
                "fixture.read", "fixture.read", "synthetic:scope",
                {"index": index},
            ),
            outcome="synthetic-only",
        )
    return audit


@pytest.mark.parametrize(
    "damage",
    ("deleted_last", "deleted_all", "forged_low_sequence", "deleted_sequence"),
)
def test_missing_terminal_witness_is_refused_without_retained_anchor(
    tmp_path, damage,
):
    audit = _fixture(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        if damage == "deleted_last":
            conn.execute("DELETE FROM action_events WHERE event_id=3")
        elif damage == "deleted_all":
            conn.execute("DELETE FROM action_events")
        elif damage == "forged_low_sequence":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=2 WHERE name='action_events'"
            )
        else:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='action_events'"
            )
        before = conn.execute(
            "SELECT event_id FROM action_events ORDER BY event_id"
        ).fetchall()

    with pytest.raises(ActionAuditSchemaError, match="high-water"):
        review_audit_continuity(audit)

    with sqlite3.connect(audit.path) as conn:
        assert conn.execute(
            "SELECT event_id FROM action_events ORDER BY event_id"
        ).fetchall() == before


def test_valid_append_after_restart_retains_inert_contiguous_witness(tmp_path):
    audit = _fixture(tmp_path)
    previous = review_audit_continuity(audit)
    reopened = SQLiteActionAudit(audit.path, clock_ms=lambda: 100)
    reopened.append(
        ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"index": 3}),
        outcome="synthetic-only",
    )
    later = review_audit_continuity(reopened, retained=previous)
    assert (previous.event_count, previous.tail_event_id) == (3, 3)
    assert (later.event_count, later.tail_event_id) == (4, 4)
    assert later.chain_sha256 != previous.chain_sha256
