"""Scheduler restart denies spoofed import-time result authority before I/O."""

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
    genesis_quarantine_witness,
)


def _case(tmp_path):
    values = ("a" * 64, 1000, 1000, 3, 100)
    qpolicy = QuarantinePolicy(*values)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=qpolicy, create=True,
    )
    return (
        ledger, DisconnectedSchedulePolicy(*values),
        DisconnectedScheduleCursor(0),
        genesis_quarantine_witness(qpolicy),
    )


def _inspect(ledger, policy, cursor, retained):
    return resume.review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=1000,
    )


@pytest.mark.parametrize("name", resume._DENIALS)
def test_false_only_resume_descriptor_rejected_before_sqlite_read(
    tmp_path, monkeypatch, name,
):
    ledger, policy, cursor, retained = _case(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("preinstalled authority swap must reject before SQLite read")

    monkeypatch.setattr(ledger, "inspect", forbidden)
    monkeypatch.setattr(
        resume.OfflineScheduleResumeReview, name, property(lambda _: False),
    )
    with pytest.raises(resume.ScheduleResumeRejected, match="denial descriptor"):
        _inspect(ledger, policy, cursor, retained)


def test_reentrant_inspect_cannot_rebind_final_resume_denial(tmp_path, monkeypatch):
    ledger, policy, cursor, retained = _case(tmp_path)
    original = ledger.inspect
    calls = 0

    def mutate(*, retained):
        nonlocal calls
        calls += 1
        answer = original(retained=retained)
        monkeypatch.setattr(
            resume.OfflineScheduleResumeReview,
            "tool_execution_authorized", property(lambda _: False),
        )
        return answer

    monkeypatch.setattr(ledger, "inspect", mutate)
    with pytest.raises(resume.ScheduleResumeRejected, match="denial descriptor"):
        _inspect(ledger, policy, cursor, retained)
    assert calls == 1


def test_original_denials_preserve_passive_restart_preview(tmp_path):
    ledger, policy, cursor, retained = _case(tmp_path)
    review = _inspect(ledger, policy, cursor, retained)
    assert review.next_state == "DUE_UNVERIFIED"
    assert all(getattr(review, name) is False for name in resume._DENIALS)
