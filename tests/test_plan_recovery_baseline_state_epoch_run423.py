"""Plan-wide recovery must preserve its initial journal state and each WRITE's identity.

Disconnected local SQLite fixtures only. Neither a successful diagnosis nor a
matching witness grants execution, automatic retry, consent, or external proof.
"""

import pytest

import ark.agency.synthetic_write_plan_recovery_review as review_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("offline recovery must not dispatch")


def _fixture(tmp_path):
    backend = NoDispatch()
    first = ToolCall("writer", "mock.write", "offline", {"index": 1})
    second = ToolCall("writer", "mock.write", "offline", {"index": 2})
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", (
        PlanStep("alpha", first), PlanStep("beta", second),
    ))
    journal.append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "offline", backend),
    ))
    return journal, ledger, audit, registry, backend


def _clone(text):
    copy = ("!" + text)[1:]
    assert copy == text and copy is not text
    return copy


@pytest.mark.parametrize("mutation", (
    "wrong_status", "equal_status_tuple", "wrong_running",
    "equal_running_tuple", "equal_tail", "equal_tail_digest",
))
def test_reentrant_step_review_cannot_rewrite_initial_plan_recovery(
    tmp_path, monkeypatch, mutation,
):
    state = _fixture(tmp_path)
    native_recover = SyntheticPlanJournal.recover
    native_step = review_module.review_synthetic_write_recovery
    original = []
    callback_count = []

    def collect(self, *args, **kwargs):
        snapshot = native_recover(self, *args, **kwargs)
        if not original:
            original.append(snapshot)
        return snapshot

    def injected(*args, **kwargs):
        reviewed = native_step(*args, **kwargs)
        if not callback_count:
            callback_count.append(True)
            baseline = original[0]
            if mutation == "wrong_status":
                changed = (("alpha", "succeeded", 2), *baseline.step_statuses[1:])
                object.__setattr__(baseline, "step_statuses", changed)
            elif mutation == "equal_status_tuple":
                replacement = tuple(list(baseline.step_statuses))
                assert replacement == baseline.step_statuses
                assert replacement is not baseline.step_statuses
                object.__setattr__(baseline, "step_statuses", replacement)
            elif mutation == "wrong_running":
                object.__setattr__(baseline, "ambiguous_running_steps", ())
            elif mutation == "equal_running_tuple":
                replacement = tuple(list(baseline.ambiguous_running_steps))
                assert replacement == baseline.ambiguous_running_steps
                assert replacement is not baseline.ambiguous_running_steps
                object.__setattr__(baseline, "ambiguous_running_steps", replacement)
            elif mutation == "equal_tail":
                from dataclasses import replace

                object.__setattr__(baseline, "tail", replace(baseline.tail))
            else:
                object.__setattr__(
                    baseline.tail, "status_digest", _clone(baseline.tail.status_digest),
                )
        return reviewed

    monkeypatch.setattr(SyntheticPlanJournal, "recover", collect)
    monkeypatch.setattr(review_module, "review_synthetic_write_recovery", injected)
    with pytest.raises(
        review_module.SyntheticWritePlanReviewRejected,
        match="returned review changed",
    ):
        review_module.review_synthetic_write_plan(*state[:4])
    assert callback_count == [True]
    assert state[4].calls == 0


@pytest.mark.parametrize("mutation", (
    "step_id", "request_id", "registry_revision", "step_state",
))
def test_per_step_review_must_match_original_journal_and_registry(
    tmp_path, monkeypatch, mutation,
):
    state = _fixture(tmp_path)
    native = review_module.review_synthetic_write_recovery

    def forged(*args, **kwargs):
        receipt = native(*args, **kwargs)
        replacement = {
            "step_id": "beta",
            "request_id": "act_" + "0" * 64,
            "registry_revision": "tools_" + "0" * 64,
            "step_state": "succeeded",
        }[mutation]
        object.__setattr__(receipt, mutation, replacement)
        return receipt

    monkeypatch.setattr(review_module, "review_synthetic_write_recovery", forged)
    with pytest.raises(
        review_module.SyntheticWritePlanReviewRejected,
        match="per-step recovery differs",
    ):
        review_module.review_synthetic_write_plan(*state[:4])
    assert state[4].calls == 0


def test_unchanged_running_write_is_held_and_never_authorizes_replay(tmp_path):
    state = _fixture(tmp_path)
    result = review_module.review_synthetic_write_plan(*state[:4])
    assert tuple(item.step_id for item in result.steps) == ("alpha", "beta")
    assert result.uncertain_step_ids == ("alpha",)
    assert result.downstream_write_hold_step_ids == ()
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_known
    assert state[4].calls == 0
