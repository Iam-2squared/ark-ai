"""Synthetic ActionAudit clock callback mutation fence; no backend execution."""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call():
    return ToolCall(
        "fixture.read", "fixture.read", "synthetic:scope", {"label": "same"}
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("tool", "other.read"),
        ("capability", "other.read"),
        ("scope", "other:scope"),
        ("arguments", {"label": "changed"}),
        ("arguments", {"label": "same"}),
    ],
)
def test_clock_mutation_rolls_back_audit_and_refuses_mixed_identity(
    tmp_path, field, replacement
):
    call = _call()

    def clock():
        object.__setattr__(call, field, replacement)
        return 123

    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=clock)
    with pytest.raises(ActionAuditSchemaError, match="changed during clock"):
        audit.append(call, outcome="synthetic-only")
    assert audit.events() == []


def test_reflected_invalid_call_is_rejected_before_clock(tmp_path):
    call = _call()
    object.__setattr__(call, "tool", "")
    clock_calls = []

    def clock():
        clock_calls.append(1)
        return 123

    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=clock)
    with pytest.raises(ActionAuditSchemaError, match="identity is invalid"):
        audit.append(call, outcome="synthetic-only")
    assert clock_calls == []
    assert audit.events() == []


def test_normal_append_is_identical_to_persisted_event(tmp_path):
    call = _call()
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 123)
    event = audit.append(call, outcome="synthetic-only")
    assert audit.events() == [event]
    assert event.request_id == call.request_id
    assert event.arguments_sha256 == call.arguments_sha256
