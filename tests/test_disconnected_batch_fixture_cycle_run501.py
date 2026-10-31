"""Run501 detached wavefront fixture cycle; never backend dispatch."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_fixture_cycle as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import (
    build_disconnected_batch_schedule,
)
from ark.agency.disconnected_toolbox import DisconnectedToolResult

REQ = "req_" + "a" * 32


def step(number, operation="math.sum", args='{"values":[1,2]}', depends=()):
    return DisconnectedBatchStep(
        f"step_{number:016x}", operation, args, depends,
    )


def fixture():
    a = step(1)
    b = step(2, "text.find", '{"needle":"a","text":"abc"}')
    c = step(3, "text.stats", '{"text":"hello world"}', (a.step_id, b.step_id))
    d = step(4, "json.inspect", '{"json":"[1,2]"}', (c.step_id,))
    plan = build_disconnected_batch_plan(REQ, (a, b, c, d))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def cycle(plan, schedule):
    return mod.simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=plan.plan_digest,
    )


def test_deterministic_waves_and_inert_authority():
    plan, schedule = fixture()
    result = cycle(plan, schedule)
    assert tuple(len(wave) for wave in result.wave_result_hashes) == (2, 1, 1)
    assert all(len(item) == 64 for wave in result.wave_result_hashes for item in wave)
    assert result == cycle(plan, schedule)
    assert result.request_id == REQ
    assert result.plan_digest == plan.plan_digest
    assert result.schedule_digest == schedule.schedule_digest
    assert len(result.cycle_digest) == 64
    assert mod.verify_disconnected_batch_fixture_cycle(
        result, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    for flag in mod._RECEIPT_FLAGS:
        assert getattr(result, flag) is False


def test_simulation_does_not_advance_caller_or_execute_backend():
    plan, schedule = fixture()
    steps_before = plan.steps
    waves_before = schedule.waves
    cycle(plan, schedule)
    assert plan.steps is steps_before
    assert schedule.waves is waves_before


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("plan_digest", "0" * 64),
    ("schedule_digest", "0" * 64),
    ("cycle_digest", True),
    ("cycle_digest", "0" * 64),
    ("wave_result_hashes", (("0" * 64,),)),
    ("wave_result_hashes", [["0" * 64]]),
    ("wave_result_hashes", ((True,),)),
])
def test_detached_receipt_tamper_rejected(field, bad):
    plan, schedule = fixture()
    original = cycle(plan, schedule)
    with pytest.raises(mod.DisconnectedBatchCycleRejected):
        mod.verify_disconnected_batch_fixture_cycle(
            replace(original, **{field: bad}), plan, schedule,
            retained_digest=plan.plan_digest,
        )


def test_wrong_independently_retained_digest_rejected():
    plan, schedule = fixture()
    with pytest.raises(ValueError):
        mod.simulate_disconnected_batch_fixture_cycle(
            plan, schedule, retained_digest="f" * 64,
        )
    with pytest.raises(ValueError):
        mod.verify_disconnected_batch_fixture_cycle(
            cycle(plan, schedule), plan, schedule, retained_digest="f" * 64,
        )


def test_invalid_fixture_operation_args_fail_closed():
    first = step(1, args='{"values":[true]}')
    plan = build_disconnected_batch_plan(REQ, (first,))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="step rejected"):
        cycle(plan, schedule)


@pytest.mark.parametrize("tamper", [
    "input_digest", "result_digest", "canonical_result_json",
    "request_id", "operation",
])
def test_mock_result_identity_substitution_rejected(monkeypatch, tamper):
    plan, schedule = fixture()
    original = mod.execute_disconnected_fixture_tool

    def forged(request):
        receipt = original(request)
        value = '{"sum":999}' if tamper == "canonical_result_json" else "f" * 64
        return replace(receipt, **{tamper: value})

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", forged)
    with pytest.raises(mod.DisconnectedBatchCycleRejected):
        cycle(plan, schedule)


def test_malicious_duplicate_json_result_rejected(monkeypatch):
    plan, schedule = fixture()
    original = mod.execute_disconnected_fixture_tool

    def forged(request):
        result = original(request)
        raw = '{"count":2,"count":3,"sum":3}'
        import hashlib

        digest = hashlib.sha256(
            mod._TOOL_DOMAIN + request.operation.encode("ascii")
            + b"\0" + raw.encode("utf-8")
        ).hexdigest()
        return replace(result, canonical_result_json=raw, result_digest=digest)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", forged)
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="duplicate"):
        cycle(plan, schedule)


def test_mutating_plan_during_fixture_execution_rejected(monkeypatch):
    plan, schedule = fixture()
    original = mod.execute_disconnected_fixture_tool

    def mutated(request):
        object.__setattr__(plan.steps[-1], "operation", "math.sum")
        return original(request)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", mutated)
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="changed"):
        cycle(plan, schedule)


def test_mutating_schedule_during_fixture_execution_rejected(monkeypatch):
    plan, schedule = fixture()
    original = mod.execute_disconnected_fixture_tool

    def mutated(request):
        object.__setattr__(schedule, "schedule_digest", "f" * 64)
        return original(request)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", mutated)
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="changed"):
        cycle(plan, schedule)


@pytest.mark.parametrize("flag", mod._RECEIPT_FLAGS)
def test_receipt_cannot_gain_authority(monkeypatch, flag):
    plan, schedule = fixture()
    monkeypatch.setattr(mod.DisconnectedBatchCycleReceipt, flag, property(lambda self: True))
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="receipt changed"):
        cycle(plan, schedule)


def test_fixture_result_cannot_gain_external_authority(monkeypatch):
    plan, schedule = fixture()
    monkeypatch.setattr(DisconnectedToolResult, "external_outcome_known", property(
        lambda self: True,
    ))
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="authority"):
        cycle(plan, schedule)


class ReceiptSubclass(mod.DisconnectedBatchCycleReceipt):
    pass


def test_subclass_receipt_is_not_accepted():
    plan, schedule = fixture()
    original = cycle(plan, schedule)
    fake = ReceiptSubclass(
        original.request_id, original.plan_digest, original.schedule_digest,
        original.wave_result_hashes, original.cycle_digest,
    )
    with pytest.raises(mod.DisconnectedBatchCycleRejected, match="exact"):
        mod.verify_disconnected_batch_fixture_cycle(
            fake, plan, schedule, retained_digest=plan.plan_digest,
        )
