"""Action audit refuses forged receipt constructors on SQLite evidence paths.

All operations are local SQLite fixtures. An audit row is not authenticated
actor consent, trusted time, external backend execution, or a safe replay key.
"""

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ToolCall


def _case(tmp_path):
    audit = audit_module.SQLiteActionAudit(
        tmp_path / "audit.sqlite", clock_ms=lambda: 100,
    )
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 1})
    return audit, call


@pytest.mark.parametrize("operation", ("append", "events"))
def test_preinstalled_event_initializer_rejected_before_sqlite(
    tmp_path, monkeypatch, operation,
):
    audit, call = _case(tmp_path)
    if operation == "events":
        audit.append(call, outcome="recorded")
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("forged initializer ran")
        raise AssertionError("forged audit constructor must never execute")

    def no_sqlite(*_args, **_kwargs):
        raise AssertionError("no audit SQLite path should start")

    with monkeypatch.context() as patch:
        patch.setattr(audit_module.ActionAuditEvent, "__init__", forbidden)
        connection = "_connect" if operation == "append" else "_connect_readonly"
        patch.setattr(audit, connection, no_sqlite)
        with pytest.raises(
            audit_module.ActionAuditSchemaError, match="audit event constructor changed",
        ):
            if operation == "append":
                audit.append(call, outcome="recorded")
            else:
                audit.events()

    assert attempted == []


def test_reentrant_clock_cannot_replace_receipt_initializer_before_sql_insert(
    tmp_path, monkeypatch,
):
    audit, call = _case(tmp_path)
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("forged initializer ran")
        raise AssertionError("forged audit constructor must never execute")

    with monkeypatch.context() as patch:
        def clock():
            patch.setattr(audit_module.ActionAuditEvent, "__init__", forbidden)
            return 100

        patch.setattr(audit, "_clock_ms", clock)
        with pytest.raises(
            audit_module.ActionAuditSchemaError, match="audit event constructor changed",
        ):
            audit.append(call, outcome="recorded")

    assert attempted == []
    assert audit.events() == []


def test_reentrant_read_validation_cannot_replace_event_initializer(
    tmp_path, monkeypatch,
):
    audit, call = _case(tmp_path)
    saved = audit.append(call, outcome="recorded")
    attempted = []
    native = audit_module._validate_v1_schema

    def forbidden(*_args, **_kwargs):
        attempted.append("forged initializer ran")
        raise AssertionError("forged audit constructor must never execute")

    with monkeypatch.context() as patch:
        def review(conn):
            native(conn)
            patch.setattr(audit_module.ActionAuditEvent, "__init__", forbidden)

        patch.setattr(audit_module, "_validate_v1_schema", review)
        with pytest.raises(
            audit_module.ActionAuditSchemaError, match="audit event constructor changed",
        ):
            audit.events()

    assert attempted == []
    assert audit.events() == [saved]


def test_unmodified_action_audit_is_non_disclosing_and_read_only(tmp_path):
    audit, call = _case(tmp_path)
    event = audit.append(call, outcome="recorded")
    assert audit.events() == [event]
    assert audit.events(after_event_id=event.event_id) == []
    assert "fixture:scope" in repr(event)
    assert "'n': 1" not in repr(event)
