"""A persisted overdue prefix can be matched to a passive next-slot preview."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from ark import offline_schedule_resume_review as resume
from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
)
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    QuarantineWitness,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


def _fixture(tmp_path):
    policy = DisconnectedSchedulePolicy("a" * 64, 1000, 1000, 3, 100)
    qpolicy = QuarantinePolicy("a" * 64, 1000, 1000, 3, 100)
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=qpolicy, create=True,
    )
    initial = genesis_quarantine_witness(qpolicy)
    return path, ledger, policy, qpolicy, initial


def _review(ledger, policy, cursor, witness, now):
    return resume.review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=witness,
        observed_now_ms=now,
    )


@pytest.mark.parametrize("now,expected", (
    (999, "NOT_DUE"), (1000, "DUE_UNVERIFIED"),
    (1100, "DUE_UNVERIFIED"), (1101, "EXPIRED_QUARANTINE"),
))
def test_genesis_only_classifies_next_claimed_slot(tmp_path, now, expected):
    _, ledger, policy, _, genesis = _fixture(tmp_path)
    review = _review(
        ledger, policy, DisconnectedScheduleCursor(0), genesis, now,
    )
    assert review.quarantined_count == 0
    assert review.next_state == expected
    assert review.notification_authorized is False
    assert review.tool_execution_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.trusted_clock_verified is False
    assert review.consent_verified is False


def test_restart_from_persisted_quarantine_cannot_repeat_first_slot(tmp_path):
    path, ledger, policy, qpolicy, genesis = _fixture(tmp_path)
    first = derive_quarantined_occurrence(qpolicy, 0)
    saved = ledger.quarantine_expired(
        index=0, occurrence_id=first, observed_ms=1200, retained=genesis,
    )
    reopened = DisconnectedScheduleQuarantineLedger(
        path, policy=qpolicy, create=False,
    )
    cursor = DisconnectedScheduleCursor(1, first)
    witness = _review(reopened, policy, cursor, saved.witness, 1800)
    assert witness.quarantined_count == 1
    assert witness.next_state == "NOT_DUE"
    assert witness.next_occurrence_id == derive_quarantined_occurrence(qpolicy, 1)
    assert witness == _review(reopened, policy, cursor, saved.witness, 1800)
    assert reopened.inspect(retained=saved.witness) == saved.witness


def test_stale_restart_cursor_cannot_undo_quarantined_prefix(tmp_path):
    _, ledger, policy, qpolicy, genesis = _fixture(tmp_path)
    first = derive_quarantined_occurrence(qpolicy, 0)
    saved = ledger.quarantine_expired(
        index=0, occurrence_id=first, observed_ms=1200, retained=genesis,
    )
    with pytest.raises(resume.ScheduleResumeRejected, match="prefix"):
        _review(ledger, policy, DisconnectedScheduleCursor(0), saved.witness, 1800)


def test_wrong_previous_slot_refused_even_with_matching_count(tmp_path):
    _, ledger, policy, qpolicy, genesis = _fixture(tmp_path)
    first = derive_quarantined_occurrence(qpolicy, 0)
    saved = ledger.quarantine_expired(
        index=0, occurrence_id=first, observed_ms=1200, retained=genesis,
    )
    with pytest.raises(resume.ScheduleResumeRejected, match="identity"):
        _review(
            ledger, policy, DisconnectedScheduleCursor(1, "slot_" + "f" * 64),
            saved.witness, 1800,
        )


def test_schedule_policy_mismatch_cannot_reuse_another_ledger(tmp_path):
    _, ledger, _, _, genesis = _fixture(tmp_path)
    changed = DisconnectedSchedulePolicy("a" * 64, 2000, 1000, 3, 100)
    with pytest.raises(resume.ScheduleResumeRejected, match="prefix"):
        _review(ledger, changed, DisconnectedScheduleCursor(0), genesis, 2100)


@pytest.mark.parametrize("clock", (True, 1200.0, "1200", -1))
def test_caller_time_requires_exact_bounded_integer(tmp_path, clock):
    _, ledger, policy, _, genesis = _fixture(tmp_path)
    with pytest.raises(resume.ScheduleResumeRejected, match="exact"):
        _review(ledger, policy, DisconnectedScheduleCursor(0), genesis, clock)


def test_wrong_retained_quarantine_hash_refused(tmp_path):
    _, ledger, policy, _, genesis = _fixture(tmp_path)
    invalid = QuarantineWitness(0, "0" * 64)
    assert invalid != genesis
    with pytest.raises(resume.ScheduleResumeRejected):
        _review(ledger, policy, DisconnectedScheduleCursor(0), invalid, 1000)


def test_reentrant_preview_cannot_retarget_cursor(monkeypatch, tmp_path):
    _, ledger, policy, _, genesis = _fixture(tmp_path)
    cursor = DisconnectedScheduleCursor(0)
    original = resume.preview_disconnected_schedule

    def retarget(*args, **kwargs):
        outcome = original(*args, **kwargs)
        object.__setattr__(cursor, "next_index", 1)
        return outcome

    monkeypatch.setattr(resume, "preview_disconnected_schedule", retarget)
    with pytest.raises(resume.ScheduleResumeRejected, match="carrier changed"):
        _review(ledger, policy, cursor, genesis, 1000)


def test_quarantine_drift_between_reads_is_denied(monkeypatch, tmp_path):
    path, ledger, policy, qpolicy, genesis = _fixture(tmp_path)
    first = derive_quarantined_occurrence(qpolicy, 0)
    saved = ledger.quarantine_expired(
        index=0, occurrence_id=first, observed_ms=1200, retained=genesis,
    )
    cursor = DisconnectedScheduleCursor(1, first)
    original = ledger.inspect
    calls = 0

    def drift(*, retained):
        nonlocal calls
        witness = original(retained=retained)
        calls += 1
        if calls == 1:
            with sqlite3.connect(path) as conn:
                conn.execute("UPDATE quarantines SET observed_ms=1201")
        return witness

    monkeypatch.setattr(ledger, "inspect", drift)
    with pytest.raises(resume.ScheduleResumeRejected):
        _review(ledger, policy, cursor, saved.witness, 1800)


def test_final_false_authority_getter_cannot_rewrite_witness(monkeypatch, tmp_path):
    _, ledger, policy, _, genesis = _fixture(tmp_path)

    def malicious_false(self):
        object.__setattr__(self, "quarantined_count", 777)
        return False

    monkeypatch.setattr(
        resume.OfflineScheduleResumeReview, "consent_verified",
        property(malicious_false),
    )
    # Import-time descriptor custody now denies the forged callback before
    # it can mutate a constructed result; a late result drift is also rejected.
    with pytest.raises(
        resume.ScheduleResumeRejected, match="witness changed|denial descriptor replaced",
    ):
        _review(ledger, policy, DisconnectedScheduleCursor(0), genesis, 1000)


@pytest.mark.parametrize("spoof", (
    "wrong_state", "wrong_due", "wrong_occurrence", "boolean_due",
))
def test_restart_rejects_forged_exact_type_preview_without_any_dispatch(
    tmp_path, monkeypatch, spoof,
):
    _, ledger, policy, _, genesis = _fixture(tmp_path)
    native = resume.preview_disconnected_schedule

    def forged(*args, **kwargs):
        value = native(*args, **kwargs)
        changes = {
            "wrong_state": {"state": "NOT_DUE"},
            "wrong_due": {"due_at_ms": 1001},
            "wrong_occurrence": {"occurrence_id": "slot_" + "f" * 64},
            "boolean_due": {"due_at_ms": True},
        }
        return replace(value, **changes[spoof])

    monkeypatch.setattr(resume, "preview_disconnected_schedule", forged)
    with pytest.raises(resume.ScheduleResumeRejected, match="preview"):
        _review(ledger, policy, DisconnectedScheduleCursor(0), genesis, 1000)
    assert ledger.inspect(retained=genesis) == genesis


def test_boolean_index_equal_to_one_cannot_imitate_restart_cursor(
    tmp_path, monkeypatch,
):
    _, ledger, policy, qpolicy, genesis = _fixture(tmp_path)
    first = derive_quarantined_occurrence(qpolicy, 0)
    saved = ledger.quarantine_expired(
        index=0, occurrence_id=first, observed_ms=1200, retained=genesis,
    )
    native = resume.preview_disconnected_schedule

    def forged(*args, **kwargs):
        return replace(native(*args, **kwargs), next_index=True)

    monkeypatch.setattr(resume, "preview_disconnected_schedule", forged)
    with pytest.raises(resume.ScheduleResumeRejected, match="preview"):
        _review(
            ledger, policy, DisconnectedScheduleCursor(1, first),
            saved.witness, 1800,
        )
    assert ledger.inspect(retained=saved.witness) == saved.witness


def test_honest_due_classification_is_unverified_and_never_authorizing(tmp_path):
    _, ledger, policy, _, genesis = _fixture(tmp_path)
    outcome = _review(
        ledger, policy, DisconnectedScheduleCursor(0), genesis, 1000,
    )
    assert outcome.next_state == "DUE_UNVERIFIED"
    assert outcome.notification_authorized is False
    assert outcome.tool_execution_authorized is False
    assert outcome.automatic_replay_authorized is False
