"""Deny replaced startup receipt slots before any fixture metadata read."""

from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_local_readiness as local
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class _NoDispatch:
    calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("startup diagnostic cannot dispatch")


@pytest.fixture
def startup():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY)")
    conn.execute("PRAGMA query_only=ON")
    retained = capture_disconnected_sqlite_schema(conn)
    backend = _NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    graph = PlanGraph((
        PlanStep("root", ToolCall("reader", "fixture.read", "test", {"value": 1})),
    ))
    try:
        yield (
            (conn, retained, graph, registry, PermissionGate(),
             (CapabilityGrant("fixture.read", "test", 500),)),
            backend,
        )
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("carrier", "name"),
    (
        *((local._SCHEMA_TYPE, name) for name in (
            "schema_sha256", "object_count", "user_version", "schema_version",
        )),
        *((local._PREFLIGHT_TYPE, name) for name in (
            "topology_digest", "status_digest", "registry_revision",
            "grant_fingerprint", "ready_step_ids", "ready_bound_ids",
            "fingerprint",
        )),
    ),
)
def test_replaced_receipt_field_never_reads_private_data(
    startup, monkeypatch, carrier, name,
):
    args, backend = startup
    seen = []

    def poisoned(_self):
        seen.append(name)
        raise AssertionError("forged receipt field must not run")

    monkeypatch.setattr(carrier, name, property(poisoned))
    with pytest.raises(
        local.DisconnectedLocalReadinessRejected, match="receipt.*carrier"
    ):
        local.review_disconnected_local_readiness(*args, observed_at_ms=100)
    assert seen == []
    assert backend.calls == 0


@pytest.mark.parametrize("name", (
    "__getattribute__", "__getattr__", "__init__",
))
@pytest.mark.parametrize("carrier", (local._SCHEMA_TYPE, local._PREFLIGHT_TYPE))
def test_replaced_receipt_lookup_hooks_denied_before_callbacks(
    startup, monkeypatch, carrier, name,
):
    args, backend = startup
    seen = []

    def poisoned(*_args, **_kwargs):
        seen.append(name)
        raise AssertionError("forged lookup hook must not execute")

    monkeypatch.setattr(carrier, name, poisoned, raising=False)
    with pytest.raises(
        local.DisconnectedLocalReadinessRejected, match="receipt.*carrier"
    ):
        local.review_disconnected_local_readiness(*args, observed_at_ms=100)
    assert seen == []
    assert backend.calls == 0


def test_unmodified_startup_retains_deny_only_result(startup):
    args, backend = startup
    result = local.review_disconnected_local_readiness(*args, observed_at_ms=100)
    assert result.ready_step_ids == ("root",)
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.source_authenticated is False
    assert result.cross_store_atomicity_proven is False
    assert backend.calls == 0
