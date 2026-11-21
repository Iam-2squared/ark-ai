"""Reviewing a stale audit object must reject changed SQLite schema bytes."""

import sqlite3

import pytest

from ark.agency import ActionAuditSchemaError, SQLiteActionAudit, ToolCall
from ark.agency.audit_continuity_review import review_audit_continuity


def _audit(tmp_path):
    path = tmp_path / "synthetic-audit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    audit.append(ToolCall("fixture.read", "fixture.read", "synthetic:scope"), outcome="ok")
    return path, audit


@pytest.mark.parametrize(
    "tamper",
    (
        "DROP INDEX idx_action_request",
        "CREATE TABLE fixture_shadow(x TEXT)",
        "CREATE TRIGGER shadow AFTER INSERT ON action_events BEGIN SELECT 1; END",
        "PRAGMA user_version=0",
        "PRAGMA user_version=2",
    ),
)
def test_continuity_rejects_post_startup_schema_drift(tmp_path, tamper):
    path, audit = _audit(tmp_path)
    retained = review_audit_continuity(audit)
    assert retained.event_count == 1
    with sqlite3.connect(path) as conn:
        conn.execute(tamper)
    with pytest.raises(ActionAuditSchemaError, match="schema|version"):
        review_audit_continuity(audit, retained=retained)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone()[0] == 1


def test_unmodified_schema_allows_append_only_prefix_continuity(tmp_path):
    _path, audit = _audit(tmp_path)
    first = review_audit_continuity(audit)
    audit.append(
        ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"step": 2}),
        outcome="ok",
    )
    second = review_audit_continuity(audit, retained=first)
    assert first.event_count == 1
    assert second.event_count == 2
    assert second.tail_event_id > first.tail_event_id
    assert second.chain_sha256 != first.chain_sha256
