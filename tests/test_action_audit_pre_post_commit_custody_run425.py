"""Synthetic ActionAudit must reject drift before and after its COMMIT.

A failure AFTER COMMIT keeps the durable pre-action row. No test has an
actual executor or interprets a local audit receipt as external outcome.
"""

from pathlib import Path

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call():
    return ToolCall(
        "offline-writer", "mock.write", "fixture",
        {"private_fixture_marker": "never-in-durable-arguments"},
    )


def _equal_text(value):
    new = ("!" + value)[1:]
    assert new == value and new is not value
    return new


def test_equal_text_subject_rebind_during_clock_rolls_back_no_audit(tmp_path):
    call = _call()

    def clock():
        object.__setattr__(call, "tool", _equal_text(call.tool))
        return 20

    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=clock)
    with pytest.raises(ActionAuditSchemaError, match="changed during clock"):
        audit.append(call, outcome="synthetic_audit_before_mock")
    assert audit.events() == []


def test_equal_text_subject_rebind_after_sql_insert_rolls_back_both(tmp_path, monkeypatch):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    call = _call()
    native_open = audit._connect

    class ReentrantConnection:
        def __init__(self, conn):
            self.conn = conn

        def __enter__(self):
            self.conn.__enter__()
            return self

        def __exit__(self, *args):
            return self.conn.__exit__(*args)

        def close(self):
            self.conn.close()

        def execute(self, sql, *args):
            cursor = self.conn.execute(sql, *args)
            if sql.lstrip().startswith("INSERT INTO action_events"):
                object.__setattr__(call, "capability", _equal_text(call.capability))
            return cursor

    monkeypatch.setattr(
        audit, "_connect",
        lambda **kwargs: ReentrantConnection(native_open(**kwargs)),
    )
    with pytest.raises(ActionAuditSchemaError, match="changed before commit"):
        audit.append(call, outcome="synthetic_audit_before_mock")
    assert audit.events() == []


@pytest.mark.parametrize("mutation", (
    "source_path", "caller_equal_tool", "event_id", "event_scope",
    "event_equal_scope", "event_outcome", "event_timestamp",
))
def test_reentrant_receipt_constructor_refuses_clean_postcommit_result(
    tmp_path, monkeypatch, mutation,
):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    call = _call()
    original_path = audit.path
    original_tool = call.tool
    original_init = audit_module.ActionAuditEvent.__init__

    def reentrant_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if mutation == "source_path":
            audit.path = Path(str(audit.path))
        elif mutation == "caller_equal_tool":
            object.__setattr__(call, "tool", _equal_text(call.tool))
        elif mutation == "event_id":
            object.__setattr__(self, "event_id", self.event_id + 1)
        elif mutation == "event_scope":
            object.__setattr__(self, "scope", "retargeted-scope")
        elif mutation == "event_equal_scope":
            object.__setattr__(self, "scope", _equal_text(self.scope))
        elif mutation == "event_outcome":
            object.__setattr__(self, "outcome", "different-outcome")
        else:
            object.__setattr__(self, "occurred_at_ms", self.occurred_at_ms + 1)

    with monkeypatch.context() as patch:
        patch.setattr(audit_module.ActionAuditEvent, "__init__", reentrant_init)
        with pytest.raises(ActionAuditSchemaError, match="after commit"):
            audit.append(call, outcome="synthetic_audit_before_mock")
    audit.path = original_path
    object.__setattr__(call, "tool", original_tool)
    # The SQL row was already durably written: no false rollback statement,
    # no accidental second append, and no replay permission follows a
    # post-COMMIT diagnostic failure.
    persisted = audit.events()
    assert len(persisted) == 1
    assert persisted[0].event_id == 1
    assert persisted[0].tool == "offline-writer"
    assert persisted[0].capability == "mock.write"
    assert persisted[0].scope == "fixture"
    assert persisted[0].outcome == "synthetic_audit_before_mock"
    assert persisted[0].occurred_at_ms == 20
