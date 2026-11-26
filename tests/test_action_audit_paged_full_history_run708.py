"""A paged audit READ cannot hide corruption outside the selected page.

Local SQLite integrity is not authenticated custody, external consent, or an
authorization to execute. No real tool, credentials, or network are involved.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _seed(path):
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    for number in (1, 2, 3, 4):
        audit.append(
            ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": number}),
            outcome="synthetic",
        )
    return audit


@pytest.mark.parametrize(
    ("damage", "after_event_id", "limit"),
    (
        ("first_identity", 2, 1),
        ("last_identity", 0, 1),
        ("hidden_clock_regression", 2, 1),
        ("empty_page_older_damage", 4, 1),
    ),
)
def test_paged_read_refuses_unseen_corrupt_committed_audit_history(
    tmp_path, damage, after_event_id, limit,
):
    path = tmp_path / "audit.sqlite"
    audit = _seed(path)
    with closing(sqlite3.connect(path)) as conn, conn:
        if damage == "first_identity":
            conn.execute(
                "UPDATE action_events SET outcome='' WHERE event_id=1"
            )
        elif damage == "last_identity":
            conn.execute(
                "UPDATE action_events SET scope='replaced:scope' WHERE event_id=4"
            )
        elif damage == "hidden_clock_regression":
            conn.execute(
                "UPDATE action_events SET occurred_at_ms=101 WHERE event_id=1"
            )
        else:
            conn.execute(
                "UPDATE action_events SET outcome='' WHERE event_id=2"
            )
        before = conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall()

    with pytest.raises(ActionAuditSchemaError):
        audit.events(after_event_id=after_event_id, limit=limit)

    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall() == before
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
        ).fetchone() == (4,)


def test_healthy_paged_audit_read_stays_read_only_and_dense(tmp_path):
    path = tmp_path / "audit.sqlite"
    audit = _seed(path)
    assert [item.event_id for item in audit.events(limit=2)] == [1, 2]
    assert [item.event_id for item in audit.events(after_event_id=2, limit=1)] == [3]
    assert audit.events(after_event_id=4, limit=1) == []
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
        ).fetchone() == (4,)
