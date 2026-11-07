"""Adversarial detached terminal and request-bound fixture verification."""

import hashlib
from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_failure_fixture as mod
import ark.agency.disconnected_batch_terminal_projection as terminal
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule
from ark.agency.disconnected_fixture_binding import DisconnectedFixtureBinding

A = "step_0000000000000001"
B = "step_0000000000000002"
C = "step_0000000000000003"


def fixture(request_id="req_" + "c" * 32):
    plan = build_disconnected_batch_plan(request_id, (
        DisconnectedBatchStep(A, "math.sum", '{"values":[1,2]}'),
        DisconnectedBatchStep(B, "text.find", '{"needle":"a","text":"abc"}'),
        DisconnectedBatchStep(C, "math.sum", '{"values":[4]}', (A, B)),
    ))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def simulate(plan, schedule, failures=()):
    return mod.simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failures,
    )


def test_real_in_memory_fixture_is_request_bound_and_inert():
    plan, schedule = fixture()
    report = simulate(plan, schedule)
    assert len(report.result_digests) == 3
    assert all(len(digest) == 64 for _, digest in report.result_digests)
    assert report == simulate(plan, schedule)
    assert mod.verify_disconnected_failure_fixture(
        report, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    for flag in mod._FLAGS:
        assert getattr(report, flag) is False


def test_identical_fixture_operation_in_distinct_requests_has_distinct_binding():
    first, first_schedule = fixture("req_" + "c" * 32)
    second, second_schedule = fixture("req_" + "d" * 32)
    first_result = simulate(first, first_schedule)
    second_result = simulate(second, second_schedule)
    assert first_result.result_digests[0][0] == second_result.result_digests[0][0]
    assert first_result.result_digests[0][1] != second_result.result_digests[0][1]


@pytest.mark.parametrize("field,forged", [
    ("projection_digest", "f" * 64),
    ("terminal_states", ((A, "BLOCKED"), (B, "SUCCEEDED"), (C, "SUCCEEDED"))),
    ("failed_step_ids", (A,)),
    ("request_id", "req_" + "f" * 32),
])
def test_forged_terminal_projection_never_reaches_toolbox(monkeypatch, field, forged):
    plan, schedule = fixture()
    original = terminal.project_disconnected_batch_terminals
    called = []

    def fake(*args, **kwargs):
        return replace(original(*args, **kwargs), **{field: forged})

    def mock_tool(request):
        called.append(request)
        raise AssertionError("must not run")

    monkeypatch.setattr(mod, "project_disconnected_batch_terminals", fake)
    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", mock_tool)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected):
        simulate(plan, schedule)
    assert called == []


@pytest.mark.parametrize("flag", [
    "dispatch_authorized", "write_authorized", "automatic_replay_authorized",
    "failure_claim_authenticated",
])
def test_projected_terminal_cannot_claim_action_authority(monkeypatch, flag):
    plan, schedule = fixture()
    monkeypatch.setattr(
        terminal.DisconnectedBatchTerminalReceipt, flag,
        property(lambda self: True),
    )
    # The lower-level terminal projector may itself reject the forged
    # receipt before the detached wrapper has received a result.
    with pytest.raises(ValueError):
        simulate(plan, schedule)


def test_terminal_receipt_subclass_does_not_propagate(monkeypatch):
    plan, schedule = fixture()
    original = terminal.project_disconnected_batch_terminals

    class TerminalSubclass(terminal.DisconnectedBatchTerminalReceipt):
        pass

    def fake(*args, **kwargs):
        receipt = original(*args, **kwargs)
        return TerminalSubclass(
            receipt.request_id, receipt.plan_digest, receipt.schedule_digest,
            receipt.failed_step_ids, receipt.terminal_states, receipt.projection_digest,
        )

    monkeypatch.setattr(mod, "project_disconnected_batch_terminals", fake)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="authority"):
        simulate(plan, schedule)


def test_self_consistent_forged_mock_result_is_not_valid_fixture(monkeypatch):
    plan, schedule = fixture()
    original = mod.execute_disconnected_fixture_tool

    def forged(request):
        result = original(request)
        if request.operation != "math.sum":
            return result
        raw = '{"count":2,"sum":999}'
        digest = hashlib.sha256(
            mod._TOOL_DOMAIN + request.operation.encode("ascii") +
            b"\0" + raw.encode("utf-8")
        ).hexdigest()
        return replace(result, canonical_result_json=raw, result_digest=digest)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", forged)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="recomputation"):
        simulate(plan, schedule)


@pytest.mark.parametrize("field,value", [
    ("request_id", "req_" + "a" * 32),
    ("input_digest", "f" * 64),
    ("result_digest", "f" * 64),
    ("request_bound_digest", "f" * 64),
])
def test_independently_forged_binding_receipt_rejected(monkeypatch, field, value):
    plan, schedule = fixture()
    original = mod.bind_disconnected_fixture_result

    def fake(request, result):
        return replace(original(request, result), **{field: value})

    monkeypatch.setattr(mod, "bind_disconnected_fixture_result", fake)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected):
        simulate(plan, schedule)


@pytest.mark.parametrize("flag", [
    "dispatch_authorized", "external_outcome_verified",
    "automatic_replay_authorized",
])
def test_binding_never_promotes_mock_evidence_to_authority(monkeypatch, flag):
    plan, schedule = fixture()
    monkeypatch.setattr(
        DisconnectedFixtureBinding, flag, property(lambda self: True),
    )
    # The existing request-binding guard may fail inside its own constructor
    # before the outer detached fixture performs the final authority check.
    with pytest.raises(mod.DisconnectedFailureFixtureRejected):
        simulate(plan, schedule)


def test_result_mutated_by_binding_callback_rejected(monkeypatch):
    plan, schedule = fixture()
    original = mod.bind_disconnected_fixture_result

    def mutate(request, result):
        bound = original(request, result)
        object.__setattr__(result, "result_digest", "f" * 64)
        return bound

    monkeypatch.setattr(mod, "bind_disconnected_fixture_result", mutate)
    with pytest.raises(mod.DisconnectedFailureFixtureRejected, match="changed"):
        simulate(plan, schedule)
