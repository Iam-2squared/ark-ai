"""Detached schedule integrity never relies on mutable dataclass equality."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_schedule as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)

REQ = "req_" + "a" * 32


def fixture():
    first = DisconnectedBatchStep("step_0000000000000001", "math.sum", '{"values":[1]}')
    second = DisconnectedBatchStep(
        "step_0000000000000002", "math.sum", '{"values":[2]}',
        (first.step_id,),
    )
    plan = build_disconnected_batch_plan(REQ, (first, second))
    schedule = mod.build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def test_valid_detached_wavefront_still_verifies():
    plan, schedule = fixture()
    assert mod.verify_disconnected_batch_schedule(
        schedule, plan, retained_digest=plan.plan_digest,
    ) is None
    assert schedule.dispatch_authorized is False


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("plan_digest", "f" * 64),
    ("schedule_digest", "f" * 64),
    ("waves", (("step_0000000000000002",), ("step_0000000000000001",))),
])
def test_mutated_schedule_rejected_even_when_equality_claims_true(monkeypatch, field, bad):
    plan, original = fixture()
    fake = replace(original, **{field: bad})
    monkeypatch.setattr(mod.DisconnectedBatchSchedule, "__eq__", lambda self, other: True)
    with pytest.raises(mod.DisconnectedBatchRejected, match="integrity"):
        mod.verify_disconnected_batch_schedule(
            fake, plan, retained_digest=plan.plan_digest,
        )


def test_false_authority_callback_cannot_rewrite_schedule_after_check(monkeypatch):
    plan, schedule = fixture()

    def malicious(self):
        if self is schedule:
            object.__setattr__(self, "schedule_digest", "f" * 64)
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchSchedule,
        "dispatch_authorized", property(malicious),
    )
    with pytest.raises(mod.DisconnectedBatchRejected, match="changed after denial"):
        mod.verify_disconnected_batch_schedule(
            schedule, plan, retained_digest=plan.plan_digest,
        )
