"""Independent mock WRITE plans share ledgers without laundering an UNKNOWN.

The first plan may die at any durable boundary. A distinct plan with a
different registry-bound request/token/occurrence can still complete a
disconnected fixture cycle, but never clears or retries the first one.
Four stores remain non-atomic; no real backend is invoked.
"""

from __future__ import annotations

import pytest
from test_synthetic_mock_sidecar_cycle_run374 import _run, _setup

from ark.agency.contracts import OneShotAuthorization, PlanStep, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)


@pytest.mark.parametrize(
    ("fault", "reserved_before", "audited_before", "linked_before"),
    (
        ("after_running", 0, 0, 0),
        ("after_reservation", 1, 0, 0),
        ("after_pre_action_audit", 1, 1, 0),
        ("after_audit_link", 1, 1, 1),
        ("after_mock_marker", 1, 1, 1),
    ),
)
def test_distinct_plan_can_finish_without_releasing_ambiguous_predecessor(
    tmp_path, fault, reserved_before, audited_before, linked_before,
):
    first = _setup(tmp_path)
    initial = first[0].recover().tail
    with pytest.raises(SyntheticMockCrashInjected):
        _run(first, fault_at=fault)
    unknown = first[0].recover(retained=initial)
    assert unknown.ambiguous_running_steps == ("root",)
    assert unknown.automatic_replay_authorized is False
    assert first[1].count_synthetic() == reserved_before
    assert len(first[2].events()) == audited_before
    assert first[5].read_witness().event_count == linked_before

    # Only the two plan journals are disjoint: all authorization/audit/link
    # stores and the immutable registry intentionally remain shared.
    second_call = ToolCall("mock", "write", "local", {"offline": True, "task": "b"})
    second_plan = SyntheticPlanJournal(
        tmp_path / "second-plan.sqlite", (PlanStep("root", second_call),),
    )
    second_token = OneShotAuthorization(
        "token-second", second_call.request_id, 1000,
    )
    second = (
        second_plan, first[1], first[2], first[3],
        second_call, first[5], second_token, first[7],
    )
    receipt = _run(second, occurrence="disjoint-plan")
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False

    # Reopening all four stores cannot turn the predecessor RUNNING into
    # an execution grant, nor erase later independent diagnostic evidence.
    assert SyntheticPlanJournal(
        tmp_path / "journal.sqlite", first[0]._steps,
    ).recover(retained=initial) == unknown
    recovered_second = SyntheticPlanJournal(
        tmp_path / "second-plan.sqlite", second_plan._steps,
    ).recover()
    assert recovered_second.step_statuses == (("root", "succeeded", 2),)
    assert recovered_second.dispatch_authorized is False
    assert recovered_second.automatic_replay_authorized is False
    assert first[1].count_synthetic() == reserved_before + 1
    assert len(first[2].events()) == audited_before + 1
    assert SyntheticOccurrenceAuditLinkStore(
        first[7],
    ).read_witness().event_count == linked_before + 1

    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(first, occurrence="new-after-independent-success")
    assert first[0].recover(retained=initial) == unknown
    assert first[1].count_synthetic() == reserved_before + 1
    assert len(first[2].events()) == audited_before + 1
    assert first[5].read_witness().event_count == linked_before + 1
