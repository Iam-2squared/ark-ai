"""Detached schedule restart denies forged result slots before SQLite access.

No real timer, notification, ToolBackend, trusted clock or consent is involved.
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


def _case(tmp_path):
    epoch = ("a" * 64, 1000, 1000, 3, 100)
    qpolicy = QuarantinePolicy(*epoch)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "schedule-resume.sqlite", policy=qpolicy, create=True,
    )
    return (
        ledger, DisconnectedSchedulePolicy(*epoch),
        DisconnectedScheduleCursor(0), genesis_quarantine_witness(qpolicy),
    )


def _review(case):
    ledger, policy, cursor, retained = case
    return resume.review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=1000,
    )


@pytest.mark.parametrize(
    "field", (
        "quarantine_chain_sha256", "quarantined_count", "next_occurrence_id",
        "next_state", "preview_sha256", "review_sha256",
    ),
)
def test_poisoned_resume_result_field_rejected_before_sqlite(
    tmp_path, monkeypatch, field,
):
    case = _case(tmp_path)
    invoked = []

    def hostile_read(_self):
        invoked.append(field)
        raise AssertionError("substituted resume result getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            resume.OfflineScheduleResumeReview,
            field, property(hostile_read),
        )
        patch.setattr(
            case[0], "inspect",
            lambda **_kw: pytest.fail("ledger inspected before preflight"),
        )
        with pytest.raises(
            resume.ScheduleResumeRejected, match="result carrier changed",
        ):
            _review(case)
    assert invoked == []
    assert case[0].inspect(retained=case[3]) == case[3]


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_poisoned_resume_lookup_hook_rejected_before_sqlite(
    tmp_path, monkeypatch, hook,
):
    case = _case(tmp_path)
    invoked = []

    def hostile_read(_self, _name):
        invoked.append(hook)
        raise AssertionError("substituted resume result lookup executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            resume.OfflineScheduleResumeReview,
            hook, hostile_read, raising=False,
        )
        patch.setattr(
            case[0], "inspect",
            lambda **_kw: pytest.fail("ledger inspected before preflight"),
        )
        with pytest.raises(
            resume.ScheduleResumeRejected, match="result carrier changed",
        ):
            _review(case)
    assert invoked == []


def test_late_preview_callback_cannot_replace_result_field(tmp_path, monkeypatch):
    case = _case(tmp_path)
    original = resume.preview_disconnected_schedule
    invoked = []

    def hostile_read(_self):
        invoked.append(True)
        raise AssertionError("late injected resume result slot executed")

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(
            resume.OfflineScheduleResumeReview,
            "review_sha256", property(hostile_read),
        )
        return result

    with monkeypatch.context() as patch:
        patch.setattr(resume, "preview_disconnected_schedule", mutate)
        with pytest.raises(
            resume.ScheduleResumeRejected, match="result carrier changed",
        ):
            _review(case)
    assert invoked == []


def test_original_schedule_resume_stays_passive(tmp_path):
    case = _case(tmp_path)
    report = _review(case)
    assert report.quarantined_count == 0
    assert report.next_state == "DUE_UNVERIFIED"
    assert report.trusted_clock_verified is False
    assert report.notification_authorized is False
    assert report.tool_execution_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.consent_verified is False
