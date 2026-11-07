"""Exact-step synthetic SUCCEEDED is only an inert cross-journal diagnostic.

Two separate local SQLite journals are reviewed; no atomic cross-store commit,
external tool result, independent actor identity or permission is established.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_planner_success_receipt_review as join
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_registered_receipt_review import (
    review_retained_registered_receipt,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

STEP = "step_" + "a" * 16


class _NeverBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("offline success review dispatched a backend")


def _case(tmp_path, terminal=StepState.SUCCEEDED):
    backend = _NeverBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    call = ToolCall("math.sum", "math.sum", "scope:private", {"values": [1, 2]})
    grants = (CapabilityGrant("math.sum", "scope:private", 100),)
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    link = review_registered_disconnected_fixture(
        registry, gate, call, grants, STEP, request, result, binding,
        observed_at_ms=50,
    )
    read_journal = DisconnectedReadJournal.create(tmp_path / "registered-read.sqlite")
    retained = read_journal.append(
        prepare_disconnected_read_receipt(STEP, request, result, binding),
        genesis_witness(),
    )
    steps = (PlanStep(STEP, call),)
    plan_path = tmp_path / "planner.sqlite"
    planner = SyntheticPlanJournal(plan_path, steps)
    genesis = planner.recover().tail
    if terminal is not None:
        planner.append(
            STEP, StepState.RUNNING, expected_revision=0, at_ms=50,
            retained=genesis,
        )
        if terminal is not StepState.RUNNING:
            planner.append(
                STEP, terminal, expected_revision=1, at_ms=51,
                retained=genesis,
            )
    recovered = SyntheticPlanJournal(plan_path, steps).recover(retained=genesis)
    read_review = review_retained_registered_receipt(
        read_journal, retained, link, registry, gate, call, grants,
        STEP, request, result, binding, observed_at_ms=50,
    )
    return read_journal, steps, recovered, link, read_review, backend


def test_cross_journal_read_success_is_exact_and_never_permission(tmp_path):
    read_journal, steps, recovered, link, reviewed, backend = _case(tmp_path)
    try:
        correlation = join.review_synthetic_succeeded_read_correlation(
            recovered, steps, link, reviewed,
        )
        assert correlation.step_id == STEP
        assert correlation.topology_digest == recovered.tail.topology_digest
        assert correlation.status_digest == recovered.tail.status_digest
        assert correlation.action_request_id == steps[0].call.request_id
        assert correlation.registry_revision == link.registry_revision
        assert correlation.result_sha256 == link.result_digest
        assert correlation.journal_tip_sha256 == reviewed.journal_tip_sha256
        assert correlation == join.review_synthetic_succeeded_read_correlation(
            recovered, steps, link, reviewed,
        )
        assert correlation.independent_execution_proven is False
        assert correlation.external_outcome_verified is False
        assert correlation.dispatch_authorized is False
        assert correlation.automatic_replay_authorized is False
        # The regular recovery path remains closed to all SUCCEEDED claims.
        with pytest.raises(DisconnectedPlannerProjectionRejected):
            project_disconnected_planner_fence(
                recovered, steps, ((STEP, "READ"),),
            )
        assert backend.calls == 0
    finally:
        read_journal.close()


@pytest.mark.parametrize(
    "terminal",
    (None, StepState.RUNNING, StepState.FAILED, StepState.CANCELLED),
)
def test_unfinished_unknown_or_terminal_non_success_never_uses_read_receipt(
    tmp_path, terminal,
):
    read_journal, steps, recovered, link, reviewed, backend = _case(
        tmp_path, terminal=terminal,
    )
    try:
        with pytest.raises(join.PlannerSucceededReadCorrelationRejected):
            join.review_synthetic_succeeded_read_correlation(
                recovered, steps, link, reviewed,
            )
        assert backend.calls == 0
    finally:
        read_journal.close()


@pytest.mark.parametrize("corruption", ("call", "link", "review", "missing"))
def test_mismatched_step_call_link_or_receipt_cannot_complete_read(
    tmp_path, corruption,
):
    read_journal, steps, recovered, link, reviewed, backend = _case(tmp_path)
    try:
        if corruption == "call":
            steps = (PlanStep(
                STEP,
                ToolCall("math.sum", "math.sum", "scope:private", {"values": [9]}),
            ),)
        elif corruption == "link":
            link = replace(link, action_request_id="act_" + "f" * 64)
        elif corruption == "review":
            reviewed = replace(reviewed, link_sha256="f" * 64)
        else:
            reviewed = None
        with pytest.raises(join.PlannerSucceededReadCorrelationRejected):
            join.review_synthetic_succeeded_read_correlation(
                recovered, steps, link, reviewed,
            )
        assert backend.calls == 0
    finally:
        read_journal.close()


def test_changed_correlation_result_denial_rejected_before_result_construction(
    tmp_path, monkeypatch,
):
    read_journal, steps, recovered, link, reviewed, backend = _case(tmp_path)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                join.PlannerSucceededReadCorrelation,
                "dispatch_authorized", property(lambda _: True),
            )
            with pytest.raises(
                join.PlannerSucceededReadCorrelationRejected,
                match="carrier changed",
            ):
                join.review_synthetic_succeeded_read_correlation(
                    recovered, steps, link, reviewed,
                )
        assert backend.calls == 0
    finally:
        read_journal.close()


@pytest.mark.parametrize(
    "primitive",
    ("hashlib_module", "json_module", "sha256", "dumps",
     "domain", "equal_domain_replacement"),
)
def test_standalone_read_correlation_pins_digest_before_receipt_access(
    tmp_path, monkeypatch, primitive,
):
    journal, steps, recovered, link, reviewed, backend = _case(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("untrusted correlation digest callback executed")

    try:
        with monkeypatch.context() as patch:
            if primitive == "hashlib_module":
                patch.setattr(join, "hashlib", object())
            elif primitive == "json_module":
                patch.setattr(join, "json", object())
            elif primitive == "sha256":
                patch.setattr(join.hashlib, "sha256", forbidden)
            elif primitive == "dumps":
                patch.setattr(join.json, "dumps", forbidden)
            elif primitive == "domain":
                patch.setattr(join, "_DOMAIN", b"altered-local-correlation")
            else:
                equal_value = bytes(bytearray(join._DOMAIN))
                assert equal_value == join._DOMAIN
                assert equal_value is not join._DOMAIN
                patch.setattr(join, "_DOMAIN", equal_value)
            with pytest.raises(
                join.PlannerSucceededReadCorrelationRejected,
                match="correlation digest implementation or domain changed",
            ):
                join.review_synthetic_succeeded_read_correlation(
                    recovered, steps, link, reviewed,
                )
        assert calls == []
        restored = join.review_synthetic_succeeded_read_correlation(
            recovered, steps, link, reviewed,
        )
        assert restored.step_id == STEP
        assert restored.dispatch_authorized is False
        assert restored.automatic_replay_authorized is False
        assert backend.calls == 0
    finally:
        journal.close()
