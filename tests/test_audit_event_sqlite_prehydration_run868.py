"""Bounded audit identity ingress before SQLite row hydration (offline-only).

A local SQL storage-class check is not authenticated evidence, a user approval,
a trusted clock, or permission to dispatch any ToolBackend.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _seed(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 100)
    call = ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"id": 1})
    first = audit.append(call, outcome="offline-only")
    return audit, call, first


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("request_id", "act_" + "é" * 64),
        ("arguments_sha256", "é" * 64),
        ("tool", sqlite3.Binary(b"fixture.read")),
        ("capability", sqlite3.Binary(b"fixture.read")),
        ("scope", sqlite3.Binary(b"synthetic:scope")),
        ("outcome", sqlite3.Binary(b"offline-only")),
        ("occurred_at_ms", "not-an-integer"),
    ),
)
def test_malformed_sqlite_metadata_refused_before_audit_page_or_history(
    tmp_path, column, replacement,
):
    audit, call, _first = _seed(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        assert conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=1",
            (replacement,),
        ).rowcount == 1

    with pytest.raises(ActionAuditSchemaError, match="hydration admission"):
        audit.events()
    with pytest.raises(ActionAuditSchemaError, match="hydration admission"):
        audit.append(call, outcome="offline-only")

    # No new append may follow a malformed retained local audit prefix.
    with sqlite3.connect(audit.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone() == (1,)


def test_valid_audit_history_retains_paged_and_append_behavior(tmp_path):
    audit, call, first = _seed(tmp_path)
    later = audit.append(call, outcome="offline-only")
    assert [item.event_id for item in audit.events(limit=1)] == [first.event_id]
    assert audit.events(after_event_id=first.event_id) == [later]
    assert audit.events() == [first, later]
