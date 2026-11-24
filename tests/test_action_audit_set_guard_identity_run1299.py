"""Run1299: ActionAudit pins its class-level assignment guard before append I/O."""

from __future__ import annotations

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call() -> ToolCall:
    return ToolCall(
        "fixture.audit",
        "fixture.read",
        "synthetic:scope",
        {"n": 1},
    )


def test_replaced_class_assignment_guard_is_rejected_before_sqlite_or_clock(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock_calls: list[bool] = []
    audit = SQLiteActionAudit(
        tmp_path / "audit.sqlite3",
        clock_ms=lambda: clock_calls.append(True) or 100,
    )
    database_calls: list[bool] = []
    guard_calls: list[tuple[object, ...]] = []

    def forbidden_connect(*_args: object, **_kwargs: object) -> None:
        database_calls.append(True)
        raise AssertionError("changed ActionAudit class must be rejected before SQLite")

    def substituted_setattr(*args: object, **_kwargs: object) -> None:
        guard_calls.append(args)
        raise AssertionError("substituted ActionAudit assignment guard must not execute")

    monkeypatch.setattr(audit, "_connect", forbidden_connect)
    monkeypatch.setattr(SQLiteActionAudit, "__setattr__", substituted_setattr)

    with pytest.raises(
        ActionAuditSchemaError,
        match="action audit implementation changed",
    ):
        audit.append(_call(), outcome="synthetic-safe")

    assert guard_calls == []
    assert database_calls == []
    assert clock_calls == []
