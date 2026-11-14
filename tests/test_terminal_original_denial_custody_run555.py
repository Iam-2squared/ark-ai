"""Detached Planner terminal reports reject preinstalled False-only denials.

Synthetic FAILED/BLOCKED projections describe a caller-supplied scenario,
not real failure evidence, execution authority, or automatic replay rights.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_batch_terminal_projection as terminal
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule

REQUEST = "req_" + "9" * 32
FIRST = "step_" + "1" * 16
SECOND = "step_" + "2" * 16


def _fixture():
    plan = build_disconnected_batch_plan(REQUEST, (
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
    return terminal.project_disconnected_batch_terminals(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=(FIRST,),
    )


@pytest.mark.parametrize("flag", terminal._FLAGS)
def test_preinstalled_false_getter_cannot_sanitize_terminal_projection(
    monkeypatch, flag,
):
    plan, schedule = _fixture()
    invoked = []

    def replaced(self):
        invoked.append(True)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(terminal.DisconnectedBatchTerminalReceipt, flag,
                      property(replaced))
        with pytest.raises(
            terminal.DisconnectedBatchTerminalRejected, match="receipt changed",
        ):
            _project(plan, schedule)
    assert invoked == []


@pytest.mark.parametrize("flag", terminal._FLAGS)
def test_verifier_rejects_preinstalled_false_getter_before_projection(
    monkeypatch, flag,
):
    plan, schedule = _fixture()
    receipt = _project(plan, schedule)
    invoked = []

    def replaced(self):
        invoked.append(True)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(terminal.DisconnectedBatchTerminalReceipt, flag,
                      property(replaced))
        with pytest.raises(
            terminal.DisconnectedBatchTerminalRejected,
            match="changed before replay",
        ):
            terminal.verify_disconnected_batch_terminals(
                receipt, plan, schedule, retained_digest=plan.plan_digest,
            )
    assert invoked == []


def test_clean_failure_cascade_stays_disconnected_and_non_authorizing():
    plan, schedule = _fixture()
    receipt = _project(plan, schedule)
    assert receipt.terminal_states == (
        (FIRST, "FAILED"), (SECOND, "BLOCKED"),
    )
    assert terminal.verify_disconnected_batch_terminals(
        receipt, plan, schedule, retained_digest=plan.plan_digest,
    ) is None
    assert all(getattr(receipt, name) is False for name in terminal._FLAGS)
