"""Audit v1 append must fail closed if its initialized SQLite source vanished."""

import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _fixture(tmp_path: Path):
    path = tmp_path / "Audit # %.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    call = ToolCall("offline", "write", "local", {"private": "NEVER-DISCLOSE"})
    return audit, call, path


def test_explicit_bootstrap_still_creates_valid_v1_storage(tmp_path: Path):
    audit, call, path = _fixture(tmp_path)
    assert path.exists()
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    event = audit.append(call, outcome="offline")
    assert event.event_id == 1
    assert len(audit.events()) == 1
    assert "NEVER-DISCLOSE" not in repr(audit.events())


def test_missing_initialized_audit_is_not_recreated_on_append(tmp_path: Path):
    audit, call, path = _fixture(tmp_path)
    audit.append(call, outcome="original")
    moved = tmp_path / "moved-audit.sqlite"
    path.rename(moved)
    with pytest.raises(sqlite3.OperationalError):
        audit.append(call, outcome="must-not-recreate")
    assert not path.exists()
    assert moved.exists()


def test_restored_audit_preserves_event_ids_after_missing_append(tmp_path: Path):
    audit, call, path = _fixture(tmp_path)
    first = audit.append(call, outcome="before-relocation")
    moved = tmp_path / "backup.sqlite"
    path.rename(moved)
    with pytest.raises(sqlite3.OperationalError):
        audit.append(call, outcome="not-saved")
    moved.rename(path)
    second = audit.append(call, outcome="after-restoration")
    assert (first.event_id, second.event_id) == (1, 2)
    assert [row.outcome for row in audit.events()] == [
        "before-relocation", "after-restoration",
    ]


def test_reentrant_clock_path_swap_rejects_and_rolls_back(tmp_path: Path):
    audit, call, original_path = _fixture(tmp_path)
    alternative = SQLiteActionAudit(tmp_path / "other.sqlite", clock_ms=lambda: 100)
    audit._clock_ms = lambda: setattr(audit, "path", alternative.path) or 101
    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.append(call, outcome="must-not-commit")
    assert alternative.events() == []
    audit.path = original_path
    assert audit.events() == []


def test_reentrant_clock_same_value_new_path_instance_rejected(tmp_path: Path):
    audit, call, original_path = _fixture(tmp_path)
    audit._clock_ms = lambda: setattr(audit, "path", Path(str(original_path))) or 101
    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.append(call, outcome="must-not-commit")
    audit.path = original_path
    assert audit.events() == []


def test_reentrant_clock_type_corruption_is_rejected(tmp_path: Path):
    audit, call, original_path = _fixture(tmp_path)
    audit._clock_ms = lambda: setattr(audit, "path", "non-path") or 101
    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.append(call, outcome="must-not-commit")
    audit.path = original_path
    assert audit.events() == []


def test_normal_append_after_reentrant_clock_denial_remains_usable(tmp_path: Path):
    audit, call, original_path = _fixture(tmp_path)
    audit._clock_ms = lambda: setattr(audit, "path", tmp_path / "other.sqlite") or 101
    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.append(call, outcome="denied")
    assert not (tmp_path / "other.sqlite").exists()
    audit.path = original_path
    audit._clock_ms = lambda: 102
    assert audit.append(call, outcome="permitted-local-audit").event_id == 1
    assert len(audit.events()) == 1
