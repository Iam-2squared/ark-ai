"""Synthetic schedule restart never trusts patchable witness equality."""

from __future__ import annotations

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
    genesis_quarantine_witness,
)


def _case(tmp_path):
    values = ("a" * 64, 1000, 1000, 3, 100)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=QuarantinePolicy(*values), create=True,
    )
    return (
        ledger, DisconnectedSchedulePolicy(*values),
        DisconnectedScheduleCursor(0),
        genesis_quarantine_witness(QuarantinePolicy(*values)),
    )


@pytest.mark.parametrize("read_index", (1, 2, 3))
def test_patched_equality_does_not_hide_forged_quarantine_witness(
    tmp_path, monkeypatch, read_index,
):
    ledger, policy, cursor, retained = _case(tmp_path)
    native = ledger.inspect
    calls = 0

    def stale(*, retained):
        nonlocal calls
        calls += 1
        genuine = native(retained=retained)
        if calls == read_index:
            return QuarantineWitness(genuine.count, "f" * 64)
        return genuine

    monkeypatch.setattr(QuarantineWitness, "__eq__", lambda self, other: True)
    monkeypatch.setattr(ledger, "inspect", stale)
    with pytest.raises(resume.ScheduleResumeRejected, match="quarantine"):
        resume.review_offline_schedule_resume(
            ledger, policy, cursor,
            retained_quarantine=retained, observed_now_ms=1000,
        )
    assert calls == read_index
    assert native(retained=retained).chain_sha256 == retained.chain_sha256


def test_original_quarantine_chain_is_accepted_without_authority(tmp_path):
    ledger, policy, cursor, retained = _case(tmp_path)
    result = resume.review_offline_schedule_resume(
        ledger, policy, cursor,
        retained_quarantine=retained, observed_now_ms=1000,
    )
    assert result.next_state == "DUE_UNVERIFIED"
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
