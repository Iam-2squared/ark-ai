"""SQLite integer overflow must fail closed in disconnected action audit."""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall


def _call():
    return ToolCall("fixture.read", "fixture.cap", "fixture:scope")


@pytest.mark.parametrize("sample", (2**63, 10**30, -1, True, 1.5, "100"))
def test_invalid_clock_never_inserts_event(tmp_path, sample):
    audit = SQLiteActionAudit(tmp_path / "audit.db", clock_ms=lambda: sample)
    with pytest.raises(ValueError, match="SQLite INTEGER"):
        audit.append(_call(), outcome="synthetic")
    with sqlite3.connect(audit.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone()[0] == 0


@pytest.mark.parametrize("cursor", (2**63, 10**30, -1, True, 1.5, "1"))
def test_invalid_event_cursor_fails_before_sqlite_binding(tmp_path, cursor):
    audit = SQLiteActionAudit(tmp_path / "audit.db")
    with pytest.raises(ValueError, match="SQLite INTEGER"):
        audit.events(after_event_id=cursor)


def test_max_signed_sqlite_clock_round_trips(tmp_path):
    max_int = 2**63 - 1
    audit = SQLiteActionAudit(tmp_path / "audit.db", clock_ms=lambda: max_int)
    created = audit.append(_call(), outcome="synthetic")
    assert created.occurred_at_ms == max_int
    assert audit.events()[0].occurred_at_ms == max_int
    assert audit.events(after_event_id=max_int) == []
