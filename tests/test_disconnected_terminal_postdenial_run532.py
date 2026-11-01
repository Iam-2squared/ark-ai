"""A false final terminal denial callback must not rewrite a DAG receipt."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_batch_terminal_projection as mod
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

REQ = "req_" + "d" * 32
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
    return plan, schedule


def _project(plan, schedule):
    return mod.project_disconnected_batch_terminals(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=(FIRST,),
    )


def test_normal_terminal_projection_remains_inert():
    plan, schedule = _fixture()
    result = _project(plan, schedule)
    assert result.terminal_states == (
        (FIRST, "FAILED"), (SECOND, "BLOCKED"),
    )
    assert mod.verify_disconnected_batch_terminals(
        result, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    assert all(getattr(result, flag) is False for flag in mod._FLAGS)


@pytest.mark.parametrize("mutation", ("receipt", "plan", "schedule", "descriptor"))
def test_false_last_denial_getter_cannot_mutate_terminal_epoch(
    monkeypatch, mutation,
):
    plan, schedule = _fixture()

    def malicious(self):
        if mutation == "receipt":
            object.__setattr__(self, "projection_digest", "0" * 64)
        elif mutation == "plan":
            object.__setattr__(plan.steps[-1], "operation", "text.find")
        elif mutation == "schedule":
            object.__setattr__(schedule, "schedule_digest", "f" * 64)
        else:
            monkeypatch.setattr(
                mod.DisconnectedBatchTerminalReceipt,
                "dispatch_authorized",
                property(lambda record: False),
            )
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchTerminalReceipt,
        "failure_claim_authenticated",
        property(malicious),
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="changed"):
        _project(plan, schedule)


def test_false_first_denial_getter_cannot_rewrite_terminal_projection(monkeypatch):
    plan, schedule = _fixture()

    def malicious(self):
        object.__setattr__(self, "failed_step_ids", ())
        return False

    monkeypatch.setattr(
        mod.DisconnectedBatchTerminalReceipt,
        "dispatch_authorized",
        property(malicious),
    )
    with pytest.raises(mod.DisconnectedBatchTerminalRejected, match="changed"):
        _project(plan, schedule)
