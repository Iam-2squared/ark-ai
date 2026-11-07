"""Adversarial offline startup tests: preflight receipts are not authority."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

import ark.disconnected_local_readiness as readiness
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class ForbidDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: object) -> None:
        self.calls += 1
        raise AssertionError("the disconnected startup check dispatched a tool")


@pytest.fixture
def offline():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE local_fixture(id INTEGER PRIMARY KEY)")
    conn.execute("PRAGMA query_only=ON")
    seal = capture_disconnected_sqlite_schema(conn)
    backend = ForbidDispatch()
    registry = ToolRegistry((
        ToolRegistration("fixture", "offline.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("root", ToolCall("fixture", "offline.read", "local", {"a": 1})),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("offline.read", "local", 1000),)
    yield (conn, seal, plan, registry, gate, grants), backend
    conn.close()


def _review(args):
    return readiness.review_disconnected_local_readiness(
        *args, observed_at_ms=100,
    )


def test_unmodified_offline_preflight_still_matches_canonical_digest(offline):
    args, backend = offline
    first = _review(args)
    second = _review(args)
    assert first == second
    assert first.ready_step_ids == ("root",)
    assert len(first.review_digest) == 64
    assert first.startup_authorized is False
    assert first.dispatch_authorized is False
    assert first.source_authenticated is False
    assert first.cross_store_atomicity_proven is False
    assert backend.calls == 0


@pytest.mark.parametrize(("field", "forgery", "message"), (
    ("ready_step_ids", ("foreign",), "membership"),
    ("ready_step_ids", ("root", "root"), "receipt"),
    ("ready_bound_ids", ("bound_" + "0" * 64,), "binding"),
    ("grant_fingerprint", "0" * 64, "fingerprint"),
    ("fingerprint", "0" * 64, "fingerprint"),
))
def test_same_type_forged_preflight_fields_are_rejected(
    offline, monkeypatch, field, forgery, message,
):
    args, backend = offline
    real = readiness.preview_registered_read_plan

    def forged(*pos, **kw):
        return replace(real(*pos, **kw), **{field: forgery})

    monkeypatch.setattr(readiness, "preview_registered_read_plan", forged)
    with pytest.raises(readiness.DisconnectedLocalReadinessRejected, match=message):
        _review(args)
    assert backend.calls == 0


def test_same_type_receipt_with_consistent_forged_hash_is_still_rejected(
    offline, monkeypatch,
):
    args, backend = offline
    real = readiness.preview_registered_read_plan

    def forged(*pos, **kw):
        return replace(
            real(*pos, **kw),
            ready_bound_ids=("bound_" + "f" * 64,),
            grant_fingerprint="f" * 64,
            fingerprint="f" * 64,
        )

    monkeypatch.setattr(readiness, "preview_registered_read_plan", forged)
    with pytest.raises(readiness.DisconnectedLocalReadinessRejected, match="binding"):
        _review(args)
    assert backend.calls == 0


def test_new_ready_step_cannot_be_hidden_in_forged_receipt(offline, monkeypatch):
    args, backend = offline
    real = readiness.preview_registered_read_plan

    def forged(*pos, **kw):
        return replace(real(*pos, **kw), ready_step_ids=("hidden",))

    monkeypatch.setattr(readiness, "preview_registered_read_plan", forged)
    with pytest.raises(readiness.DisconnectedLocalReadinessRejected, match="membership"):
        _review(args)
    assert backend.calls == 0


def test_registry_is_read_only_and_no_one_shot_authorization_consumed(offline):
    args, backend = offline
    registry = args[3]
    revision = registry.revision
    report = _review(args)
    assert report.registry_revision == revision
    assert registry.revision == revision
    assert backend.calls == 0
