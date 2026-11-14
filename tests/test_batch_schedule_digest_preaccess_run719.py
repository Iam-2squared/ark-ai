"""Offline wavefronts reject replaced digest callbacks before inspecting plans."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_batch_schedule as schedule
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
@pytest.mark.parametrize("operation", ("build", "verify"))
def test_schedule_digest_callback_preaccess_denial(monkeypatch, dependency, operation):
    step = DisconnectedBatchStep(
        "step_0000000000000001", "math.sum", '{"values":[1,2]}',
    )
    plan = build_disconnected_batch_plan("req_" + "a" * 32, (step,))
    expected = schedule.build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    intercepted: list[tuple[object, ...]] = []

    def hostile(*args, **_kwargs):
        intercepted.append(args)
        raise AssertionError("unreviewed digest callback received plan details")

    module = schedule.hashlib if dependency == "sha256" else schedule.json
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, hostile)
        with pytest.raises(
            schedule.DisconnectedBatchRejected,
            match="batch schedule digest callback changed",
        ):
            if operation == "build":
                schedule.build_disconnected_batch_schedule(
                    plan, retained_digest=plan.plan_digest,
                )
            else:
                schedule.verify_disconnected_batch_schedule(
                    expected, plan, retained_digest=plan.plan_digest,
                )
    assert intercepted == []
    assert schedule.verify_disconnected_batch_schedule(
        expected, plan, retained_digest=plan.plan_digest,
    ) is None
