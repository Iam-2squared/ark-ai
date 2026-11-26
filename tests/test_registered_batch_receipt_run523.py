"""Disconnected Planner DAG -> Registry -> READ journal reconciliation."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_registered_batch_receipt_review import (
    RegisteredBatchReceiptRejected,
    RegisteredBatchReceiptReview,
    review_registered_batch_receipt,
)
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

STEP = "step_" + "a" * 16
SECOND = "step_" + "b" * 16
ARGS = '{"values":[1,2]}'


@dataclass
class ForbiddenBackend:
    calls: int = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("batch READ review must not dispatch")


def setup_case(tmp_path, *, dependent=False):
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "local:mock", backend),
    ))
    gate = PermissionGate()
    call = ToolCall(
        "math.sum", "math.sum", "sandbox:fixture", {"values": [1, 2]},
    )
    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    request = DisconnectedToolRequest("req_" + "a" * 32, "math.sum", ARGS)
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    link = review_registered_disconnected_fixture(
        registry, gate, call, grants, STEP, request, result,
        binding, observed_at_ms=50,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "registered-batch.sqlite")
    retained = journal.append(
        prepare_disconnected_read_receipt(STEP, request, result, binding),
        genesis_witness(),
    )
    steps = (DisconnectedBatchStep(STEP, "math.sum", ARGS, ()),)
    if dependent:
        steps += (DisconnectedBatchStep(SECOND, "math.sum", ARGS, (STEP,)),)
    plan = build_disconnected_batch_plan("req_" + "f" * 32, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return locals()


def invoke(case, **changes):
    kwargs = {
        "plan": case["plan"], "schedule": case["schedule"],
        "retained_plan_digest": case["plan"].plan_digest,
        "journal": case["journal"], "retained_journal": case["retained"],
        "link": case["link"], "registry": case["registry"],
        "gate": case["gate"], "call": case["call"],
        "grants": case["grants"], "step_id": STEP,
        "request": case["request"], "result": case["result"],
        "binding": case["binding"], "observed_at_ms": 50,
    }
    kwargs.update(changes)
    return review_registered_batch_receipt(**kwargs)


def test_registered_step_with_dependent_dag_is_diagnostic_only(tmp_path):
    case = setup_case(tmp_path, dependent=True)
    try:
        review = invoke(case)
        assert type(review) is RegisteredBatchReceiptReview
        assert review.step_id == STEP
        assert review.wave_index == 0
        assert review.plan_digest == case["plan"].plan_digest
        assert review.schedule_digest == case["schedule"].schedule_digest
        assert len(review.review_sha256) == 64
        assert not review.backend_dispatched
        assert not review.dependencies_completed_proven
        assert not review.write_authorized
        assert not review.automatic_replay_authorized
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize("changed", [
    {"step_id": SECOND},
    {"step_id": "step_" + "f" * 16},
    {"retained_plan_digest": "f" * 64},
    {"observed_at_ms": 101},
])
def test_wrong_step_witness_or_expired_grant_denied(tmp_path, changed):
    case = setup_case(tmp_path, dependent=True)
    try:
        with pytest.raises(RegisteredBatchReceiptRejected):
            invoke(case, **changed)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize("field,value", [
    ("operation", "text.find"),
    ("canonical_args_json", '{"values":[9,9]}'),
])
def test_dag_step_mismatch_is_denied(tmp_path, field, value):
    case = setup_case(tmp_path)
    try:
        object.__setattr__(case["plan"].steps[0], field, value)
        with pytest.raises(RegisteredBatchReceiptRejected):
            invoke(case)
    finally:
        case["journal"].close()


def test_schedule_reordering_denied(tmp_path):
    case = setup_case(tmp_path, dependent=True)
    try:
        object.__setattr__(case["schedule"], "waves", ((SECOND,), (STEP,)))
        with pytest.raises(RegisteredBatchReceiptRejected):
            invoke(case)
    finally:
        case["journal"].close()


@pytest.mark.parametrize("field,value", [
    ("action_request_id", "act_" + "f" * 64),
    ("fixture_request_id", "req_" + "f" * 32),
    ("journal_count", 999),
])
def test_last_authority_getter_cannot_modify_result(
    tmp_path, monkeypatch, field, value,
):
    case = setup_case(tmp_path)

    def forged_denial(self):
        object.__setattr__(self, field, value)
        return False

    monkeypatch.setattr(
        RegisteredBatchReceiptReview, "independent_custody_proven",
        property(forged_denial),
    )
    try:
        with pytest.raises(RegisteredBatchReceiptRejected, match="changed after denial"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_local_journal_tamper_is_not_accepted(tmp_path):
    case = setup_case(tmp_path)
    try:
        case["journal"]._connection.execute(
            "UPDATE receipts SET operation='text.find'"
        )
        with pytest.raises(RegisteredBatchReceiptRejected):
            invoke(case)
    finally:
        case["journal"].close()


@pytest.mark.parametrize("name", (
    "backend_dispatched", "write_authorized", "automatic_replay_authorized",
    "dependencies_completed_proven", "independent_custody_proven",
))
def test_nonoriginal_denial_never_enters_registered_journal(
    tmp_path, monkeypatch, name,
):
    """A property returning False is not proof of its original authority."""
    from ark.agency import disconnected_registered_batch_receipt_review as mod

    case = setup_case(tmp_path)
    try:
        monkeypatch.setattr(
            RegisteredBatchReceiptReview, name, property(lambda _self: False),
        )

        def forbidden_scan():
            raise AssertionError("untrusted denial entered the READ journal")

        monkeypatch.setattr(case["journal"], "_scan", forbidden_scan)
        with pytest.raises(RegisteredBatchReceiptRejected, match="descriptor replaced"):
            invoke(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
        assert mod._ORIGINAL_DENIALS[0] is not None
    finally:
        case["journal"].close()


def test_registered_batch_rejects_denial_replacement_inside_receipt_callback(
    tmp_path, monkeypatch,
):
    """The first genuine journal observation must not launder a late swap."""
    from ark.agency import disconnected_registered_batch_receipt_review as mod

    case = setup_case(tmp_path)
    original = mod.review_retained_registered_receipt

    def substituted(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(
            RegisteredBatchReceiptReview, "write_authorized",
            property(lambda _self: False),
        )
        return result

    monkeypatch.setattr(mod, "review_retained_registered_receipt", substituted)
    try:
        with pytest.raises(RegisteredBatchReceiptRejected, match="descriptor replaced"):
            invoke(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
