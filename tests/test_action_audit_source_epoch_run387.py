"""ActionAudit reads and appends reject reflected SQLite source substitution.

All fixtures remain local, synthetic, and free of backend dispatch.
"""

from pathlib import Path

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path):
    return SQLiteActionAudit(tmp_path / "audit # %.sqlite", clock_ms=lambda: 120)


def _call():
    return ToolCall("mock", "cap", "fixture", {"secret": "not-in-audit"})


@pytest.mark.parametrize("has_event", [False, True])
def test_event_read_rejects_source_change_during_schema_check(
    tmp_path, monkeypatch, has_event,
):
    audit = _audit(tmp_path)
    if has_event:
        audit.append(_call(), outcome="fixture")
    original_path = audit.path
    original_validate = audit_module._validate_v1_schema

    def changed_schema_check(conn):
        original_validate(conn)
        audit.path = Path(str(audit.path))

    monkeypatch.setattr(audit_module, "_validate_v1_schema", changed_schema_check)
    with pytest.raises(ActionAuditSchemaError, match="source changed"):
        audit.events()
    audit.path = original_path
    monkeypatch.setattr(audit_module, "_validate_v1_schema", original_validate)
    assert len(audit.events()) == int(has_event)


@pytest.mark.parametrize("has_event", [False, True])
def test_event_read_rejects_source_change_during_readonly_open(
    tmp_path, monkeypatch, has_event,
):
    audit = _audit(tmp_path)
    if has_event:
        audit.append(_call(), outcome="fixture")
    original_path = audit.path
    original_open = audit._connect_readonly

    def retargeting_open():
        connection = original_open()
        audit.path = Path(str(audit.path))
        return connection

    monkeypatch.setattr(audit, "_connect_readonly", retargeting_open)
    with pytest.raises(ActionAuditSchemaError, match="source changed"):
        audit.events()
    audit.path = original_path
    monkeypatch.setattr(audit, "_connect_readonly", original_open)
    assert len(audit.events()) == int(has_event)


def test_append_rejects_source_change_while_opening_write_handle(
    tmp_path, monkeypatch,
):
    audit = _audit(tmp_path)
    original_path = audit.path
    original_open = audit._connect

    def retargeting_open(*, create=False):
        connection = original_open(create=create)
        audit.path = Path(str(audit.path))
        return connection

    monkeypatch.setattr(audit, "_connect", retargeting_open)
    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.append(_call(), outcome="fixture")
    audit.path = original_path
    monkeypatch.setattr(audit, "_connect", original_open)
    assert audit.events() == []
    assert audit.append(_call(), outcome="fixture").event_id == 1


def test_append_rolls_back_when_source_changes_after_insert(tmp_path, monkeypatch):
    audit = _audit(tmp_path)
    original_path = audit.path
    original_open = audit._connect

    class ReentrantConnection:
        def __init__(self, conn):
            self._conn = conn

        def __enter__(self):
            self._conn.__enter__()
            return self

        def __exit__(self, *args):
            return self._conn.__exit__(*args)

        def close(self):
            self._conn.close()

        def execute(self, statement, *args):
            cursor = self._conn.execute(statement, *args)
            if statement.lstrip().startswith("INSERT INTO action_events"):
                audit.path = Path(str(audit.path))
            return cursor

    monkeypatch.setattr(
        audit, "_connect",
        lambda **kwargs: ReentrantConnection(original_open(**kwargs)),
    )
    with pytest.raises(ActionAuditSchemaError, match="before commit"):
        audit.append(_call(), outcome="fixture")
    audit.path = original_path
    monkeypatch.setattr(audit, "_connect", original_open)
    assert audit.events() == []


def test_unchanged_audit_evidence_never_contains_arguments(tmp_path):
    audit = _audit(tmp_path)
    event = audit.append(_call(), outcome="fixture")
    assert audit.events() == [event]
    assert "not-in-audit" not in repr(audit.events())
