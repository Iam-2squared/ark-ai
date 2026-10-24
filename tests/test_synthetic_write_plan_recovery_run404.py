"""Plan-wide restart diagnosis covers every WRITE without live dispatch.

The SQLite journals and clocks are local fixtures. A matching read-only
snapshot, including a SUCCEEDED mock, cannot prove any external effect.
"""

from pathlib import Path

import pytest

import ark.agency.synthetic_write_plan_recovery_review as module
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
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_recovery_triage import SyntheticRecoveryRejected


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic recovery cannot execute a backend")


def _setup(root: Path, *, names=("alpha", "beta"), read_step=False):
    backend = NeverExecute()
    calls = tuple(
        ToolCall("writer", "mock.write", "local", {"step": name})
        for name in names
    )
    steps = tuple(PlanStep(name, call) for name, call in zip(names, calls, strict=True))
    if read_step:
        steps += (PlanStep(
            "reader", ToolCall("viewer", "mock.read", "local"),
        ),)
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "never", backend),
        ToolRegistration("viewer", "mock.read", Effect.READ, "never", backend),
    ))
    journal = SyntheticPlanJournal(root / "plan.sqlite", steps)
    ledger_path = root / "occ.sqlite"
    ledger = SyntheticOccurrenceStore(ledger_path)
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    link = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    return journal, ledger_path, ledger, audit, registry, calls, backend, link


def _review(state, *, include_link=False):
    journal, path, _ledger, audit, registry, _calls, _backend, link = state
    return module.review_synthetic_write_plan(
        journal, path, audit, registry,
        link_store=link if include_link else None,
    )


def test_two_pending_writes_are_both_reviewed_without_authority(tmp_path):
    state = _setup(tmp_path, read_step=True)
    result = _review(state)
    assert tuple(x.step_id for x in result.steps) == ("alpha", "beta")
    assert result.uncertain_step_ids == ()
    assert all(x.step_state == "pending" for x in result.steps)
    assert result.plan_topology_digest.startswith("plan_")
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_known
    assert state[6].calls == 0


def test_running_write_remains_uncertain_after_reopening_stores(tmp_path):
    state = _setup(tmp_path)
    state[0].append("beta", StepState.RUNNING, expected_revision=0, at_ms=10)
    first = _review(state)
    assert first.uncertain_step_ids == ("beta",)
    assert first.steps[1].ambiguous_write
    reopened = _setup(tmp_path)
    assert _review(reopened).uncertain_step_ids == ("beta",)
    assert reopened[6].calls == 0


def test_local_success_does_not_claim_external_outcome(tmp_path):
    state = _setup(tmp_path)
    state[0].append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    state[0].append("alpha", StepState.SUCCEEDED, expected_revision=1, at_ms=12)
    result = _review(state)
    assert result.steps[0].step_state == "succeeded"
    assert not result.external_outcome_known
    assert not result.automatic_replay_authorized
    assert state[6].calls == 0


def test_orphan_pending_reservation_is_explicitly_uncertain(tmp_path):
    state = _setup(tmp_path)
    call = state[5][1]
    state[2].reserve_synthetic(
        state[4], call,
        OneShotAuthorization("local-only", call.request_id, 1000),
        occurrence_id="occ_" + "1" * 64, now_ms=11,
    )
    result = _review(state)
    assert result.steps[1].step_state == "pending"
    assert result.steps[1].ambiguous_write is False
    assert result.uncertain_step_ids == ("beta",)
    assert state[6].calls == 0


def test_sidecar_empty_witness_is_reconciled_for_every_write(tmp_path):
    state = _setup(tmp_path)
    result = _review(state, include_link=True)
    assert all(x.link_witness.event_count == 0 for x in result.steps)
    assert not result.dispatch_authorized
    assert state[6].calls == 0


def test_duplicate_write_request_id_is_refused_before_read(tmp_path):
    state = _setup(tmp_path, names=("duplicate",))
    repeated = (PlanStep("a", state[5][0]), PlanStep("b", state[5][0]))
    state[0]._steps = repeated
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected,
        match="share a request identity",
    ):
        _review(state)
    assert state[6].calls == 0


def test_all_read_plan_is_not_mistaken_for_write_recovery(tmp_path):
    backend = NeverExecute()
    call = ToolCall("viewer", "mock.read", "local")
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("read", call),),
    )
    path = tmp_path / "occ.sqlite"
    SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    registry = ToolRegistry((
        ToolRegistration("viewer", "mock.read", Effect.READ, "never", backend),
    ))
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected,
        match="no synthetic WRITE",
    ):
        module.review_synthetic_write_plan(journal, path, audit, registry)
    assert backend.calls == 0


def test_missing_reservation_ledger_is_not_recreated(tmp_path):
    state = _setup(tmp_path)
    state[1].unlink()
    with pytest.raises(SyntheticRecoveryRejected, match="incomplete"):
        _review(state)
    assert not state[1].exists()
    assert state[6].calls == 0


def test_cross_step_history_drift_is_rejected(tmp_path, monkeypatch):
    state = _setup(tmp_path)
    original = module.review_synthetic_write_recovery
    seen = []

    def reviewed(*args, **kwargs):
        result = original(*args, **kwargs)
        seen.append(result.step_id)
        if len(seen) == 1:
            state[3].append(state[5][0], outcome="synthetic new evidence")
        return result

    monkeypatch.setattr(module, "review_synthetic_write_recovery", reviewed)
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected,
        match="stores changed across",
    ):
        _review(state)
    assert seen == ["alpha", "beta"]
    assert state[6].calls == 0


def test_per_step_callback_path_swap_is_rejected(tmp_path, monkeypatch):
    state = _setup(tmp_path)
    original = module.review_synthetic_write_recovery

    def reviewed(*args, **kwargs):
        result = original(*args, **kwargs)
        state[0]._path = Path(str(state[0]._path))
        return result

    monkeypatch.setattr(module, "review_synthetic_write_recovery", reviewed)
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected, match="epoch changed",
    ):
        _review(state)
    assert state[6].calls == 0


@pytest.mark.parametrize("bad", (None, False, "not-an-audit", 7))
def test_wrong_audit_type_fails_before_any_backend(tmp_path, bad):
    state = _setup(tmp_path)
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected, match="exact synthetic",
    ):
        module.review_synthetic_write_plan(
            state[0], state[1], bad, state[4],
        )
    assert state[6].calls == 0


def test_plan_review_has_a_strict_topology_budget(tmp_path):
    state = _setup(tmp_path)
    state[0]._steps = tuple(
        PlanStep(
            f"step_{index}",
            ToolCall("writer", "mock.write", "local", {"index": index}),
        )
        for index in range(129)
    )
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected, match="budget exceeded",
    ):
        _review(state)
    assert state[6].calls == 0
