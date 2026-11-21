"""Detached terminal projection verification rejects mutable equality and late edits."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_terminal_projection as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

REQ = "req_" + "b" * 32
A = "step_0000000000000001"
B = "step_0000000000000002"


def fixture():
    plan = build_disconnected_batch_plan(REQ, (
        DisconnectedBatchStep(A, "math.sum", '{"values":[1]}'),
        DisconnectedBatchStep(B, "math.sum", '{"values":[2]}', (A,)),
    ))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    result = mod.project_disconnected_batch_terminals(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=(A,),
    )
    return plan, schedule, result


def verify(receipt, plan, schedule):
    return mod.verify_disconnected_batch_terminals(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    )


def test_matching_inert_failure_projection():
    plan, schedule, result = fixture()
    assert result.terminal_states == ((A, "FAILED"), (B, "BLOCKED"))
    assert verify(result, plan, schedule) is None
    assert result.failure_claim_authenticated is False


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("plan_digest", "f" * 64),
    ("schedule_digest", "f" * 64),
    ("failed_step_ids", ()),
    ("terminal_states", ((A, "SUCCEEDED"), (B, "BLOCKED"))),
    ("projection_digest", "f" * 64),
])
def test_dataclass_equality_spoof_cannot_bypass_receipt_fields(monkeypatch, field, bad):
    plan, schedule, result = fixture()
    forged = replace(result, **{field: bad})
    monkeypatch.setattr(
        mod.DisconnectedBatchTerminalReceipt, "__eq__",
        lambda self, other: True,
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="integrity"):
        verify(forged, plan, schedule)


@pytest.mark.parametrize("mutation", ["receipt", "plan"])
def test_false_final_authority_getter_cannot_change_result_or_plan(monkeypatch, mutation):
    plan, schedule, result = fixture()

    def malicious(self):
        if self is result:
            if mutation == "receipt":
                object.__setattr__(self, "projection_digest", "f" * 64)
            else:
                object.__setattr__(plan.steps[-1], "operation", "text.find")
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchTerminalReceipt, "failure_claim_authenticated",
        property(malicious),
    )
    with pytest.raises(ValueError):
        verify(result, plan, schedule)
