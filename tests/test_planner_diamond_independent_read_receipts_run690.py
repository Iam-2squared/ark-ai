"""A four-step diamond cannot borrow a sibling's detached fixture READ.

These synthetic journals exercise every ancestor/sibling/sink receipt and the
all-success bundle after SQLite reopen. No ToolBackend is dispatched, and no
independently authenticated execution or WRITE capability is claimed.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_planner_success_bundle_review import (
    PlannerReadSuccessBundleRejected,
    review_synthetic_succeeded_read_bundle,
)
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


class _NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("synthetic READ bundle must not execute tools")


def _diamond(tmp_path, *, finish_sink=True):
    ids = tuple("step_" + character * 16 for character in "abcd")
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "scope:private", 200),)
    steps = (
        PlanStep(ids[0], ToolCall(
            "math.sum", "math.sum", "scope:private", {"values": [1, 2]},
        )),
        PlanStep(ids[1], ToolCall(
            "math.sum", "math.sum", "scope:private", {"values": [3, 4]},
        ), (ids[0],)),
        PlanStep(ids[2], ToolCall(
            "math.sum", "math.sum", "scope:private", {"values": [5, 6]},
        ), (ids[0],)),
        PlanStep(ids[3], ToolCall(
            "math.sum", "math.sum", "scope:private", {"values": [7, 8]},
        ), (ids[1], ids[2])),
    )

    read_path = tmp_path / "reads.sqlite"
    read_journal = DisconnectedReadJournal.create(read_path)
    retained = genesis_witness()
    payloads = []
    for index, step in enumerate(steps):
        left = 2 * index + 1
        request = DisconnectedToolRequest(
            "req_" + "abcd"[index] * 32, "math.sum",
            '{"values":[' + str(left) + "," + str(left + 1) + "]}",
        )
        result = execute_disconnected_fixture_tool(request)
        binding = bind_disconnected_fixture_result(request, result)
        link = review_registered_disconnected_fixture(
            registry, gate, step.call, grants, step.step_id,
            request, result, binding, observed_at_ms=50,
        )
        retained = read_journal.append(
            prepare_disconnected_read_receipt(
                step.step_id, request, result, binding,
            ), retained,
        )
        payloads.append((step, request, result, binding, link))

    plan_path = tmp_path / "planner.sqlite"
    plan = SyntheticPlanJournal(plan_path, steps)
    genesis = plan.recover().tail
    for index, step in enumerate(steps):
        if index == 3 and not finish_sink:
            break
        plan.append(
            step.step_id, StepState.RUNNING,
            expected_revision=0, at_ms=60 + index * 2,
            retained=genesis,
        )
        plan.append(
            step.step_id, StepState.SUCCEEDED,
            expected_revision=1, at_ms=61 + index * 2,
            retained=genesis,
        )
    recovered = SyntheticPlanJournal(plan_path, steps).recover(retained=genesis)

    evidence = []
    for step, request, result, binding, link in payloads:
        reviewed = review_retained_registered_receipt(
            read_journal, retained, link, registry, gate, step.call,
            grants, step.step_id, request, result, binding, observed_at_ms=50,
        )
        evidence.append((link, reviewed))
    return read_journal, ids, steps, recovered, tuple(evidence), backend


@pytest.mark.parametrize("omitted", (0, 1, 2, 3))
def test_diamond_requires_own_read_for_every_succeeded_step(tmp_path, omitted):
    reads, ids, steps, recovered, evidence, backend = _diamond(tmp_path)
    try:
        approved = review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[::-1],
        )
        assert approved.step_ids == ids
        assert len(set(approved.correlation_sha256s)) == 4
        assert approved.external_execution_proven is False
        assert approved.write_authorized is False
        assert approved.dispatch_authorized is False
        assert approved.automatic_replay_authorized is False
        missing = evidence[:omitted] + evidence[omitted + 1:]
        with pytest.raises(PlannerReadSuccessBundleRejected):
            review_synthetic_succeeded_read_bundle(recovered, steps, missing)
        assert backend.calls == 0
    finally:
        reads.close()


def test_pending_sink_cannot_borrow_an_unexecuted_fixture_result(tmp_path):
    reads, ids, steps, recovered, evidence, backend = _diamond(
        tmp_path, finish_sink=False,
    )
    try:
        partial = review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[:3],
        )
        assert partial.step_ids == ids[:3]
        assert partial.dispatch_authorized is False
        with pytest.raises(PlannerReadSuccessBundleRejected):
            review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        reads.close()
