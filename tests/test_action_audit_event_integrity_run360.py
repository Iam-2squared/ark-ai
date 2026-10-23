"""Action audit read path rejects malformed persistent metadata, never reads arguments."""

import sqlite3

import pytest

from ark.agency import ActionAuditSchemaError, SQLiteActionAudit, ToolCall


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("request_id", "act_" + "z" * 64),
        ("arguments_sha256", "a" * 63),
        ("arguments_sha256", "A" * 64),
        ("tool", 42),
        ("scope", ""),
        ("outcome", ""),
        ("occurred_at_ms", -1),
        ("occurred_at_ms", "not-an-integer"),
    ],
)
def test_audit_rejects_malformed_persisted_event(tmp_path, column, replacement) -> None:
    path = tmp_path / "audit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    call = ToolCall("synthetic.read", "synthetic.read", "synthetic:scope", {"secret": "fixture"})
    audit.append(call, outcome="allowed")
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=1", (replacement,)
        ).rowcount == 1
    with pytest.raises(ActionAuditSchemaError):
        audit.events()


def test_audit_event_pagination_retains_identity_and_excludes_arguments(tmp_path) -> None:
    path = tmp_path / "audit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    call = ToolCall("synthetic.read", "synthetic.read", "synthetic:scope", {"private": "test"})
    first = audit.append(call, outcome="allowed")
    second = audit.append(call, outcome="denied")
    assert audit.events(limit=1) == [first]
    assert audit.events(after_event_id=first.event_id) == [second]
    assert "private" not in repr(audit.events())
