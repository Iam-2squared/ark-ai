"""Scheduler restart review rejects a rebound result class before SQLite.

No real clock, OS timer, notification, consent or ToolBackend is involved.
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
    genesis_quarantine_witness,
)


@pytest.mark.parametrize("replacement", ("object", "counterfeit"))
def test_rebound_result_class_does_not_read_quarantine(tmp_path, monkeypatch, replacement):
    values = ("a" * 64, 1000, 1000, 3, 100)
    policy = QuarantinePolicy(*values)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "synthetic.sqlite", policy=policy, create=True,
    )
    calls = []

    class Counterfeit:
        def __init__(self, *_args, **_kwargs):
            calls.append("forged constructor")

    def forbidden_inspection(*_args, **_kwargs):
        calls.append("SQLite inspection")
        raise AssertionError("untrusted class must fail before SQLite")

    monkeypatch.setattr(ledger, "inspect", forbidden_inspection)
    monkeypatch.setattr(
        resume, "OfflineScheduleResumeReview",
        object if replacement == "object" else Counterfeit,
    )
    with pytest.raises(resume.ScheduleResumeRejected, match="denial descriptor replaced"):
        resume.review_offline_schedule_resume(
            ledger, DisconnectedSchedulePolicy(*values),
            DisconnectedScheduleCursor(0),
            retained_quarantine=genesis_quarantine_witness(policy),
            observed_now_ms=1000,
        )
    assert calls == []


def test_original_class_produces_no_dispatch_authority(tmp_path):
    values = ("a" * 64, 1000, 1000, 3, 100)
    qpolicy = QuarantinePolicy(*values)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "synthetic.sqlite", policy=qpolicy, create=True,
    )
    result = resume.review_offline_schedule_resume(
        ledger, DisconnectedSchedulePolicy(*values),
        DisconnectedScheduleCursor(0),
        retained_quarantine=genesis_quarantine_witness(qpolicy),
        observed_now_ms=1000,
    )
    assert type(result) is resume._RESULT_TYPE
    assert result.next_state == "DUE_UNVERIFIED"
    assert all(getattr(result, name) is False for name in resume._DENIALS)
