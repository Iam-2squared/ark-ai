"""Pure deterministic dependency-wave preview; no backend execution."""

from dataclasses import replace

import pytest

from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    DisconnectedBatchRejected,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import (
    DisconnectedBatchSchedule,
    build_disconnected_batch_schedule,
    verify_disconnected_batch_schedule,
)

REQ = "req_" + "a" * 32


def step(number, depends=()):
    return DisconnectedBatchStep(
        f"step_{number:016x}", "math.sum", '{"values":[1,2]}', depends,
    )


def fixture():
    a, b, e = step(1), step(2), step(5)
    c = step(3, (a.step_id, b.step_id))
    d = step(4, (c.step_id,))
    plan = build_disconnected_batch_plan(REQ, (a, b, c, d, e))
    return plan, (a, b, c, d, e)


def schedule(plan):
    return build_disconnected_batch_schedule(plan, retained_digest=plan.plan_digest)


def test_parallel_ready_wavefronts_are_stable_and_non_executing():
    plan, (a, b, c, d, e) = fixture()
    report = schedule(plan)
    assert report.waves == (
        (a.step_id, b.step_id, e.step_id),
        (c.step_id,),
        (d.step_id,),
    )
    assert report.schedule_digest == schedule(plan).schedule_digest
    assert len(report.schedule_digest) == 64
    assert not report.dispatch_authorized
    assert not report.parallel_execution_authorized
    assert not report.write_authorized
    assert not report.replay_authorized
    assert verify_disconnected_batch_schedule(
        report, plan, retained_digest=plan.plan_digest,
    ) is None


def test_chain_and_all_independent_wavefronts():
    a, b, c = step(1), step(2, ("step_0000000000000001",)), step(
        3, ("step_0000000000000002",),
    )
    chain = build_disconnected_batch_plan(REQ, (a, b, c))
    assert schedule(chain).waves == ((a.step_id,), (b.step_id,), (c.step_id,))
    loose = build_disconnected_batch_plan(REQ, (step(1), step(2), step(3)))
    assert schedule(loose).waves == (tuple(s.step_id for s in loose.steps),)


@pytest.mark.parametrize("field,mutation", [
    ("request_id", "req_" + "b" * 32),
    ("plan_digest", "f" * 64),
    ("schedule_digest", "0" * 64),
    ("schedule_digest", True),
    ("waves", (("step_0000000000000001",),)),
    ("waves", [["step_0000000000000001"]]),
    ("waves", ((True,),)),
])
def test_tampered_schedule_cannot_be_verified(field, mutation):
    plan, _ = fixture()
    outcome = schedule(plan)
    with pytest.raises(DisconnectedBatchRejected):
        verify_disconnected_batch_schedule(
            replace(outcome, **{field: mutation}),
            plan, retained_digest=plan.plan_digest,
        )


def test_retained_plan_digest_is_independent():
    plan, _ = fixture()
    with pytest.raises(DisconnectedBatchRejected):
        build_disconnected_batch_schedule(plan, retained_digest="f" * 64)
    with pytest.raises(DisconnectedBatchRejected):
        verify_disconnected_batch_schedule(
            schedule(plan), plan, retained_digest="f" * 64,
        )


class FakeSchedule(DisconnectedBatchSchedule):
    pass


def test_schedule_requires_exact_type():
    plan, _ = fixture()
    outcome = schedule(plan)
    fake = FakeSchedule(
        outcome.request_id, outcome.plan_digest, outcome.waves,
        outcome.schedule_digest,
    )
    with pytest.raises(DisconnectedBatchRejected):
        verify_disconnected_batch_schedule(
            fake, plan, retained_digest=plan.plan_digest,
        )


def test_reflective_plan_change_during_wavefront_build_is_rejected(monkeypatch):
    import ark.agency.disconnected_batch_schedule as mod

    plan, _ = fixture()
    original = mod._wavefronts

    def mutated(plan_arg):
        waves = original(plan_arg)
        object.__setattr__(plan_arg, "plan_digest", "f" * 64)
        return waves

    monkeypatch.setattr(mod, "_wavefronts", mutated)
    with pytest.raises(DisconnectedBatchRejected):
        schedule(plan)
