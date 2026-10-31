"""SQLite audit rows must bind their request ID to stored identity fields.

The check is local consistency only: a malicious writer can replace every
field and recompute the digest. No external effect or trusted clock is proven.
"""

import sqlite3

import pytest

from ark.agency import ActionAuditSchemaError, SQLiteActionAudit, ToolCall


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("request_id", "act_" + "0" * 64),
        ("tool", "another.read"),
        ("capability", "another.read"),
        ("scope", "different:scope"),
        ("arguments_sha256", "f" * 64),
    ],
)
def test_locally_consistent_shapes_cannot_hide_inconsistent_request_identity(
    tmp_path, column, replacement
):
    path = tmp_path / "audit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope", {"private": "value"})
    original = audit.append(call, outcome="fixture-only")
    assert getattr(original, column) != replacement
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=?",
            (replacement, original.event_id),
        ).rowcount == 1
    with pytest.raises(ActionAuditSchemaError, match="request identity is inconsistent"):
        audit.events()
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM action_events").fetchone() == (1,)


def test_valid_audit_request_identity_survives_readonly_pagination(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 100)
    first = audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:scope", {"a": 1}),
        outcome="allowed",
    )
    second = audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:scope", {"a": 2}),
        outcome="denied",
    )
    assert audit.events(limit=1) == [first]
    assert audit.events(after_event_id=first.event_id) == [second]
    assert "fixture-only-private-argument" not in repr(audit.events())
