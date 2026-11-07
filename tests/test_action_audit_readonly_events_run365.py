"""Read-only ActionAudit events must not create or mutate replacement SQLite files."""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call():
    return ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": 1})


def test_events_remain_valid_with_read_only_connection(tmp_path):
    path = tmp_path / "synthetic-audit.db"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 123)
    event = audit.append(_call(), outcome="fixture-pass")
    assert audit.events() == [event]
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_stale_audit_path_does_not_create_a_replacement(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "real.db", clock_ms=lambda: 123)
    audit.append(_call(), outcome="fixture-pass")
    missing = tmp_path / "absent.db"
    audit.path = missing
    with pytest.raises(ActionAuditSchemaError, match="read-only file"):
        audit.events()
    assert not missing.exists()


def test_read_only_events_with_special_characters_in_local_path(tmp_path):
    audit = SQLiteActionAudit(
        tmp_path / "folder # space" / "audit # 20%.db", clock_ms=lambda: 123
    )
    event = audit.append(_call(), outcome="fixture-pass")
    assert audit.events(after_event_id=0) == [event]
    assert audit.events(after_event_id=event.event_id) == []


def test_events_never_open_mutating_store_connection(tmp_path, monkeypatch):
    audit = SQLiteActionAudit(tmp_path / "synthetic.db", clock_ms=lambda: 123)
    event = audit.append(_call(), outcome="fixture-pass")

    def forbidden():
        raise AssertionError("mutating connection unexpectedly used")

    monkeypatch.setattr(audit, "_connect", forbidden)
    assert audit.events() == [event]
