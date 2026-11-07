"""Multi-step retained READ evidence never completes a missing ancestor.

All cases run on local disconnected SQLite journals, with a backend that
throws on invocation. These are correlations, not independent execution proof.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_planner_success_bundle_review as bundle
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

FIRST = "step_" + "a" * 16
SECOND = "step_" + "b" * 16


class _NoBackend:
    calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("offline bundle attempted real tool execution")


def _multi(tmp_path, *, finish_second=True):
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "scope:private", 200),)
    steps = (
        PlanStep(
            FIRST,
            ToolCall("math.sum", "math.sum", "scope:private", {"values": [1, 2]}),
        ),
        PlanStep(
            SECOND,
            ToolCall("math.sum", "math.sum", "scope:private", {"values": [3, 4]}),
            (FIRST,),
        ),
    )
    read_journal = DisconnectedReadJournal.create(tmp_path / "read.sqlite")
    retained = genesis_witness()
    payloads = []
    for step, value in zip(steps, ("a", "b"), strict=True):
        request = DisconnectedToolRequest(
            "req_" + value * 32, "math.sum",
            '{"values":[' + ("1,2" if value == "a" else "3,4") + "]}",
        )
        result = execute_disconnected_fixture_tool(request)
        binding = bind_disconnected_fixture_result(request, result)
        link = review_registered_disconnected_fixture(
            registry, gate, step.call, grants, step.step_id,
            request, result, binding, observed_at_ms=50,
        )
        retained = read_journal.append(
            prepare_disconnected_read_receipt(step.step_id, request, result, binding),
            retained,
        )
        payloads.append((step, request, result, binding, link))

    planner = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps)
    genesis = planner.recover().tail
    planner.append(FIRST, StepState.RUNNING, expected_revision=0, at_ms=50, retained=genesis)
    planner.append(FIRST, StepState.SUCCEEDED, expected_revision=1, at_ms=51, retained=genesis)
    if finish_second:
        planner.append(
            SECOND, StepState.RUNNING, expected_revision=0, at_ms=52, retained=genesis,
        )
        planner.append(
            SECOND, StepState.SUCCEEDED, expected_revision=1, at_ms=53, retained=genesis,
        )
    recovered = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps).recover(
        retained=genesis,
    )
    evidence = []
    for step, request, result, binding, link in payloads:
        reviewed = review_retained_registered_receipt(
            read_journal, retained, link, registry, gate, step.call,
            grants, step.step_id, request, result, binding, observed_at_ms=50,
        )
        evidence.append((link, reviewed))
    return read_journal, steps, recovered, tuple(evidence), backend


def test_two_step_bundle_requires_both_distinct_receipts_in_canonical_order(tmp_path):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    try:
        result = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[::-1],
        )
        assert result.step_ids == (FIRST, SECOND)
        assert result == bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        assert len(result.correlation_sha256s) == 2
        assert result.external_execution_proven is False
        assert result.write_authorized is False
        assert result.dispatch_authorized is False
        assert result.automatic_replay_authorized is False
        with pytest.raises(DisconnectedPlannerProjectionRejected):
            project_disconnected_planner_fence(
                recovered, steps, ((FIRST, "READ"), (SECOND, "READ")),
            )
        assert backend.calls == 0
    finally:
        journal.close()


@pytest.mark.parametrize(
    "fault",
    ("missing_ancestor", "missing_successor", "duplicate", "wrong_step",
     "wrong_registry", "no_receipts", "non_tuple_pair", "duplicate_fixture"),
)
def test_incomplete_or_mismatched_multistep_evidence_is_not_success(
    tmp_path, fault,
):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    try:
        if fault == "missing_ancestor":
            evidence = (evidence[1],)
        elif fault == "missing_successor":
            evidence = (evidence[0],)
        elif fault == "duplicate":
            evidence = (evidence[0], evidence[0])
        elif fault == "wrong_step":
            evidence = ((replace(evidence[0][0], step_id=SECOND), evidence[0][1]),
                        evidence[1])
        elif fault == "wrong_registry":
            evidence = ((replace(evidence[0][0], registry_revision="wrong"), evidence[0][1]),
                        evidence[1])
        elif fault == "no_receipts":
            evidence = ()
        elif fault == "non_tuple_pair":
            evidence = ([*evidence[0]], evidence[1])
        else:
            evidence = (
                evidence[0],
                (replace(evidence[1][0], fixture_request_id=evidence[0][0].fixture_request_id),
                 evidence[1][1]),
            )
        with pytest.raises(bundle.PlannerReadSuccessBundleRejected):
            bundle.review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        journal.close()


def test_succeeded_ancestor_with_pending_descendant_is_only_partial_evidence(tmp_path):
    journal, steps, recovered, evidence, backend = _multi(tmp_path, finish_second=False)
    try:
        result = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, (evidence[0],),
        )
        assert result.step_ids == (FIRST,)
        with pytest.raises(bundle.PlannerReadSuccessBundleRejected):
            bundle.review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        journal.close()


def test_replaced_bundle_authority_carrier_rejected_before_read_review(
    tmp_path, monkeypatch,
):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                bundle.PlannerReadSuccessBundle,
                "dispatch_authorized", property(lambda _: True),
            )
            with pytest.raises(
                bundle.PlannerReadSuccessBundleRejected, match="carrier changed",
            ):
                bundle.review_synthetic_succeeded_read_bundle(
                    recovered, steps, evidence,
                )
        assert backend.calls == 0
    finally:
        journal.close()
