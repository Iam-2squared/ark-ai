"""Outcome budget globals remain pinned before Action Audit opens SQLite."""

from __future__ import annotations

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call() -> ToolCall:
    return ToolCall(
        "fixture.audit", "fixture.read", "synthetic:scope", {"fixture": "only"},
    )


def test_coordinated_outcome_budget_rebinding_fails_before_database_or_clock(
    tmp_path, monkeypatch,
):
    clock_calls = []
    audit = SQLiteActionAudit(
        tmp_path / "audit.sqlite3",
        clock_ms=lambda: clock_calls.append(True) or 100,
    )

    # Rebind both limits and the tuple they were compared against. The
    # validator function identity itself remains unchanged.
    monkeypatch.setattr(audit_module, "_MAX_AUDIT_OUTCOME_CHARS", 1024)
    monkeypatch.setattr(audit_module, "_MAX_AUDIT_OUTCOME_BYTES", 1024)
    monkeypatch.setattr(
        audit_module, "_ORIGINAL_AUDIT_OUTCOME_BUDGETS", (1024, 1024),
    )

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("tampered budget must be rejected before SQLite")

    monkeypatch.setattr(audit, "_connect", forbidden_connect)
    with pytest.raises(ActionAuditSchemaError, match="digest callback changed"):
        audit.append(_call(), outcome="x" * 257)
    assert clock_calls == []
