"""Version-1 ActionAudit startup contract checks on synthetic SQLite only."""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path):
    path = tmp_path / "synthetic-audit.sqlite3"
    return path, SQLiteActionAudit(path, clock_ms=lambda: 111)


def _sample_call():
    return ToolCall(
        "fixture.read", "fixture.read", "synthetic:scope", {"fixture": "only"}
    )


def test_new_and_reopened_audit_preserve_readable_events(tmp_path):
    path, audit = _audit(tmp_path)
    expected = audit.append(_sample_call(), outcome="synthetic-allowed")
    reopened = SQLiteActionAudit(path, clock_ms=lambda: 111)
    assert reopened.events() == [expected]
    assert reopened.append(_sample_call(), outcome="synthetic-second").event_id == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "DROP INDEX idx_action_request",
        (
            "DROP INDEX idx_action_request;"
            "CREATE INDEX idx_action_request ON action_events(event_id, request_id)"
        ),
        "CREATE INDEX extra_action_index ON action_events(scope)",
        (
            "CREATE TRIGGER unexpected_action_trigger BEFORE INSERT ON action_events "
            "BEGIN SELECT RAISE(FAIL, 'synthetic-only'); END"
        ),
    ],
)
def test_version_one_schema_mutations_refuse_reopen(tmp_path, mutation):
    path, audit = _audit(tmp_path)
    original = audit.append(_sample_call(), outcome="synthetic-safe")
    with sqlite3.connect(path) as conn:
        conn.executescript(mutation)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone()[0] == 1

    with pytest.raises(ActionAuditSchemaError, match="schema differs"):
        SQLiteActionAudit(path, clock_ms=lambda: 111)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT request_id FROM action_events").fetchone()[0] == (
            original.request_id
        )


def test_same_version_unexpected_column_contract_refuses_reopen(tmp_path):
    path, _ = _audit(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("ALTER TABLE action_events ADD COLUMN injected TEXT")
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
    with pytest.raises(ActionAuditSchemaError, match="schema differs"):
        SQLiteActionAudit(path, clock_ms=lambda: 111)


def test_newer_version_still_fails_closed(tmp_path):
    path, _ = _audit(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(ActionAuditSchemaError, match="newer"):
        SQLiteActionAudit(path, clock_ms=lambda: 111)
