"""Every detached Scheduler quarantine read remains non-authorizing.

The synthetic ledger is local. Caller-observed time cannot dispatch or replay.
"""

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
    policy = DisconnectedSchedulePolicy("a" * 64, 1000, 1000, 3, 100)
    quarantine_policy = QuarantinePolicy("a" * 64, 1000, 1000, 3, 100)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=quarantine_policy, create=True,
    )
    retained = genesis_quarantine_witness(quarantine_policy)
    return ledger, policy, retained


def _review(ledger, policy, retained):
    return resume.review_offline_schedule_resume(
        ledger, policy, DisconnectedScheduleCursor(0),
        retained_quarantine=retained, observed_now_ms=1000,
    )


def test_three_honest_reads_preserve_nonauthorizing_due_review(tmp_path):
    ledger, policy, retained = _case(tmp_path)
    result = _review(ledger, policy, retained)
    assert result.next_state == "DUE_UNVERIFIED"
    assert result.quarantined_count == 0
    assert result.notification_authorized is False
    assert result.trusted_clock_verified is False
    assert result.automatic_replay_authorized is False
    assert ledger.inspect(retained=retained) == retained


@pytest.mark.parametrize("read_number,claimed", (
    (1, False), (2, False), (3, False),
    (2, True), (3, True),
))
def test_changed_quarantine_authority_descriptor_cannot_cross_restart_read(
    tmp_path, monkeypatch, read_number, claimed,
):
    ledger, policy, retained = _case(tmp_path)
    native = ledger.inspect
    count = [0]

    def rebind(*, retained):
        witness = native(retained=retained)
        count[0] += 1
        if count[0] == read_number:
            monkeypatch.setattr(
                QuarantineWitness, "independently_authenticated",
                property(lambda self: claimed),
            )
        return witness

    monkeypatch.setattr(ledger, "inspect", rebind)
    with pytest.raises(resume.ScheduleResumeRejected, match="quarantine witness"):
        _review(ledger, policy, retained)
    assert count[0] == read_number
