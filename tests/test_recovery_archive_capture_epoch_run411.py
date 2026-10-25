"""Offline archive capture and retained-UNKNOWN regression probes.

Local hashes and mock Planner statuses cannot authorize a ToolBackend action.
"""

import pytest

import ark.agency.synthetic_recovery_archive_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_recovery_triage import review_synthetic_write_recovery


class NeverBackend:
    def execute(self, call):
        raise AssertionError("no backend may execute during archive review")


def _fixture(tmp_path):
    call = ToolCall("offline", "mock.write", "local", {"case": "capture"})
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("write", call),),
    )
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    registry = ToolRegistry((
        ToolRegistration("offline", "mock.write", Effect.WRITE, "inert", NeverBackend()),
    ))
    return call, journal, ledger, audit, registry


def _review(state):
    call, journal, ledger, audit, registry = state
    return review_synthetic_write_recovery(
        journal, ledger, audit, registry, call, step_id="write",
    )


@pytest.mark.parametrize("phase", ("serialize", "digest", "restore"))
def test_archive_capture_rejects_mutation_at_every_callback_phase(
    tmp_path, monkeypatch, phase,
):
    review = _review(_fixture(tmp_path))
    if phase == "serialize":
        original = module._canonical

        def altered(value):
            result = original(value)
            object.__setattr__(review.plan_tail, "status_digest", "state_" + "f" * 64)
            return result

        monkeypatch.setattr(module, "_canonical", altered)
    elif phase == "digest":
        original = module._digest

        def altered(value):
            result = original(value)
            object.__setattr__(review, "request_id", review.request_id + "_")
            return result

        monkeypatch.setattr(module, "_digest", altered)
    else:
        original = module._restore

        def altered(value):
            result = original(value)
            object.__setattr__(review.audit_witness, "chain_sha256", "f" * 64)
            return result

        monkeypatch.setattr(module, "_restore", altered)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="review changed"):
        module.archive_synthetic_recovery(review)


def test_equal_valued_request_carrier_replacement_is_not_silent(
    tmp_path, monkeypatch,
):
    review = _review(_fixture(tmp_path))
    original = module._canonical

    def altered(value):
        result = original(value)
        current = review.request_id
        replacement = current[:20] + current[20:]
        assert replacement == current and replacement is not current
        object.__setattr__(review, "request_id", replacement)
        return result

    monkeypatch.setattr(module, "_canonical", altered)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="review changed"):
        module.archive_synthetic_recovery(review)


def test_archive_object_changed_during_validation_is_not_returned(
    tmp_path, monkeypatch,
):
    review = _review(_fixture(tmp_path))
    original = module._restore

    def altered(archive):
        result = original(archive)
        digest = archive.digest
        cloned = digest[:20] + digest[20:]
        assert cloned == digest and cloned is not digest
        object.__setattr__(archive, "digest", cloned)
        return result

    monkeypatch.setattr(module, "_restore", altered)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="archive changed"):
        module.archive_synthetic_recovery(review)


@pytest.mark.parametrize("terminal", (StepState.SUCCEEDED, StepState.FAILED))
def test_retained_unknown_cannot_be_cleared_by_local_terminal_status(
    tmp_path, terminal,
):
    state = _fixture(tmp_path)
    state[1].append("write", StepState.RUNNING, expected_revision=0, at_ms=10)
    archive = module.archive_synthetic_recovery(_review(state))
    state[1].append("write", terminal, expected_revision=1, at_ms=11)
    with pytest.raises(
        module.SyntheticRecoveryArchiveRejected, match="archived UNKNOWN WRITE",
    ):
        module.recheck_synthetic_recovery_archive(archive, *state)


def test_retained_unknown_remains_diagnostic_without_live_authority(tmp_path):
    state = _fixture(tmp_path)
    state[1].append("write", StepState.RUNNING, expected_revision=0, at_ms=10)
    archive = module.archive_synthetic_recovery(_review(state))
    fresh = module.recheck_synthetic_recovery_archive(archive, *state)
    assert fresh.ambiguous_write
    assert not fresh.dispatch_authorized
    assert not fresh.automatic_replay_authorized
    assert not fresh.external_outcome_known
