"""Synthetic three-store WRITE fixtures must retain deny-only authority and identity.

These tests deliberately simulate reflected Python mutations. They do NOT
create real approval, dispatch a backend, or establish cross-store atomicity.
"""

import hashlib

import pytest

import ark.agency.synthetic_mock_action_cycle_review as cycle
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)

_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "external_outcome_known",
)


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("mock-only WRITE may not dispatch")


def _setup(tmp_path):
    call = ToolCall("offline.write", "write.fixture", "synthetic", {"x": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrence.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("offline.write", "write.fixture", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("single-use", call.request_id, 1000)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    return journal, ledger, audit, registry, call, token, links, backend


def _run(state, *, with_link=False):
    journal, ledger, audit, registry, call, token, links, _ = state
    return cycle.run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root", occurrence_id="occ_" + hashlib.sha256(b"run600").hexdigest(),
        now_ms=10, link_store=links if with_link else None,
    )


@pytest.mark.parametrize("flag", _DENIALS)
@pytest.mark.parametrize("moment", ("before", "after_reservation"))
def test_false_looking_receipt_descriptor_never_executes(
    tmp_path, monkeypatch, flag, moment,
):
    state = _setup(tmp_path)
    seen = []

    def spoof(self):
        seen.append(flag)
        return False

    def install():
        monkeypatch.setattr(
            cycle.SyntheticMockCycleReceipt, flag, property(spoof),
        )

    if moment == "before":
        install()
    else:
        original = state[2].append

        def append(*args, **kwargs):
            event = original(*args, **kwargs)
            install()
            return event

        monkeypatch.setattr(state[2], "append", append)
    with pytest.raises(
        cycle.SyntheticMockCycleRejected,
        match="receipt authority descriptor changed",
    ):
        _run(state)
    assert seen == []
    assert state[-1].calls == 0
    if moment == "before":
        assert state[0].recover().step_statuses == (("root", "pending", 0),)
        assert state[1].count_synthetic() == 0
        assert state[2].events() == []
    else:
        assert state[0].recover().ambiguous_running_steps == ("root",)
        assert state[1].count_synthetic() == 1
        assert len(state[2].events()) == 1


def test_equal_value_reservation_identity_swap_is_unknown_not_replay(
    tmp_path, monkeypatch,
):
    state = _setup(tmp_path)
    captured = []
    real_reserve = state[1].reserve_synthetic
    real_audit = state[2].append

    def reserve(*args, **kwargs):
        receipt = real_reserve(*args, **kwargs)
        captured.append(receipt)
        return receipt

    def audit_and_swap(*args, **kwargs):
        event = real_audit(*args, **kwargs)
        receipt = captured[0]
        original = receipt.occurrence_id
        substitute = ("x" + original)[1:]
        assert substitute == original and substitute is not original
        object.__setattr__(receipt, "occurrence_id", substitute)
        return event

    monkeypatch.setattr(state[1], "reserve_synthetic", reserve)
    monkeypatch.setattr(state[2], "append", audit_and_swap)
    with pytest.raises(
        cycle.SyntheticMockCycleRejected, match="reservation receipt changed",
    ):
        _run(state)
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1
    assert state[-1].calls == 0


def test_equal_value_audit_identity_swap_during_link_is_unknown(
    tmp_path, monkeypatch,
):
    state = _setup(tmp_path)
    captured = []
    real_audit = state[2].append
    real_link = state[6].link_synthetic

    def append(*args, **kwargs):
        event = real_audit(*args, **kwargs)
        captured.append(event)
        return event

    def link_and_swap(*args, **kwargs):
        receipt = real_link(*args, **kwargs)
        event = captured[0]
        original = event.request_id
        substitute = ("x" + original)[1:]
        assert substitute == original and substitute is not original
        object.__setattr__(event, "request_id", substitute)
        return receipt

    monkeypatch.setattr(state[2], "append", append)
    monkeypatch.setattr(state[6], "link_synthetic", link_and_swap)
    with pytest.raises(
        cycle.SyntheticMockCycleRejected, match="audit receipt changed",
    ):
        _run(state, with_link=True)
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1
    assert state[6].read_witness().event_count == 1
    assert state[-1].calls == 0


def test_ordinary_mock_result_has_no_effect_or_replay_authority(tmp_path):
    state = _setup(tmp_path)
    receipt = _run(state, with_link=True)
    assert all(getattr(receipt, key) is False for key in _DENIALS)
    assert state[0].recover().step_statuses == (("root", "succeeded", 2),)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1
    assert state[6].read_witness().event_count == 1
    with pytest.raises(cycle.SyntheticMockCycleRejected, match="cannot retry"):
        _run(state)
    assert state[-1].calls == 0
