"""Disconnected startup must never execute mutable schema-seal equality.

Schema equality can be replaced in-process; only the four exact scalar
snapshot fields can establish this local consistency check. This test
does not authorize a tool, trust a clock or prove cross-store atomicity.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_local_readiness import (
    DisconnectedLocalReadinessRejected,
    review_disconnected_local_readiness,
)
from ark.disconnected_sqlite_schema_probe import (
    DisconnectedSQLiteSchemaSeal,
    capture_disconnected_sqlite_schema,
)


class _NoDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("disconnected readiness cannot execute a backend")


@pytest.mark.parametrize("forgery", ("raise", "always-true", "always-false"))
def test_startup_never_calls_mutable_schema_equality(
    monkeypatch: pytest.MonkeyPatch, forgery: str,
) -> None:
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY)")
        connection.execute("PRAGMA query_only=ON")
        seal = capture_disconnected_sqlite_schema(connection)
        backend = _NoDispatch()
        registry = ToolRegistry((
            ToolRegistration("reader", "local.read", Effect.READ, "mock", backend),
        ))
        plan = PlanGraph((
            PlanStep("root", ToolCall("reader", "local.read", "fixture", {})),
        ))
        grants = (CapabilityGrant("local.read", "fixture", 500),)
        calls: list[str] = []

        def trap(_self: object, _other: object) -> bool:
            calls.append("unexpected-equality")
            if forgery == "raise":
                raise AssertionError("schema __eq__ must not be invoked")
            return forgery == "always-true"

        monkeypatch.setattr(DisconnectedSQLiteSchemaSeal, "__eq__", trap)
        args = (connection, seal, plan, registry, PermissionGate(), grants)
        report = review_disconnected_local_readiness(
            *args, observed_at_ms=100,
        )
        assert report.ready_step_ids == ("root",)
        assert report.startup_authorized is False
        assert report.dispatch_authorized is False
        assert report.cross_store_atomicity_proven is False
        assert calls == []
        assert backend.calls == 0

        # A forged always-true equality must not conceal schema change.
        connection.execute("PRAGMA query_only=OFF")
        connection.execute("CREATE TABLE changed(id TEXT)")
        connection.execute("PRAGMA query_only=ON")
        with pytest.raises(DisconnectedLocalReadinessRejected, match="schema"):
            review_disconnected_local_readiness(*args, observed_at_ms=100)
        assert calls == []
        assert backend.calls == 0
