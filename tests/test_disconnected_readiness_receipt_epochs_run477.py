"""Receipt custody across two detached startup probes; no live dispatch."""

from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_local_readiness as mod
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.disconnected_read_preflight import DisconnectedReadPreflight
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_sqlite_schema_probe import (
    DisconnectedSQLiteSchemaSeal,
    capture_disconnected_sqlite_schema,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("no registered backend may be used")


@pytest.fixture
def case():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE fixture(key TEXT PRIMARY KEY)")
    conn.execute("PRAGMA query_only=ON")
    retained = capture_disconnected_sqlite_schema(conn)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("root", ToolCall("reader", "fixture.read", "test", {"x": 1})),
    ))
    args = (conn, retained, plan, registry, PermissionGate(), (
        CapabilityGrant("fixture.read", "test", 200),
    ))
    yield args, backend
    conn.close()


def _run(args):
    return mod.review_disconnected_local_readiness(*args, observed_at_ms=100)


@pytest.mark.parametrize("probe", (1, 2))
def test_rejects_duck_typed_schema_probe_receipt(case, monkeypatch, probe):
    args, backend = case
    original = mod.review_disconnected_sqlite_schema
    calls = 0

    def swapped(*parameters):
        nonlocal calls
        calls += 1
        result = original(*parameters)
        return object() if calls == probe else result

    monkeypatch.setattr(mod, "review_disconnected_sqlite_schema", swapped)
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="schema"):
        _run(args)
    assert backend.calls == 0


def test_first_probe_same_value_carrier_replaced_during_second(case, monkeypatch):
    args, backend = case
    original = mod.review_disconnected_sqlite_schema
    previous = []

    def swapped(*parameters):
        result = original(*parameters)
        if previous:
            old = previous[0].schema_sha256
            same_value = bytes(old, "ascii").decode("ascii")
            assert same_value == old and same_value is not old
            object.__setattr__(previous[0], "schema_sha256", same_value)
        else:
            previous.append(result)
        return result

    monkeypatch.setattr(mod, "review_disconnected_sqlite_schema", swapped)
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="stable"):
        _run(args)
    assert backend.calls == 0


@pytest.mark.parametrize("field", (
    "topology_digest",
    "status_digest",
    "registry_revision",
    "grant_fingerprint",
    "ready_step_ids",
    "ready_bound_ids",
    "fingerprint",
))
def test_preflight_same_value_carrier_swap_during_second_probe(
    case, monkeypatch, field,
):
    args, backend = case
    original_preflight = mod.preview_registered_read_plan
    original_probe = mod.review_disconnected_sqlite_schema
    captured = []
    probes = 0

    def preflight(*a, **kw):
        result = original_preflight(*a, **kw)
        captured.append(result)
        return result

    def probe(*a):
        nonlocal probes
        probes += 1
        result = original_probe(*a)
        if probes == 2:
            value = getattr(captured[0], field)
            if type(value) is tuple:
                equal = tuple(list(value))
            else:
                equal = bytes(value, "ascii").decode("ascii")
            assert equal == value and equal is not value
            object.__setattr__(captured[0], field, equal)
        return result

    monkeypatch.setattr(mod, "preview_registered_read_plan", preflight)
    monkeypatch.setattr(mod, "review_disconnected_sqlite_schema", probe)
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="receipt epoch"):
        _run(args)
    assert backend.calls == 0


@pytest.mark.parametrize("field", (
    "source_authenticated",
    "independent_custody_proven",
    "wal_snapshot_verified",
    "cross_store_atomicity_proven",
    "application_data_disclosure_authorized",
))
def test_schema_seal_cannot_claim_authority(case, monkeypatch, field):
    args, backend = case
    monkeypatch.setattr(
        DisconnectedSQLiteSchemaSeal, field, property(lambda _self: True),
    )
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="schema authority"):
        _run(args)
    assert backend.calls == 0


@pytest.mark.parametrize("field", (
    "dispatch_authorized",
    "external_result_verified",
    "authenticated_clock_or_consent",
    "automatic_replay_authorized",
))
def test_preflight_authority_forged_only_after_first_check(
    case, monkeypatch, field,
):
    args, backend = case
    original_probe = mod.review_disconnected_sqlite_schema
    probes = 0

    def probe(*a):
        nonlocal probes
        probes += 1
        result = original_probe(*a)
        if probes == 2:
            monkeypatch.setattr(
                DisconnectedReadPreflight, field,
                property(lambda _self: True),
            )
        return result

    monkeypatch.setattr(mod, "review_disconnected_sqlite_schema", probe)
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="receipt epoch"):
        _run(args)
    assert backend.calls == 0


def test_valid_receipt_remains_non_authorizing(case):
    args, backend = case
    result = _run(args)
    assert result.ready_step_ids == ("root",)
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert backend.calls == 0
