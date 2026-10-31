"""Plan-wide recovery must honor caller-retained prefixes across restarts.

Independent disposable SQLite stores simulate lost historical evidence. The
reviewer remains read-only and has no backend/replay authority.
"""

from pathlib import Path

import pytest

import ark.agency.synthetic_write_plan_recovery_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    ActionAuditSchemaError,
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)


class NoDispatch:
    def execute(self, _call):
        raise AssertionError("plan recovery cannot invoke a real backend")


def _fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    backend = NoDispatch()
    calls = (
        ToolCall("writer", "mock.write", "local", {"step": "one"}),
        ToolCall("writer", "mock.write", "local", {"step": "two"}),
    )
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("one", calls[0]),
        PlanStep("two", calls[1], ("one",)),
    ))
    path = root / "ledger.sqlite"
    ledger = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "mock", backend),
    ))
    link = SyntheticOccurrenceAuditLinkStore(root / "link.sqlite")
    return journal, path, audit, registry, calls, ledger, link


def _review(state, **kwargs):
    return module.review_synthetic_write_plan(
        *state[:4], link_store=state[6], **kwargs,
    )


def _retain(review):
    first = review.steps[0]
    return {
        "retained_plan": first.plan_tail,
        "retained_ledger": first.ledger_witness,
        "retained_audit": first.audit_witness,
        "retained_link": first.link_witness,
    }


def test_stable_reopen_accepts_all_four_independent_prefixes(tmp_path):
    state = _fixture(tmp_path)
    original = _review(state)
    reopened = _fixture(tmp_path)
    restored = _review(reopened, **_retain(original))
    assert restored == original
    assert not restored.dispatch_authorized
    assert not restored.automatic_replay_authorized
    assert not restored.external_outcome_known


def test_new_empty_plan_cannot_erase_previously_running_write(tmp_path):
    observed = _fixture(tmp_path / "observed")
    observed[0].append("one", StepState.RUNNING, expected_revision=0, at_ms=10)
    retained = _retain(_review(observed))
    replacement = _fixture(tmp_path / "replacement")
    with pytest.raises(SyntheticPlanJournalRejected):
        _review(replacement, **retained)


def test_new_empty_ledger_cannot_erase_prior_pending_reservation(tmp_path):
    observed = _fixture(tmp_path / "observed")
    call = observed[4][1]
    observed[5].reserve_synthetic(
        observed[3], call,
        OneShotAuthorization("synthetic-local-only", call.request_id, 1000),
        occurrence_id="occ_" + "2" * 64, now_ms=11,
    )
    original = _review(observed)
    assert original.uncertain_step_ids == ("two",)
    replacement = _fixture(tmp_path / "replacement")
    assert _review(replacement).uncertain_step_ids == ()
    with pytest.raises(SyntheticReplayRejected, match="retained reservation"):
        _review(replacement, **_retain(original))


def test_new_empty_audit_cannot_erase_previously_observed_event(tmp_path):
    observed = _fixture(tmp_path / "observed")
    observed[2].append(observed[4][0], outcome="synthetic fixture evidence")
    original = _review(observed)
    replacement = _fixture(tmp_path / "replacement")
    with pytest.raises(ActionAuditSchemaError, match="shorter than retained"):
        _review(replacement, **_retain(original))


def test_retained_link_requires_a_real_sidecar_store(tmp_path):
    state = _fixture(tmp_path)
    witness = _retain(_review(state))
    with pytest.raises(module.SyntheticWritePlanReviewRejected, match="exact"):
        module.review_synthetic_write_plan(
            *state[:4], retained_link=witness["retained_link"],
        )


def test_retained_witness_carrier_change_mid_review_is_rejected(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    state[2].append(state[4][0], outcome="synthetic audit")
    retained = _retain(_review(state))
    witness = retained["retained_audit"]
    original = module.review_synthetic_write_recovery
    seen = []

    def swapped(*args, **kwargs):
        result = original(*args, **kwargs)
        seen.append(result.step_id)
        if len(seen) == 1:
            new_digest = witness.chain_sha256.encode("ascii").decode("ascii")
            assert new_digest == witness.chain_sha256
            assert new_digest is not witness.chain_sha256
            object.__setattr__(witness, "chain_sha256", new_digest)
        return result

    monkeypatch.setattr(module, "review_synthetic_write_recovery", swapped)
    with pytest.raises(
        module.SyntheticWritePlanReviewRejected, match="epoch changed",
    ):
        _review(state, **retained)
    assert seen == ["one"]
