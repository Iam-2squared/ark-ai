"""Query-only startup review binds schema and registered READ identity."""

from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_local_readiness as mod
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_read_preflight import DisconnectedReadPreflight
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class NoDispatchBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("startup review must never execute tools")


@pytest.fixture
def case():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("PRAGMA query_only=ON")
    seal = capture_disconnected_sqlite_schema(conn)
    backend = NoDispatchBackend()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((PlanStep(
        "root", ToolCall("reader", "fixture.read", "test", {"value": 1}),
    ),))
    args = (conn, seal, plan, registry, PermissionGate(), (
        CapabilityGrant("fixture.read", "test", 500),
    ))
    yield args, backend
    conn.close()


def _review(args):
    return mod.review_disconnected_local_readiness(*args, observed_at_ms=100)


def test_synthetic_startup_diagnostic_is_deterministic_and_denies_actions(case):
    args, backend = case
    result = _review(args)
    assert result == _review(args)
    assert result.ready_step_ids == ("root",)
    assert len(result.review_digest) == 64
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.source_authenticated is False
    assert result.cross_store_atomicity_proven is False
    assert backend.calls == 0


def test_stale_schema_is_denied_without_application_data_read(case):
    args, backend = case
    conn = args[0]
    conn.execute("PRAGMA query_only=OFF")
    conn.execute("CREATE TABLE second(id TEXT)")
    conn.execute("PRAGMA query_only=ON")
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="schema"):
        _review(args)
    assert backend.calls == 0


def test_requires_query_only_sqlite_connection(case):
    args, backend = case
    args[0].execute("PRAGMA query_only=OFF")
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="schema"):
        _review(args)
    assert backend.calls == 0


def test_nonread_registered_tool_cannot_pass_startup(case):
    args, backend = case
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.WRITE, "mock", backend),
    ))
    replaced = (*args[:3], registry, *args[4:])
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="preflight"):
        _review(replaced)
    assert backend.calls == 0


@pytest.mark.parametrize("field", (
    "dispatch_authorized",
    "external_result_verified",
    "authenticated_clock_or_consent",
    "automatic_replay_authorized",
))
def test_forged_preflight_authority_denies_startup(case, monkeypatch, field):
    args, backend = case
    monkeypatch.setattr(
        DisconnectedReadPreflight, field, property(lambda _report: True),
    )
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="receipt"):
        _review(args)
    assert backend.calls == 0


def test_plan_transition_during_schema_callback_refuses_mixed_epoch(case, monkeypatch):
    args, backend = case
    plan = args[2]
    original = mod.review_disconnected_sqlite_schema

    def drift(connection, retained):
        result = original(connection, retained)
        plan.transition("root", StepState.RUNNING, expected_revision=0)
        return result

    monkeypatch.setattr(mod, "review_disconnected_sqlite_schema", drift)
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="epoch"):
        _review(args)
    assert backend.calls == 0


@pytest.mark.parametrize("field", (
    "startup_authorized",
    "dispatch_authorized",
    "source_authenticated",
    "cross_store_atomicity_proven",
))
def test_forged_report_authority_is_denied(case, monkeypatch, field):
    args, backend = case
    monkeypatch.setattr(
        mod.DisconnectedLocalReadiness, field, property(lambda _report: True),
    )
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="report"):
        _review(args)
    assert backend.calls == 0
