"""Run501 synthetic Planner terminal propagation without action execution."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_terminal_projection as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

REQ = "req_" + "c" * 32
A = "step_0000000000000001"
B = "step_0000000000000002"
C = "step_0000000000000003"
D = "step_0000000000000004"
E = "step_0000000000000005"


def fixture():
    steps = (
        DisconnectedBatchStep(A, "math.sum", '{"values":[1]}'),
        DisconnectedBatchStep(B, "math.sum", '{"values":[2]}'),
        DisconnectedBatchStep(C, "math.sum", '{"values":[3]}', (A, B)),
        DisconnectedBatchStep(D, "math.sum", '{"values":[4]}', (C,)),
        DisconnectedBatchStep(E, "math.sum", '{"values":[5]}'),
    )
    plan = build_disconnected_batch_plan(REQ, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def projection(plan, schedule, failures=()):
    return mod.project_disconnected_batch_terminals(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failures,
    )


def test_successful_hypothetical_path_is_deterministic_and_inert():
    plan, schedule = fixture()
    result = projection(plan, schedule)
    assert result.terminal_states == (
        (A, "SUCCEEDED"), (B, "SUCCEEDED"),
        (C, "SUCCEEDED"), (D, "SUCCEEDED"), (E, "SUCCEEDED"),
    )
    assert len(result.projection_digest) == 64
    assert result == projection(plan, schedule)
    assert mod.verify_disconnected_batch_terminals(
        result, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    for flag in mod._FLAGS:
        assert getattr(result, flag) is False


@pytest.mark.parametrize("failures,wanted", [
    ((A,), ("FAILED", "SUCCEEDED", "BLOCKED", "BLOCKED", "SUCCEEDED")),
    ((B,), ("SUCCEEDED", "FAILED", "BLOCKED", "BLOCKED", "SUCCEEDED")),
    ((A, B), ("FAILED", "FAILED", "BLOCKED", "BLOCKED", "SUCCEEDED")),
    ((C,), ("SUCCEEDED", "SUCCEEDED", "FAILED", "BLOCKED", "SUCCEEDED")),
    ((D,), ("SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "FAILED", "SUCCEEDED")),
    ((E,), ("SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "FAILED")),
])
def test_failure_propagation_never_claims_descendant_execution(failures, wanted):
    plan, schedule = fixture()
    result = projection(plan, schedule, failures)
    assert tuple(state for _, state in result.terminal_states) == wanted


@pytest.mark.parametrize("bad", [
    (A, A), (B, A), ("step_ffffffffffffffff",),
    (A, C), (A, D), [A], (True,), ("",), tuple([A] * 25),
])
def test_invalid_or_unreachable_hypothetical_failure_denied(bad):
    plan, schedule = fixture()
    with pytest.raises(mod.DisconnectedBatchTerminalRejected):
        projection(plan, schedule, bad)


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("plan_digest", "f" * 64),
    ("schedule_digest", "f" * 64),
    ("failed_step_ids", (C,)),
    ("failed_step_ids", [A]),
    ("terminal_states", ((A, "FAILED"),)),
    ("terminal_states", ((A, True),)),
    ("projection_digest", "f" * 64),
    ("projection_digest", True),
])
def test_detached_terminal_receipt_mutation_rejected(field, bad):
    plan, schedule = fixture()
    original = projection(plan, schedule)
    with pytest.raises(mod.DisconnectedBatchTerminalRejected):
        mod.verify_disconnected_batch_terminals(
            replace(original, **{field: bad}), plan, schedule,
            retained_digest=plan.plan_digest,
        )


def test_retained_plan_witness_required():
    plan, schedule = fixture()
    with pytest.raises(ValueError):
        mod.project_disconnected_batch_terminals(
            plan, schedule, retained_digest="f" * 64,
        )


def test_digest_callback_reflective_plan_mutation_denied(monkeypatch):
    plan, schedule = fixture()
    original = mod._digest

    def malicious(payload):
        result = original(payload)
        object.__setattr__(plan.steps[-1], "operation", "text.find")
        return result

    monkeypatch.setattr(mod, "_digest", malicious)
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="changed"):
        projection(plan, schedule)


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_terminal_projection_is_never_action_authority(monkeypatch, flag):
    plan, schedule = fixture()
    monkeypatch.setattr(mod.DisconnectedBatchTerminalReceipt, flag, property(
        lambda self: True,
    ))
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="receipt changed"):
        projection(plan, schedule)


class ForgedTerminalReceipt(mod.DisconnectedBatchTerminalReceipt):
    pass


def test_terminal_receipt_subclass_not_accepted():
    plan, schedule = fixture()
    outcome = projection(plan, schedule)
    forged = ForgedTerminalReceipt(
        outcome.request_id, outcome.plan_digest, outcome.schedule_digest,
        outcome.failed_step_ids, outcome.terminal_states,
        outcome.projection_digest,
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="exact"):
        mod.verify_disconnected_batch_terminals(
            forged, plan, schedule, retained_digest=plan.plan_digest,
        )
