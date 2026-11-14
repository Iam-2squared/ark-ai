"""Restart archive verification must retain exact original carriers.

All stores are disposable SQLite and no real backend is reached.
"""

import pytest

import ark.agency.synthetic_recovery_archive_review as archive_review
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_recovery_triage import review_synthetic_write_recovery


class NeverBackend:
    def execute(self, call):
        raise AssertionError("recovery review must never dispatch")


def _fixture(tmp_path):
    call = ToolCall("offline", "mock.write", "local", {"case": "recheck-epoch"})
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("write", call),),
    )
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    registry = ToolRegistry((
        ToolRegistration("offline", "mock.write", Effect.WRITE, "inert", NeverBackend()),
    ))
    witness = review_synthetic_write_recovery(
        journal, ledger, audit, registry, call, step_id="write",
    )
    saved = archive_review.archive_synthetic_recovery(witness)
    return saved, (journal, ledger, audit, registry, call)


def _check(saved, arguments):
    return archive_review.recheck_synthetic_recovery_archive(saved, *arguments)


def _clone(text):
    new = text[:20] + text[20:]
    assert new == text and new is not text
    return new


@pytest.mark.parametrize("phase", ("first_restore", "review", "final_restore"))
def test_equal_digest_carrier_replacement_rejected_at_each_phase(
    tmp_path, monkeypatch, phase,
):
    saved, arguments = _fixture(tmp_path)
    if phase == "review":
        original = archive_review.review_synthetic_write_recovery

        def altered(*args, **kwargs):
            result = original(*args, **kwargs)
            object.__setattr__(saved, "digest", _clone(saved.digest))
            return result

        monkeypatch.setattr(archive_review, "review_synthetic_write_recovery", altered)
    else:
        original = archive_review._restore
        count = 0

        def altered(value):
            nonlocal count
            count += 1
            result = original(value)
            if count == (1 if phase == "first_restore" else 2):
                object.__setattr__(saved, "digest", _clone(saved.digest))
            return result

        monkeypatch.setattr(archive_review, "_restore", altered)

    with pytest.raises(
        archive_review.SyntheticRecoveryArchiveRejected,
        match="archive changed during restart review",
    ):
        _check(saved, arguments)


@pytest.mark.parametrize("field", ("step_state", "plan_tail", "nested_plan"))
def test_final_parser_cannot_mutate_reopened_review(
    tmp_path, monkeypatch, field,
):
    saved, arguments = _fixture(tmp_path)
    actual_review = archive_review.review_synthetic_write_recovery
    observed = {}

    def capture(*args, **kwargs):
        result = actual_review(*args, **kwargs)
        observed["fresh"] = result
        return result

    original_restore = archive_review._restore
    count = 0

    def mutate_final(value):
        nonlocal count
        count += 1
        restored = original_restore(value)
        if count == 2:
            fresh = observed["fresh"]
            if field == "step_state":
                object.__setattr__(fresh, "step_state", "running")
            elif field == "plan_tail":
                object.__setattr__(
                    fresh, "plan_tail",
                    archive_review.SyntheticPlanTail(
                        **{
                            name: getattr(fresh.plan_tail, name)
                            for name in archive_review._PLAN
                        }
                    ),
                )
            else:
                object.__setattr__(fresh.plan_tail, "event_count", 99)
        return restored

    monkeypatch.setattr(archive_review, "review_synthetic_write_recovery", capture)
    monkeypatch.setattr(archive_review, "_restore", mutate_final)
    with pytest.raises(
        archive_review.SyntheticRecoveryArchiveRejected,
        match="reopened recovery changed during final archive validation",
    ):
        _check(saved, arguments)


def test_unchanged_archive_recheck_remains_diagnostic(tmp_path):
    saved, arguments = _fixture(tmp_path)
    reviewed = _check(saved, arguments)
    assert reviewed.step_state == "pending"
    assert reviewed.ambiguous_write is False
    assert reviewed.dispatch_authorized is False
    assert reviewed.automatic_replay_authorized is False
    assert reviewed.external_outcome_known is False
