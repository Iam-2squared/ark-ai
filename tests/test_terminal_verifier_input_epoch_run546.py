"""Run546: a detached terminal verifier must retain caller and denial epochs."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_batch_terminal_projection as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

REQ = "req_" + "a" * 32
FIRST = "step_" + "1" * 16
SECOND = "step_" + "2" * 16


def _fixture():
    plan = build_disconnected_batch_plan(REQ, (
        DisconnectedBatchStep(FIRST, "math.sum", '{"values":[1]}'),
        DisconnectedBatchStep(
            SECOND, "math.sum", '{"values":[2]}', (FIRST,),
        ),
    ))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    receipt = mod.project_disconnected_batch_terminals(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=(FIRST,),
    )
    return plan, schedule, receipt


def _verify(plan, schedule, receipt):
    return mod.verify_disconnected_batch_terminals(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    )


def test_readonly_terminal_verifier_still_accepts_intact_receipt():
    plan, schedule, receipt = _fixture()
    assert _verify(plan, schedule, receipt) is None
    assert all(getattr(receipt, name) is False for name in mod._FLAGS)


@pytest.mark.parametrize("field", (
    "failed_step_ids", "terminal_states", "projection_digest",
))
def test_projector_cannot_rebase_equal_valued_caller_receipt(
    monkeypatch, field,
):
    plan, schedule, receipt = _fixture()
    original = mod.project_disconnected_batch_terminals

    def changing_projector(*args, **kwargs):
        projected = original(*args, **kwargs)
        old = getattr(receipt, field)
        if type(old) is tuple:
            replacement = tuple([*old])
        else:
            replacement = "".join((old[:1], old[1:]))
        assert replacement == old and replacement is not old
        object.__setattr__(receipt, field, replacement)
        return projected

    monkeypatch.setattr(
        mod, "project_disconnected_batch_terminals", changing_projector,
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="changed"):
        _verify(plan, schedule, receipt)


def test_false_last_denial_cannot_replace_earlier_authority_descriptor(monkeypatch):
    plan, schedule, receipt = _fixture()

    def malicious(self):
        if self is receipt:
            monkeypatch.setattr(
                mod.DisconnectedBatchTerminalReceipt,
                "dispatch_authorized",
                property(lambda _record: True),
            )
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchTerminalReceipt,
        "failure_claim_authenticated",
        property(malicious),
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="changed"):
        _verify(plan, schedule, receipt)


def test_false_first_denial_cannot_replace_equal_terminal_states(monkeypatch):
    plan, schedule, receipt = _fixture()

    def malicious(self):
        if self is receipt:
            old = self.terminal_states
            object.__setattr__(self, "terminal_states", tuple([*old]))
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchTerminalReceipt,
        "dispatch_authorized",
        property(malicious),
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="changed"):
        _verify(plan, schedule, receipt)


def test_forged_receipt_values_still_denied():
    plan, schedule, receipt = _fixture()
    fake = replace(receipt, projection_digest="0" * 64)
    with pytest.raises(mod.DisconnectedBatchTerminalRejected):
        _verify(plan, schedule, fake)
