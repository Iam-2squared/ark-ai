"""ActionAudit receipts reject executable slotted descriptors before reading them.

All callers, rows and clocks are local fixtures. An audit event does not
authenticate the writer, trusted time, human consent or any external effect.
"""

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _case(tmp_path):
    audit = audit_module.SQLiteActionAudit(
        tmp_path / "audit.sqlite", clock_ms=lambda: 100,
    )
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 1})
    return audit, call


@pytest.mark.parametrize("field", (
    "event_id", "request_id", "occurred_at_ms", "__getattribute__",
))
@pytest.mark.parametrize("operation", ("append", "events"))
def test_preinstalled_receipt_descriptor_denied_before_sqlite_or_execution(
    tmp_path, monkeypatch, field, operation,
):
    audit, call = _case(tmp_path)
    if operation == "events":
        audit.append(call, outcome="recorded")
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("forged receipt lookup")
        raise AssertionError("forged receipt lookup must never execute")

    def no_sqlite(*_args, **_kwargs):
        raise AssertionError("receipt check must precede SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(
            audit_module.ActionAuditEvent, field,
            forbidden if field == "__getattribute__" else property(forbidden),
        )
        patch.setattr(
            audit,
            "_connect" if operation == "append" else "_connect_readonly",
            no_sqlite,
        )
        with pytest.raises(
            ActionAuditSchemaError, match="audit event constructor changed",
        ):
            if operation == "append":
                audit.append(call, outcome="recorded")
            else:
                audit.events()
    assert invoked == []
    assert len(audit.events()) == (1 if operation == "events" else 0)


@pytest.mark.parametrize("field", ("event_id", "__getattribute__"))
def test_clock_callback_cannot_install_receipt_descriptor_before_commit(
    tmp_path, monkeypatch, field,
):
    audit, call = _case(tmp_path)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("forged receipt lookup")
        raise AssertionError("forged receipt lookup must never execute")

    with monkeypatch.context() as patch:
        def clock():
            patch.setattr(
                audit_module.ActionAuditEvent, field,
                forbidden if field == "__getattribute__" else property(forbidden),
            )
            return 100

        patch.setattr(audit, "_clock_ms", clock)
        with pytest.raises(
            ActionAuditSchemaError, match="audit event constructor changed",
        ):
            audit.append(call, outcome="recorded")
    assert invoked == []
    assert audit.events() == []


@pytest.mark.parametrize("field", ("scope", "__getattribute__"))
def test_read_schema_callback_cannot_install_receipt_descriptor_for_hydration(
    tmp_path, monkeypatch, field,
):
    audit, call = _case(tmp_path)
    original = audit.append(call, outcome="recorded")
    invoked = []
    native_review = audit_module._validate_v1_schema

    def forbidden(*_args, **_kwargs):
        invoked.append("forged receipt lookup")
        raise AssertionError("forged receipt lookup must never execute")

    with monkeypatch.context() as patch:
        def review(conn):
            native_review(conn)
            patch.setattr(
                audit_module.ActionAuditEvent, field,
                forbidden if field == "__getattribute__" else property(forbidden),
            )

        patch.setattr(audit_module, "_validate_v1_schema", review)
        with pytest.raises(
            ActionAuditSchemaError, match="audit event constructor changed",
        ):
            audit.events()
    assert invoked == []
    assert audit.events() == [original]
