"""Detached startup readiness must close input/result epochs after authority reads."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_local_readiness import (
    DisconnectedLocalReadiness,
    DisconnectedLocalReadinessRejected,
    review_disconnected_local_readiness,
)
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class NoDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: object) -> None:
        self.calls += 1
        raise AssertionError("startup is inspection-only")


@pytest.fixture
def offline():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY)")
    connection.execute("PRAGMA query_only=ON")
    seal = capture_disconnected_sqlite_schema(connection)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("reader", "local.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("root", ToolCall("reader", "local.read", "local", {"id": 1})),
    ))
    arguments = (
        connection, seal, plan, registry, PermissionGate(),
        (CapabilityGrant("local.read", "local", 200),),
    )
    yield arguments, backend
    connection.close()


def review(arguments):
    return review_disconnected_local_readiness(*arguments, observed_at_ms=100)


def test_normal_readiness_remains_non_authorizing(offline):
    args, backend = offline
    result = review(args)
    assert result.ready_step_ids == ("root",)
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.source_authenticated is False
    assert result.cross_store_atomicity_proven is False
    assert backend.calls == 0


@pytest.mark.parametrize("mutation", (
    "plan", "retained_seal", "result_digest", "same_value_ready_ids",
))
def test_last_false_authority_getter_cannot_change_startup_basis_or_result(
    offline, monkeypatch, mutation,
):
    args, backend = offline
    seal, plan = args[1], args[2]

    def late_side_effect(report):
        if mutation == "plan":
            plan.transition("root", StepState.RUNNING, expected_revision=0)
        elif mutation == "retained_seal":
            object.__setattr__(seal, "schema_sha256", "0" * 64)
        elif mutation == "result_digest":
            object.__setattr__(report, "review_digest", "0" * 64)
        else:
            equal = tuple(list(report.ready_step_ids))
            assert equal == report.ready_step_ids
            assert equal is not report.ready_step_ids
            object.__setattr__(report, "ready_step_ids", equal)
        return False

    monkeypatch.setattr(
        DisconnectedLocalReadiness,
        "cross_store_atomicity_proven",
        property(late_side_effect),
    )
    with pytest.raises(DisconnectedLocalReadinessRejected, match="epoch|report"):
        review(args)
    assert backend.calls == 0
