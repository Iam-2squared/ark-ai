"""Failure-aware synthetic Planner fixture; no authorized tool dispatch."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_failure_fixture as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule
from ark.agency.disconnected_toolbox import DisconnectedToolResult

REQ = "req_" + "d" * 32
A = "step_0000000000000001"
B = "step_0000000000000002"
C = "step_0000000000000003"
D = "step_0000000000000004"
E = "step_0000000000000005"


def example():
    steps = (
        DisconnectedBatchStep(A, "math.sum", '{"values":[1]}'),
        DisconnectedBatchStep(B, "text.find", '{"needle":"a","text":"abc"}'),
        DisconnectedBatchStep(C, "math.sum", '{"values":[2]}', (A, B)),
        DisconnectedBatchStep(D, "text.stats", '{"text":"hello"}', (C,)),
        DisconnectedBatchStep(E, "json.inspect", '{"json":"[1,2]"}'),
    )
    plan = build_disconnected_batch_plan(REQ, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def run(plan, schedule, failures=()):
    return mod.simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failures,
    )


def test_all_success_has_bounded_digests_and_no_authority():
    plan, schedule = example()
    receipt = run(plan, schedule)
    assert len(receipt.result_digests) == 5
    assert tuple(s for _, s in receipt.terminal_states) == ("SUCCEEDED",) * 5
    assert all(len(sha) == 64 for _, sha in receipt.result_digests)
    assert receipt == run(plan, schedule)
    assert mod.verify_disconnected_failure_fixture(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    for flag in mod._FLAGS:
        assert getattr(receipt, flag) is False


@pytest.mark.parametrize("failures,expected,executed", [
    ((A,), ("FAILED", "SUCCEEDED", "BLOCKED", "BLOCKED", "SUCCEEDED"), (B, E)),
    ((B,), ("SUCCEEDED", "FAILED", "BLOCKED", "BLOCKED", "SUCCEEDED"), (A, E)),
    ((C,), ("SUCCEEDED", "SUCCEEDED", "FAILED", "BLOCKED", "SUCCEEDED"), (A, B, E)),
    ((D,), ("SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "FAILED", "SUCCEEDED"),
     (A, B, E, C)),
    ((E,), ("SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "FAILED"),
     (A, B, C, D)),
    ((A, B), ("FAILED", "FAILED", "BLOCKED", "BLOCKED", "SUCCEEDED"), (E,)),
])
def test_synthetic_failures_skip_blocked_descendants(
    monkeypatch, failures, expected, executed,
):
    plan, schedule = example()
    original = mod.execute_disconnected_fixture_tool
    called = []

    def spy(request):
        called.append(request.canonical_args_json)
        return original(request)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", spy)
    receipt = run(plan, schedule, failures)
    assert tuple(state for _, state in receipt.terminal_states) == expected
    assert tuple(step for step, _ in receipt.result_digests) == executed
    assert len(called) == len(executed)
    assert receipt.failed_step_ids == failures


@pytest.mark.parametrize("bad", [
    [A], (A, A), (B, A), (A, C), ("step_ffffffffffffffff",), (True,),
    ("",), tuple([A] * 25),
])
def test_invalid_or_blocked_failures_denied(bad):
    plan, schedule = example()
    with pytest.raises(ValueError):
        run(plan, schedule, bad)


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("plan_digest", "f" * 64),
    ("schedule_digest", "f" * 64),
    ("projection_digest", "f" * 64),
    ("failed_step_ids", (A,)),
    ("terminal_states", ((A, "FAILED"),)),
    ("result_digests", ((A, "f" * 64),)),
    ("result_digests", [[A, "f" * 64]]),
    ("fixture_digest", "f" * 64),
    ("fixture_digest", True),
])
def test_changed_receipt_rejected(field, bad):
    plan, schedule = example()
    original = run(plan, schedule)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected):
        mod.verify_disconnected_failure_fixture(
            replace(original, **{field: bad}),
            plan, schedule, retained_digest=plan.plan_digest,
        )


@pytest.mark.parametrize("tamper", ["input_digest", "result_digest", "operation"])
def test_result_substitution_denied(monkeypatch, tamper):
    plan, schedule = example()
    original = mod.execute_disconnected_fixture_tool

    def forged(request):
        receipt = original(request)
        return replace(receipt, **{tamper: "f" * 64})

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", forged)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected):
        run(plan, schedule, (A,))


def test_duplicate_json_result_denied(monkeypatch):
    plan, schedule = example()
    original = mod.execute_disconnected_fixture_tool

    def forged(request):
        receipt = original(request)
        return replace(receipt, canonical_result_json='{"a":1,"a":2}')

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", forged)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="duplicate"):
        run(plan, schedule)


def test_plan_change_during_fixture_denied(monkeypatch):
    plan, schedule = example()
    original = mod.execute_disconnected_fixture_tool

    def mutated(request):
        object.__setattr__(plan.steps[3], "operation", "math.sum")
        return original(request)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", mutated)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="changed"):
        run(plan, schedule)


def test_schedule_change_during_fixture_denied(monkeypatch):
    plan, schedule = example()
    original = mod.execute_disconnected_fixture_tool

    def mutated(request):
        object.__setattr__(schedule, "schedule_digest", "f" * 64)
        return original(request)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", mutated)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="changed"):
        run(plan, schedule)


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_synthetic_receipt_cannot_gain_authority(monkeypatch, flag):
    plan, schedule = example()
    monkeypatch.setattr(
        mod.DisconnectedFailureFixtureReceipt, flag,
        property(lambda self: True),
    )
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="receipt changed"):
        run(plan, schedule)


def test_mock_result_cannot_gain_external_authority(monkeypatch):
    plan, schedule = example()
    monkeypatch.setattr(
        DisconnectedToolResult, "external_outcome_known",
        property(lambda self: True),
    )
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="authority"):
        run(plan, schedule)


class ReceiptSubclass(mod.DisconnectedFailureFixtureReceipt):
    pass


def test_subclass_receipt_denied():
    plan, schedule = example()
    base = run(plan, schedule)
    forged = ReceiptSubclass(
        base.request_id, base.plan_digest, base.schedule_digest,
        base.projection_digest, base.failed_step_ids, base.terminal_states,
        base.result_digests, base.fixture_digest,
    )
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="exact"):
        mod.verify_disconnected_failure_fixture(
            forged, plan, schedule, retained_digest=plan.plan_digest,
        )
