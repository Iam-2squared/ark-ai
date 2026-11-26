"""Restart previews may not inherit a callback-installed False-only authority."""

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
    QuarantineWitness,
    genesis_quarantine_witness,
)


def _case(tmp_path):
    settings = ("a" * 64, 1000, 1000, 3, 100)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "offline-quarantine.sqlite",
        policy=QuarantinePolicy(*settings), create=True,
    )
    policy = DisconnectedSchedulePolicy(*settings)
    retained = genesis_quarantine_witness(QuarantinePolicy(*settings))
    return ledger, policy, DisconnectedScheduleCursor(0), retained


def _review(case):
    ledger, policy, cursor, retained = case
    return resume.review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=1000,
    )


@pytest.mark.parametrize("flag", (
    "trusted_clock_verified", "notification_authorized",
    "tool_execution_authorized", "automatic_replay_authorized",
    "consent_verified",
))
def test_preinstalled_false_preview_denial_getter_is_not_baseline(
    tmp_path, monkeypatch, flag,
):
    case = _case(tmp_path)
    monkeypatch.setattr(
        DisconnectedDuePreview, flag, property(lambda self: False),
    )
    with pytest.raises(resume.ScheduleResumeRejected, match="preview denial descriptor"):
        _review(case)


@pytest.mark.parametrize("replacement", (False, True))
def test_preinstalled_quarantine_authenticity_getter_is_rejected(
    tmp_path, monkeypatch, replacement,
):
    case = _case(tmp_path)
    monkeypatch.setattr(
        QuarantineWitness, "independently_authenticated",
        property(lambda self: replacement),
    )
    with pytest.raises(
        resume.ScheduleResumeRejected, match="quarantine witness authority descriptor",
    ):
        _review(case)


def test_reentrant_ledger_read_cannot_install_false_only_preview_getter(
    tmp_path, monkeypatch,
):
    case = _case(tmp_path)
    ledger = case[0]
    inspect = ledger.inspect
    reads = []

    def swap_on_first(*, retained):
        result = inspect(retained=retained)
        reads.append(1)
        monkeypatch.setattr(
            DisconnectedDuePreview, "consent_verified",
            property(lambda self: False),
        )
        return result

    monkeypatch.setattr(ledger, "inspect", swap_on_first)
    with pytest.raises(resume.ScheduleResumeRejected, match="preview denial descriptor"):
        _review(case)
    assert reads == [1]


def test_unmodified_restart_stays_denied_and_nonexecuting(tmp_path):
    result = _review(_case(tmp_path))
    assert result.next_state == "DUE_UNVERIFIED"
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False
