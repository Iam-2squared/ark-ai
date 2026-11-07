"""Detached scheduling cannot promote monkeypatched false authority descriptors.

A deterministic wavefront is not permission to dispatch, parallelize, write,
notify, or replay real operations.
"""

import pytest

import ark.agency.disconnected_batch_schedule as schedule
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchRejected,
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)


def _plan():
    first = DisconnectedBatchStep(
        "step_0000000000000001", "math.sum", '{"values":[1]}',
    )
    second = DisconnectedBatchStep(
        "step_0000000000000002", "math.sum", '{"values":[2]}',
        (first.step_id,),
    )
    return build_disconnected_batch_plan(
        "req_" + "a" * 32, (first, second),
    )


_FLAGS = (
    "dispatch_authorized", "parallel_execution_authorized",
    "write_authorized", "replay_authorized",
)


@pytest.mark.parametrize("flag", _FLAGS)
def test_builder_rejects_preinstalled_false_only_denial_descriptor(monkeypatch, flag):
    plan = _plan()
    monkeypatch.setattr(
        schedule.DisconnectedBatchSchedule, flag,
        property(lambda _self: False),
    )
    with pytest.raises(DisconnectedBatchRejected, match="schedule changed after denial"):
        schedule.build_disconnected_batch_schedule(
            plan, retained_digest=plan.plan_digest,
        )


@pytest.mark.parametrize("flag", _FLAGS)
def test_verifier_rejects_preinstalled_false_only_denial_descriptor(monkeypatch, flag):
    plan = _plan()
    report = schedule.build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    monkeypatch.setattr(
        schedule.DisconnectedBatchSchedule, flag,
        property(lambda _self: False),
    )
    with pytest.raises(DisconnectedBatchRejected, match="schedule changed after denial"):
        schedule.verify_disconnected_batch_schedule(
            report, plan, retained_digest=plan.plan_digest,
        )


def test_builder_rejects_rebound_schedule_constructor(monkeypatch):
    plan = _plan()
    base = schedule.DisconnectedBatchSchedule
    monkeypatch.setattr(schedule, "DisconnectedBatchSchedule", type("Fake", (base,), {}))
    with pytest.raises(DisconnectedBatchRejected, match="schedule changed after denial"):
        schedule.build_disconnected_batch_schedule(
            plan, retained_digest=plan.plan_digest,
        )


def test_original_builder_and_verifier_keep_deterministic_wavefront():
    plan = _plan()
    result = schedule.build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    assert result.waves == (
        ("step_0000000000000001",), ("step_0000000000000002",),
    )
    assert schedule.verify_disconnected_batch_schedule(
        result, plan, retained_digest=plan.plan_digest,
    ) is None
    assert all(getattr(result, name) is False for name in _FLAGS)
