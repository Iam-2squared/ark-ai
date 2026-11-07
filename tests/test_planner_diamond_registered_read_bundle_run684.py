"""Every successful branch of a diamond DAG needs its own READ receipt.

All results are offline fixtures, not proof that a real tool executed. A
complete local bundle still cannot authorize dispatch or automatic replay.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_planner_success_bundle_review as bundle
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_read_journal import DisconnectedReadJournal, genesis_witness
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

A, B, C, D = ("step_" + letter * 16 for letter in "abcd")


class NoBackend:
    calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("READ evidence bundle invoked a real tool")


def _diamond(tmp_path, *, finish_last=True):
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "scope:private", 200),)
    steps = (
        PlanStep(A, ToolCall("math.sum", "math.sum", "scope:private", {"values": [1, 2]})),
        PlanStep(B, ToolCall("math.sum", "math.sum", "scope:private", {"values": [2, 3]}),
                 (A,)),
        PlanStep(C, ToolCall("math.sum", "math.sum", "scope:private", {"values": [3, 4]}),
                 (A,)),
        PlanStep(D, ToolCall("math.sum", "math.sum", "scope:private", {"values": [4, 5]}),
                 (B, C)),
    )
    read_journal = DisconnectedReadJournal.create(tmp_path / "read.sqlite")
    retained = genesis_witness()
    payloads = []
    for i, (step, letter) in enumerate(zip(steps, "abcd", strict=True), start=1):
        request = DisconnectedToolRequest(
            "req_" + letter * 32,
            "math.sum",
            '{"values":[' + str(i) + "," + str(i + 1) + "]}",
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

    planner_path = tmp_path / "planner.sqlite"
    planner = SyntheticPlanJournal(planner_path, steps)
    genesis = planner.recover().tail
    for i, step in enumerate(steps):
        if not finish_last and step.step_id == D:
            break
        planner.append(
            step.step_id, StepState.RUNNING,
            expected_revision=0, at_ms=50 + 2 * i, retained=genesis,
        )
        planner.append(
            step.step_id, StepState.SUCCEEDED,
            expected_revision=1, at_ms=51 + 2 * i, retained=genesis,
        )
    recovered = SyntheticPlanJournal(planner_path, steps).recover(retained=genesis)
    evidence = []
    for step, request, result, binding, link in payloads:
        reviewed = review_retained_registered_receipt(
            read_journal, retained, link, registry, gate, step.call,
            grants, step.step_id, request, result, binding, observed_at_ms=50,
        )
        evidence.append((link, reviewed))
    return read_journal, steps, recovered, tuple(evidence), backend


def test_four_success_diamond_requires_distinct_ancestor_and_sibling_receipts(tmp_path):
    journal, steps, recovered, evidence, backend = _diamond(tmp_path)
    try:
        ordered = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        reversed_order = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[::-1],
        )
        assert ordered == reversed_order
        assert ordered.step_ids == (A, B, C, D)
        assert len(set(ordered.correlation_sha256s)) == 4
        assert ordered.dispatch_authorized is False
        assert ordered.automatic_replay_authorized is False
        assert ordered.external_execution_proven is False
        assert backend.calls == 0
    finally:
        journal.close()


@pytest.mark.parametrize("missing", range(4))
def test_diamond_success_cannot_borrow_missing_branch_or_ancestor_receipt(
    tmp_path, missing,
):
    journal, steps, recovered, evidence, backend = _diamond(tmp_path)
    try:
        incomplete = tuple(pair for i, pair in enumerate(evidence) if i != missing)
        with pytest.raises(bundle.PlannerReadSuccessBundleRejected):
            bundle.review_synthetic_succeeded_read_bundle(
                recovered, steps, incomplete,
            )
        assert backend.calls == 0
    finally:
        journal.close()


def test_diamond_pending_terminal_requires_only_actual_success_evidence(tmp_path):
    journal, steps, recovered, evidence, backend = _diamond(
        tmp_path, finish_last=False,
    )
    try:
        partial = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[:3],
        )
        assert partial.step_ids == (A, B, C)
        assert partial.write_authorized is False
        with pytest.raises(bundle.PlannerReadSuccessBundleRejected):
            bundle.review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        journal.close()
