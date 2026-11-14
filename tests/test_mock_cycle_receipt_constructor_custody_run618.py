"""Exact constructor custody for the *disconnected* synthetic WRITE cycle.

A local mock marker never dispatches a ToolBackend or proves an external effect.
"""

import hashlib

import pytest

from ark.agency import synthetic_mock_action_cycle_review as cycle
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _request):
        self.calls += 1
        raise AssertionError("no tool should run in the disconnected cycle")


def _setup(tmp_path):
    call = ToolCall("fixture.write", "offline.write", "synthetic", {"n": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "journal.sqlite", (PlanStep("root", call),),
    )
    occurrences = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("fixture-token", call.request_id, 1000)
    return journal, occurrences, audit, registry, call, token, backend


def _run(inputs):
    journal, occurrences, audit, registry, call, token, _ = inputs
    return cycle.run_synthetic_mock_cycle(
        journal, occurrences, audit, registry, call, token,
        step_id="root", occurrence_id="occ_" + hashlib.sha256(b"run618").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize("target", ("constructor", "class"))
def test_preinstalled_receipt_replacement_rejected_before_any_write(
    tmp_path, monkeypatch, target,
):
    state = _setup(tmp_path)
    executed = []

    def malicious(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("counterfeit receipt constructor executed")

    if target == "constructor":
        monkeypatch.setattr(cycle.SyntheticMockCycleReceipt, "__init__", malicious)
    else:
        monkeypatch.setattr(cycle, "SyntheticMockCycleReceipt", malicious)
    with pytest.raises(
        cycle.SyntheticMockCycleRejected, match="receipt authority descriptor changed",
    ):
        _run(state)
    assert executed == []
    # The preinstalled receipt override is rejected before Planner RUNNING.
    # There is no ambiguous started step and no permission to dispatch.
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
    assert state[0].recover().ambiguous_running_steps == ()
    assert state[1].count_synthetic() == 0
    assert state[2].events() == []
    assert state[-1].calls == 0


def test_mock_marker_digest_reentrant_constructor_change_stays_unknown(
    tmp_path, monkeypatch,
):
    state = _setup(tmp_path)
    executed = []
    injected = []
    original_sha256 = cycle.hashlib.sha256

    def malicious(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("counterfeit receipt constructor executed")

    def sha256(data=b""):
        digest = original_sha256(data)
        if data.startswith(b"ARK-no-action-mock-v1"):
            injected.append("marker")
            monkeypatch.setattr(cycle.SyntheticMockCycleReceipt, "__init__", malicious)
        return digest

    with monkeypatch.context() as patch:
        patch.setattr(cycle.hashlib, "sha256", sha256)
        # The registry rejects this digest before any durable mock phase,
        # so the downstream marker/receipt hook cannot be reached.
        with pytest.raises(ValueError, match="registry digest dependencies changed"):
            _run(state)
    assert injected == []
    assert executed == []
    # The original PENDING step remains unchanged; no occurrence is spent.
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
    assert state[0].recover().ambiguous_running_steps == ()
    assert state[1].count_synthetic() == 0
    assert state[2].events() == []
    assert state[-1].calls == 0


def test_postterminal_callback_cannot_execute_replaced_constructor(
    tmp_path, monkeypatch,
):
    state = _setup(tmp_path)
    executed = []
    original_append = state[0].append

    def malicious(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("counterfeit receipt constructor executed")

    def append(step_id, new_state, **kwargs):
        result = original_append(step_id, new_state, **kwargs)
        if new_state is StepState.SUCCEEDED:
            monkeypatch.setattr(cycle.SyntheticMockCycleReceipt, "__init__", malicious)
        return result

    monkeypatch.setattr(state[0], "append", append)
    with pytest.raises(
        cycle.SyntheticMockCycleRejected, match="receipt authority descriptor changed",
    ):
        _run(state)
    assert executed == []
    # The terminal marker is a committed local fixture state, never a proof of
    # a real backend effect or a reason to replay the rejected call.
    assert state[0].recover().step_statuses == (("root", "succeeded", 2),)
    assert state[-1].calls == 0


def test_original_receipt_is_denial_only_without_backend_dispatch(tmp_path):
    state = _setup(tmp_path)
    receipt = _run(state)
    assert type(receipt) is cycle.SyntheticMockCycleReceipt
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert state[-1].calls == 0
