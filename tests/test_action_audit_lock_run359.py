"""Audit receipts are stored under a writer lock before sampling time."""

import sqlite3
from contextlib import closing

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall


def test_audit_clock_observes_sqlite_writer_lock(tmp_path) -> None:
    path = tmp_path / "audit.sqlite3"
    checked = {"count": 0}

    def clock() -> int:
        checked["count"] += 1
        with closing(sqlite3.connect(path, timeout=0.01)) as competing:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                competing.execute("BEGIN IMMEDIATE")
        return 1234

    audit = SQLiteActionAudit(path, clock_ms=clock)
    call = ToolCall("synthetic.read", "synthetic.read", "scope:synthetic", {"x": "secret"})
    event = audit.append(call, outcome="fixture-allowed")
    assert checked["count"] == 1
    assert event.occurred_at_ms == 1234
    assert audit.events() == [event]
    assert "secret" not in repr(event)


def test_invalid_clock_rolls_back_audit_event(tmp_path) -> None:
    path = tmp_path / "audit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: True)
    call = ToolCall("synthetic.read", "synthetic.read", "scope:synthetic")
    with pytest.raises(ValueError, match="non-negative integer"):
        audit.append(call, outcome="fixture-allowed")
    assert audit.events() == []


@pytest.mark.parametrize("invalid", [object(), "synthetic"])
def test_audit_rejects_nonexact_tool_call(tmp_path, invalid: object) -> None:
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 10)
    with pytest.raises(TypeError, match="exact ToolCall"):
        audit.append(invalid, outcome="fixture-allowed")  # type: ignore[arg-type]
    assert audit.events() == []


def test_audit_rejects_nonexact_outcome_type(tmp_path) -> None:
    class OutcomeAlias(str):
        pass

    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 10)
    call = ToolCall("synthetic.read", "synthetic.read", "scope:synthetic")
    with pytest.raises(ValueError, match="exact string"):
        audit.append(call, outcome=OutcomeAlias("fixture"))
    assert audit.events() == []
