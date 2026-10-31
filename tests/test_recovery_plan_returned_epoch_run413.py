"""Cross-step recovery retains the original returned witness carriers.

All fixtures are disconnected SQLite reads and never authorize an external
effect. A later step callback must not rewrite an earlier review, even when a
nested digest is replaced with a separately allocated equal-valued string.
"""

import pytest

import ark.agency.synthetic_write_plan_recovery_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.called = False

    def execute(self, _call):
        self.called = True
        raise AssertionError("cross-store diagnosis must not dispatch")


def _fixture(tmp_path):
    backend = NeverExecute()
    calls = (
        ToolCall("writer", "write", "local", {"index": 1}),
        ToolCall("writer", "write", "local", {"index": 2}),
    )
    registry = ToolRegistry((
        ToolRegistration("writer", "write", Effect.WRITE, "mock", backend),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite",
        (PlanStep("alpha", calls[0]), PlanStep("beta", calls[1])),
    )
    path = tmp_path / "occ.sqlite"
    SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    return journal, path, audit, registry, backend


@pytest.mark.parametrize("boundary", [2, 3])
@pytest.mark.parametrize("target", ["step_state", "equal_digest_carrier"])
def test_later_step_cannot_rewrite_prior_returned_review(
    tmp_path, monkeypatch, boundary, target,
):
    state = _fixture(tmp_path)
    actual = module.review_synthetic_write_recovery
    seen = []

    def callback(*args, **kwargs):
        result = actual(*args, **kwargs)
        seen.append(result)
        if len(seen) == boundary:
            earlier = seen[0 if boundary == 2 else 1]
            if target == "step_state":
                object.__setattr__(earlier, "step_state", "succeeded")
            else:
                witness = earlier.ledger_witness
                before = witness.digest
                equal_copy = ("_" + before)[1:]
                assert equal_copy == before and equal_copy is not before
                object.__setattr__(witness, "digest", equal_copy)
        return result

    monkeypatch.setattr(module, "review_synthetic_write_recovery", callback)
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected,
        match="returned review changed",
    ):
        module.review_synthetic_write_plan(*state[:4])
    assert len(seen) == boundary
    assert state[4].called is False


def test_stable_two_write_recovery_remains_inert(tmp_path):
    state = _fixture(tmp_path)
    result = module.review_synthetic_write_plan(*state[:4])
    assert tuple(item.step_id for item in result.steps) == ("alpha", "beta")
    assert result.uncertain_step_ids == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert state[4].called is False
