"""Independent preview digest and post-validation custody in disconnected scheduler."""

from __future__ import annotations

import pytest

from ark import offline_schedule_resume_review as resume
from ark.disconnected_schedule_preview import (
    DisconnectedDuePreview,
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
)
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    genesis_quarantine_witness,
)


def _fixture(tmp_path):
    policy = DisconnectedSchedulePolicy("a" * 64, 1000, 1000, 3, 100)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "digest.sqlite",
        policy=QuarantinePolicy("a" * 64, 1000, 1000, 3, 100),
        create=True,
    )
    retained = genesis_quarantine_witness(
        QuarantinePolicy("a" * 64, 1000, 1000, 3, 100)
    )
    return ledger, policy, DisconnectedScheduleCursor(0), retained


@pytest.mark.parametrize("now,state", (
    (0, "NOT_DUE"),
    (1000, "DUE_UNVERIFIED"),
    (1101, "EXPIRED_QUARANTINE"),
))
def test_original_preview_fingerprint_matches_independent_derivation(tmp_path, now, state):
    ledger, policy, cursor, retained = _fixture(tmp_path)
    result = resume.review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained, observed_now_ms=now,
    )
    assert result.next_state == state
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False
    assert ledger.inspect(retained=retained) == retained


@pytest.mark.parametrize("fake", ("0" * 64, "f" * 64))
def test_exact_preview_with_forged_well_formed_fingerprint_is_rejected(
    tmp_path, monkeypatch, fake,
):
    ledger, policy, cursor, retained = _fixture(tmp_path)
    official = resume.preview_disconnected_schedule

    def forged(*args, **kwargs):
        legitimate = official(*args, **kwargs)
        return DisconnectedDuePreview(
            legitimate.state, legitimate.next_index, legitimate.occurrence_id,
            legitimate.due_at_ms, fake,
        )

    monkeypatch.setattr(resume, "preview_disconnected_schedule", forged)
    with pytest.raises(resume.ScheduleResumeRejected, match="fingerprint"):
        resume.review_offline_schedule_resume(
            ledger, policy, cursor,
            retained_quarantine=retained, observed_now_ms=1000,
        )
    assert ledger.inspect(retained=retained) == retained


def test_preview_mutated_during_second_quarantine_read_is_rejected(tmp_path, monkeypatch):
    ledger, policy, cursor, retained = _fixture(tmp_path)
    original_preview = resume.preview_disconnected_schedule
    original_inspect = ledger.inspect
    observed = {}
    reads = 0

    def capture(*args, **kwargs):
        result = original_preview(*args, **kwargs)
        observed["preview"] = result
        return result

    def tamper(*, retained):
        nonlocal reads
        result = original_inspect(retained=retained)
        reads += 1
        if reads == 2:
            object.__setattr__(observed["preview"], "fingerprint", "0" * 64)
        return result

    monkeypatch.setattr(resume, "preview_disconnected_schedule", capture)
    monkeypatch.setattr(ledger, "inspect", tamper)
    with pytest.raises(resume.ScheduleResumeRejected, match="preview changed"):
        resume.review_offline_schedule_resume(
            ledger, policy, cursor,
            retained_quarantine=retained, observed_now_ms=1000,
        )
    assert reads == 2
    assert original_inspect(retained=retained) == retained


def test_denial_callback_cannot_rewrite_previously_verified_preview(tmp_path, monkeypatch):
    ledger, policy, cursor, retained = _fixture(tmp_path)
    original_preview = resume.preview_disconnected_schedule
    preview_holder = {}

    def capture(*args, **kwargs):
        output = original_preview(*args, **kwargs)
        preview_holder["value"] = output
        return output

    def denied_and_mutate(self):
        object.__setattr__(preview_holder["value"], "state", "NOT_DUE")
        return False

    monkeypatch.setattr(resume, "preview_disconnected_schedule", capture)
    monkeypatch.setattr(
        resume.OfflineScheduleResumeReview,
        "trusted_clock_verified",
        property(denied_and_mutate),
    )
    # Original result authority is now checked before the preview callback;
    # a preinstalled False-only substitute never gets to mutate the preview.
    with pytest.raises(resume.ScheduleResumeRejected, match="witness changed"):
        resume.review_offline_schedule_resume(
            ledger, policy, cursor,
            retained_quarantine=retained, observed_now_ms=1000,
        )
    assert preview_holder == {}
    assert ledger.inspect(retained=retained) == retained
