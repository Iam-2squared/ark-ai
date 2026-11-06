"""Preflight proactive restart denial definitions before private ledger access.

Even a class-level getter that would return False is not the import-original
authority definition. These are disconnected scheduling fixtures only.
"""

from __future__ import annotations

import pytest
from test_schedule_resume_result_slots_run647 import _case, _review

from ark import offline_schedule_resume_review as resume
from ark.disconnected_schedule_preview import DisconnectedDuePreview
from ark.disconnected_schedule_quarantine_ledger import QuarantineWitness


@pytest.mark.parametrize(
    ("target", "flag", "message"),
    (
        (resume.OfflineScheduleResumeReview, "consent_verified", "denial descriptor replaced"),
        (DisconnectedDuePreview, "notification_authorized", "preview denial descriptor changed"),
        (
            QuarantineWitness, "independently_authenticated",
            "quarantine witness authority descriptor changed",
        ),
    ),
)
def test_preinstalled_false_authority_cannot_touch_private_ledger_path(
    tmp_path, monkeypatch, target, flag, message,
):
    case = _case(tmp_path)
    ledger = case[0]
    calls = []

    def poison_path(_self):
        calls.append("private ledger path accessed")
        raise AssertionError("restart accessed ledger before authority preflight")

    def poison_denial(_self):
        calls.append("substituted authority getter executed")
        raise AssertionError("substituted denial was executed")

    with monkeypatch.context() as patch:
        patch.setattr(type(ledger), "_path", property(poison_path), raising=False)
        patch.setattr(target, flag, property(poison_denial))
        with pytest.raises(resume.ScheduleResumeRejected, match=message):
            _review(case)
    assert calls == []


def test_unmodified_restart_result_does_not_authorize_dispatch(tmp_path):
    report = _review(_case(tmp_path))
    assert report.next_state == "DUE_UNVERIFIED"
    assert report.trusted_clock_verified is False
    assert report.notification_authorized is False
    assert report.tool_execution_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.consent_verified is False
