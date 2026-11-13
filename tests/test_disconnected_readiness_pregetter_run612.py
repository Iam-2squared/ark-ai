"""Startup inspection refuses dynamic denial rebinding and constructors.

These synthetic fixtures have query-only SQLite and a backend that must never
execute. The readiness result carries no authority to dispatch or disclose.
"""

import hashlib
import sqlite3

import pytest

import ark.disconnected_local_readiness as mod
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("startup must remain disconnected")


@pytest.fixture
def case():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY)")
    conn.execute("PRAGMA query_only=ON")
    seal = capture_disconnected_sqlite_schema(conn)
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep(
            "root", ToolCall("reader", "fixture.read", "test", {"id": 1}),
        ),
    ))
    args = (
        conn, seal, plan, registry, PermissionGate(),
        (CapabilityGrant("fixture.read", "test", 200),),
    )
    yield args, backend
    conn.close()


@pytest.mark.parametrize("stage", ("schema", "preflight", "report"))
def test_first_denial_read_cannot_activate_second_descriptor(
    case, monkeypatch, stage,
):
    args, backend = case
    if stage == "schema":
        cls = mod._SCHEMA_TYPE
        first, second = mod._SCHEMA_DENIALS[:2]
    elif stage == "preflight":
        cls = mod._PREFLIGHT_TYPE
        first, second = mod._PREFLIGHT_DENIALS[:2]
    else:
        cls = mod._REPORT_TYPE
        first, second = mod._REPORT_DENIALS[:2]

    original_getattribute = cls.__getattribute__
    observed = {"injection": 0, "evil": 0}

    def evil(_value):
        observed["evil"] += 1
        return False

    def reentrant_getattribute(self, name):
        if name == first and observed["injection"] == 0:
            observed["injection"] += 1
            monkeypatch.setattr(cls, second, property(evil))
        return original_getattribute(self, name)

    monkeypatch.setattr(cls, "__getattribute__", reentrant_getattribute)
    with pytest.raises(mod.DisconnectedLocalReadinessRejected, match="authority|denied"):
        mod.review_disconnected_local_readiness(*args, observed_at_ms=100)
    # Startup now pins schema, READ preflight, and report carrier descriptors
    # before any per-instance getter. All three substituted __getattribute__
    # implementations must be rejected without even entering the first getter.
    assert observed["injection"] == 0
    assert observed["evil"] == 0
    assert backend.calls == 0


def test_posthash_global_report_constructor_replacement_is_never_called(
    case, monkeypatch,
):
    args, backend = case
    original_sha256 = hashlib.sha256
    observed = {"ctor": 0, "mutation": 0}

    def evil_constructor(*_args):
        observed["ctor"] += 1
        raise AssertionError("foreign constructor invoked")

    def injected_sha256(payload=b""):
        if payload.startswith(mod._DOMAIN) and not observed["mutation"]:
            observed["mutation"] += 1
            monkeypatch.setattr(
                mod, "DisconnectedLocalReadiness", evil_constructor,
            )
        return original_sha256(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", injected_sha256)
    with pytest.raises(
        mod.DisconnectedLocalReadinessRejected,
        match="startup digest dependencies changed",
    ):
        mod.review_disconnected_local_readiness(*args, observed_at_ms=100)
    assert observed == {"ctor": 0, "mutation": 0}
    assert backend.calls == 0


def test_valid_inspection_is_still_read_only(case):
    args, backend = case
    result = mod.review_disconnected_local_readiness(
        *args, observed_at_ms=100,
    )
    assert result.ready_step_ids == ("root",)
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.cross_store_atomicity_proven is False
    assert backend.calls == 0
