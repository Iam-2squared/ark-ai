"""Detached failed-wave receipts resist spoofed equality and late callbacks."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_failure_fixture as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

A = "step_0000000000000001"
B = "step_0000000000000002"


def fixture():
    plan = build_disconnected_batch_plan("req_" + "d" * 32, (
        DisconnectedBatchStep(A, "math.sum", '{"values":[1,2]}'),
        DisconnectedBatchStep(B, "text.stats", '{"text":"hello"}', (A,)),
    ))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def simulate(plan, schedule):
    return mod.simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
    )


def verify(receipt, plan, schedule):
    return mod.verify_disconnected_failure_fixture(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    )


@pytest.mark.parametrize("field,forged", [
    ("request_id", "req_" + "f" * 32),
    ("projection_digest", "f" * 64),
    ("result_digests", ((A, "f" * 64),)),
    ("terminal_states", ((A, "FAILED"),)),
    ("fixture_digest", "f" * 64),
])
def test_true_for_all_dataclass_equality_cannot_accept_tampering(
    monkeypatch, field, forged,
):
    plan, schedule = fixture()
    original = simulate(plan, schedule)
    changed = replace(original, **{field: forged})
    monkeypatch.setattr(
        mod.DisconnectedFailureFixtureReceipt, "__eq__",
        lambda self, other: True,
    )
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="mismatch"):
        verify(changed, plan, schedule)


@pytest.mark.parametrize("mutation", ["receipt", "plan", "schedule"])
def test_last_denial_callback_cannot_conceal_mutation(
    monkeypatch, mutation,
):
    plan, schedule = fixture()
    original = simulate(plan, schedule)

    def denial(self):
        if self is original:
            if mutation == "receipt":
                object.__setattr__(self, "fixture_digest", "f" * 64)
            elif mutation == "plan":
                object.__setattr__(plan.steps[0], "operation", "text.find")
            else:
                object.__setattr__(schedule, "schedule_digest", "f" * 64)
        return False

    monkeypatch.setattr(
        mod.DisconnectedFailureFixtureReceipt,
        "external_outcome_verified", property(denial),
    )
    with pytest.raises(ValueError):
        verify(original, plan, schedule)


def test_creation_detects_late_mutation_of_result_digests(monkeypatch):
    plan, schedule = fixture()

    def denial(self):
        object.__setattr__(self, "result_digests", ())
        return False

    monkeypatch.setattr(
        mod.DisconnectedFailureFixtureReceipt,
        "external_outcome_verified", property(denial),
    )
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="changed"):
        simulate(plan, schedule)


def test_unchanged_all_success_and_failure_masks_stay_inert():
    plan, schedule = fixture()
    good = simulate(plan, schedule)
    assert verify(good, plan, schedule) is None
    failed = mod.simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=(A,),
    )
    assert mod.verify_disconnected_failure_fixture(
        failed, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    assert failed.write_authorized is False
