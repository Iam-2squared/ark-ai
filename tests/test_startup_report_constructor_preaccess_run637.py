"""Startup report identity must be original before any schema review callback."""

from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_local_readiness as readiness
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("readiness cannot dispatch a backend")


@pytest.mark.parametrize("hook", ("__init__", "review_digest", "ready_step_ids"))
def test_injected_startup_report_hook_never_executes_before_inspection(
    monkeypatch, hook,
):
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY)")
        conn.execute("PRAGMA query_only=ON")
        seal = capture_disconnected_sqlite_schema(conn)
        backend = NoBackend()
        registry = ToolRegistry((
            ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
        ))
        plan = PlanGraph((
            PlanStep("root", ToolCall("reader", "fixture.read", "fixture", {"id": 1})),
        ))
        visited = []

        def executable(*_args, **_kwargs):
            visited.append("injected")
            raise AssertionError("injected startup hook executed")

        def schema(*_args, **_kwargs):
            visited.append("schema-read")
            raise AssertionError("startup inspected schema before original DTO contract")

        if hook == "__init__":
            monkeypatch.setattr(readiness.DisconnectedLocalReadiness, hook, executable)
        else:
            monkeypatch.setattr(
                readiness.DisconnectedLocalReadiness, hook, property(executable),
            )
        monkeypatch.setattr(readiness, "review_disconnected_sqlite_schema", schema)
        with pytest.raises(
            readiness.DisconnectedLocalReadinessRejected,
            match="startup report authority definition changed",
        ):
            readiness.review_disconnected_local_readiness(
                conn, seal, plan, registry, PermissionGate(),
                (CapabilityGrant("fixture.read", "fixture", 200),),
                observed_at_ms=100,
            )
        assert visited == []
        assert backend.calls == 0
