"""Detached fixture-cycle receipt verification never trusts dataclass equality."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_fixture_cycle as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

REQ = "req_" + "e" * 32


def fixture():
    first = DisconnectedBatchStep(
        "step_0000000000000001", "math.sum", '{"values":[1,2]}',
    )
    second = DisconnectedBatchStep(
        "step_0000000000000002", "math.sum", '{"values":[3,4]}',
        (first.step_id,),
    )
    plan = build_disconnected_batch_plan(REQ, (first, second))
    schedule = build_disconnected_batch_schedule(plan, retained_digest=plan.plan_digest)
    receipt = mod.simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=plan.plan_digest,
    )
    return plan, schedule, receipt


def verify(receipt, plan, schedule):
    return mod.verify_disconnected_batch_fixture_cycle(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    )


def test_valid_detached_cycle_is_inert_and_recomputable():
    plan, schedule, receipt = fixture()
    assert verify(receipt, plan, schedule) is None
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_verified is False


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("plan_digest", "f" * 64),
    ("schedule_digest", "f" * 64),
    ("cycle_digest", "f" * 64),
    ("wave_result_hashes", (("f" * 64,),)),
])
def test_forged_equality_does_not_accept_substituted_result(monkeypatch, field, bad):
    plan, schedule, receipt = fixture()
    forged = replace(receipt, **{field: bad})
    monkeypatch.setattr(mod.DisconnectedBatchCycleReceipt, "__eq__", lambda a, b: True)
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="integrity"):
        verify(forged, plan, schedule)


@pytest.mark.parametrize("mutation", ["receipt", "schedule"])
def test_last_false_denial_callback_cannot_rewrite_cycle_or_schedule(
    monkeypatch, mutation,
):
    plan, schedule, receipt = fixture()

    def malicious(self):
        if self is receipt:
            if mutation == "receipt":
                object.__setattr__(self, "cycle_digest", "f" * 64)
            else:
                object.__setattr__(schedule, "schedule_digest", "f" * 64)
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchCycleReceipt, "authenticated_consent",
        property(malicious),
    )
    with pytest.raises(ValueError):
        verify(receipt, plan, schedule)
