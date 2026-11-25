"""Run1386: ActionAudit event validator vectors retain import-time identity."""

from __future__ import annotations

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _case(tmp_path):
    audit = audit_module.SQLiteActionAudit(
        tmp_path / "audit.sqlite", clock_ms=lambda: 100,
    )
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 1})
    return audit, call


@pytest.mark.parametrize("operation", ("append", "events"))
def test_event_validator_rejects_joint_vector_rebinding_before_sqlite(
    tmp_path, monkeypatch, operation,
):
    audit, call = _case(tmp_path)
    if operation == "events":
        audit.append(call, outcome="recorded")

    descriptor_calls = []
    connection_calls = []

    def hostile_descriptor(*_args, **_kwargs):
        descriptor_calls.append(True)
        raise AssertionError("replaced audit event descriptor executed")

    def forbidden_connect(*_args, **_kwargs):
        connection_calls.append(True)
        raise AssertionError("audit SQLite access must follow constructor custody")

    with monkeypatch.context() as patch:
        patch.setattr(
            audit_module.ActionAuditEvent, "event_id", property(hostile_descriptor),
        )
        for name in (
            "_EVENT_FIELDS",
            "_ORIGINAL_EVENT_FIELDS",
            "_EVENT_HOOKS",
            "_ORIGINAL_EVENT_HOOKS",
        ):
            patch.setattr(audit_module, name, ())
        connection = "_connect" if operation == "append" else "_connect_readonly"
        patch.setattr(audit, connection, forbidden_connect)

        with pytest.raises(
            ActionAuditSchemaError, match="audit event constructor changed",
        ):
            if operation == "append":
                audit.append(call, outcome="recorded")
            else:
                audit.events()

    assert descriptor_calls == []
    assert connection_calls == []
