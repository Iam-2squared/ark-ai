"""ActionAudit closes bootstrap/write handles on Windows and rollback paths."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call():
    return ToolCall("offline", "fixture", "test", {"number": 1})


def test_bootstrap_closes_file_handle_for_relocation(tmp_path: Path):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 10)
    moved = tmp_path / "moved.sqlite"
    path.replace(moved)
    assert not path.exists()
    assert moved.exists()
    with pytest.raises(ActionAuditSchemaError, match="unavailable"):
        audit.events()
    assert not path.exists()


def test_append_closes_file_handle_without_losing_event(tmp_path: Path):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 11)
    event = audit.append(_call(), outcome="offline")
    assert event.event_id == 1
    path.replace(tmp_path / "backup.sqlite")
    assert not path.exists()
    assert (tmp_path / "backup.sqlite").exists()


def test_failed_clock_rolls_back_and_closes_writer(tmp_path: Path):
    path = tmp_path / "audit.sqlite"

    def raise_clock():
        raise ValueError("fixture clock failed")

    audit = SQLiteActionAudit(path, clock_ms=raise_clock)
    with pytest.raises(ValueError, match="fixture clock failed"):
        audit.append(_call(), outcome="never_committed")
    assert audit.events() == []
    path.replace(tmp_path / "rollback.sqlite")
    assert not path.exists()


def test_failed_bootstrap_releases_corrupt_file_handle(tmp_path: Path):
    path = tmp_path / "audit.sqlite"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("PRAGMA user_version=999")
    with pytest.raises(ActionAuditSchemaError, match="newer"):
        SQLiteActionAudit(path)
    path.replace(tmp_path / "unmodified.sqlite")
    with closing(sqlite3.connect(tmp_path / "unmodified.sqlite")) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 999


def test_successful_append_preserves_v1_history(tmp_path: Path):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 123)
    before = audit.events()
    audit.append(_call(), outcome="synthetic")
    after = audit.events()
    assert before == []
    assert len(after) == 1
    assert after[0].occurred_at_ms == 123
    assert after[0].outcome == "synthetic"
