"""Fail-closed synthetic Planner terminal policy vector custody.

No real execution, external effect, or authoritative failure outcome is used.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_batch_terminal_projection as terminal
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule


def _fixture():
    request = "req_" + "e" * 32
    steps = (
        DisconnectedBatchStep("step_" + "1" * 16, "math.sum", '{"values":[1]}'),
        DisconnectedBatchStep(
            "step_" + "2" * 16, "math.sum", '{"values":[2]}',
            ("step_" + "1" * 16,),
        ),
    )
    plan = build_disconnected_batch_plan(request, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    return plan, schedule


def _project(plan, schedule):
    return terminal.project_disconnected_batch_terminals(
        plan, schedule, retained_digest=plan.plan_digest,
    )


@pytest.mark.parametrize("vector,value", [
    ("_FLAGS", ()),
    ("_FLAGS", tuple(reversed(terminal._FLAGS))),
    ("_STATES", frozenset(("SUCCEEDED",))),
    ("_DOMAIN", b"modified-synthetic-terminal-domain"),
    ("_ORIGINAL_TERMINAL_DENIALS", ()),
    ("_RECEIPT_TYPE", object),
])
def test_mutated_terminal_policy_rejected_before_plan_review(
    monkeypatch, vector, value,
):
    plan, schedule = _fixture()

    def no_plan_access(*args, **kwargs):
        pytest.fail("modified terminal policy consulted the private plan")

    monkeypatch.setattr(terminal, vector, value)
    monkeypatch.setattr(terminal, "verify_disconnected_batch_plan", no_plan_access)
    with pytest.raises(
        terminal.DisconnectedBatchTerminalRejected, match="policy vector",
    ):
        _project(plan, schedule)


def test_forged_denial_cannot_be_hidden_by_shrinking_policy(monkeypatch):
    plan, schedule = _fixture()
    monkeypatch.setattr(terminal, "_FLAGS", ())
    monkeypatch.setattr(
        terminal.DisconnectedBatchTerminalReceipt, "dispatch_authorized",
        property(lambda self: True),
    )
    with pytest.raises(
        terminal.DisconnectedBatchTerminalRejected, match="policy vector",
    ):
        _project(plan, schedule)


def test_replay_policy_denied_before_touching_retained_receipt(monkeypatch):
    plan, schedule = _fixture()
    receipt = _project(plan, schedule)
    monkeypatch.setattr(terminal, "_STATES", frozenset())
    with pytest.raises(
        terminal.DisconnectedBatchTerminalRejected, match="policy vector",
    ):
        terminal.verify_disconnected_batch_terminals(
            receipt, plan, schedule, retained_digest=plan.plan_digest,
        )


def test_unmodified_terminal_projection_remains_digest_only():
    plan, schedule = _fixture()
    receipt = _project(plan, schedule)
    assert receipt.terminal_states == (
        ("step_" + "1" * 16, "SUCCEEDED"),
        ("step_" + "2" * 16, "SUCCEEDED"),
    )
    assert terminal.verify_disconnected_batch_terminals(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    assert receipt.dispatch_authorized is False
    assert receipt.write_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.failure_claim_authenticated is False
