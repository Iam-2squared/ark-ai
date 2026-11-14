"""Partial successful READ journal with FAILED/BLOCKED archive: no dispatch."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_batch_failure_archive import (
    archive_disconnected_failure_fixture,
)
from ark.agency.disconnected_batch_failure_fixture import (
    simulate_disconnected_failure_fixture,
)
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_partial_registered_failure_join import (
    PartialFailureJoinRejected,
    PartialFailureJoinReview,
    review_partial_registered_failure_archive,
)
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_registered_batch_receipt_set import RegisteredBatchStepEvidence
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

A = "step_" + "a" * 16
B = "step_" + "b" * 16
C = "step_" + "c" * 16
ARGS = '{"values":[1,2]}'


@dataclass
class NeverDispatch:
    calls: int = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("a disconnected review must not execute tools")


def setup_case(tmp_path):
    backend = NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "local:mock", backend),
    ))
    gate = PermissionGate()
    steps = (
        DisconnectedBatchStep(A, "math.sum", ARGS),
        DisconnectedBatchStep(B, "math.sum", ARGS),
        DisconnectedBatchStep(C, "math.sum", ARGS, (B,)),
    )
    plan = build_disconnected_batch_plan("req_" + "f" * 32, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    failures = (B,)
    receipt = simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failures,
    )
    path = tmp_path / "hypothetical-terminal.json"
    witness = archive_disconnected_failure_fixture(
        receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path,
    )

    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    call = ToolCall("math.sum", "math.sum", "sandbox:fixture", {"values": [1, 2]})
    request = DisconnectedToolRequest(plan.request_id, "math.sum", ARGS)
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    link = review_registered_disconnected_fixture(
        registry, gate, call, grants, A, request, result, binding,
        observed_at_ms=50,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "success-only.sqlite")
    retained = journal.append(
        prepare_disconnected_read_receipt(A, request, result, binding),
        genesis_witness(),
    )
    success = RegisteredBatchStepEvidence(
        journal, retained, link, call, grants, request, result, binding,
    )
    return locals()


def invoke(case, **overrides):
    arguments = {
        "plan": case["plan"], "schedule": case["schedule"],
        "evidence": ((A, case["success"]),),
        "registry": case["registry"], "gate": case["gate"],
        "retained_plan_digest": case["plan"].plan_digest,
        "retained_failed_step_ids": case["failures"],
        "path": case["path"], "retained_file_sha256": case["witness"].file_sha256,
        "observed_at_ms": 50,
    }
    arguments.update(overrides)
    return review_partial_registered_failure_archive(**arguments)


def test_one_success_failed_and_blocked_reconcile_without_dispatch(tmp_path):
    case = setup_case(tmp_path)
    try:
        result = invoke(case)
        assert type(result) is PartialFailureJoinReview
        assert result.terminal_states == (
            (A, "SUCCEEDED"), (B, "FAILED"), (C, "BLOCKED"),
        )
        assert tuple(row[0] for row in result.successful_read_receipts) == (A,)
        assert result.failure_file_sha256 == case["witness"].file_sha256
        assert len(result.join_sha256) == 64
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
        for name in (
            "backend_dispatched", "write_authorized",
            "automatic_replay_authorized", "failure_authenticated",
            "dependencies_completed_proven", "cross_store_atomicity_proven",
        ):
            assert getattr(result, name) is False
    finally:
        case["journal"].close()


@pytest.mark.parametrize("kind", (
    "missing", "failed", "blocked", "duplicate", "wrong_name", "extra_object",
))
def test_only_successful_ordered_registered_receipts_are_accepted(tmp_path, kind):
    case = setup_case(tmp_path)
    evidence = ((A, case["success"]),)
    variants = {
        "missing": (),
        "failed": ((B, case["success"]),),
        "blocked": ((C, case["success"]),),
        "duplicate": evidence + evidence,
        "wrong_name": (("step_" + "d" * 16, case["success"]),),
        "extra_object": ((A, object()),),
    }
    try:
        with pytest.raises(PartialFailureJoinRejected):
            invoke(case, evidence=variants[kind])
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize("kind", (
    "file_hash", "failure_mask", "path_bytes", "retained_digest",
    "clock_bool", "clock_expired",
))
def test_archive_failure_mask_plan_and_clock_remain_independent(tmp_path, kind):
    case = setup_case(tmp_path)
    kwargs = {}
    if kind == "file_hash":
        kwargs["retained_file_sha256"] = "0" * 64
    elif kind == "failure_mask":
        kwargs["retained_failed_step_ids"] = ()
    elif kind == "path_bytes":
        case["path"].write_bytes(b'{"fake":"archive"}')
    elif kind == "retained_digest":
        kwargs["retained_plan_digest"] = "0" * 64
    elif kind == "clock_bool":
        kwargs["observed_at_ms"] = True
    else:
        kwargs["observed_at_ms"] = 101
    try:
        with pytest.raises(PartialFailureJoinRejected):
            invoke(case, **kwargs)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_registered_success_journal_tamper_is_rejected(tmp_path):
    case = setup_case(tmp_path)
    try:
        case["journal"]._connection.execute(
            "UPDATE receipts SET operation='text.find'"
        )
        with pytest.raises(PartialFailureJoinRejected):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_different_synthetic_request_cannot_borrow_a_success_receipt(tmp_path):
    case = setup_case(tmp_path)
    try:
        bad_request = DisconnectedToolRequest("req_" + "d" * 32, "math.sum", ARGS)
        bad = replace(case["success"], request=bad_request)
        with pytest.raises(PartialFailureJoinRejected, match="request binding"):
            invoke(case, evidence=((A, bad),))
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_false_only_replacement_of_result_authority_is_not_original(
    tmp_path, monkeypatch,
):
    case = setup_case(tmp_path)
    monkeypatch.setattr(
        PartialFailureJoinReview, "automatic_replay_authorized",
        property(lambda _self: False),
    )
    try:
        with pytest.raises(PartialFailureJoinRejected, match="definition changed"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()
