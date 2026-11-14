"""Offline proactive restart rejects injected code before its result is built.

These records are disconnected timing fixtures, never actual notifications,
authenticated time, consent, or automatic execution authority.
"""

import pytest
from test_offline_schedule_resume_run534 import _fixture, _review

from ark import offline_schedule_resume_review as resume
from ark.disconnected_schedule_preview import DisconnectedScheduleCursor


@pytest.mark.parametrize("attack", ("initializer", "descriptor"))
def test_preinstalled_injected_result_code_denied_without_inspection(
    tmp_path, monkeypatch, attack,
):
    _, ledger, policy, _, retained = _fixture(tmp_path)
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("forged initializer ran")
        raise AssertionError("initializer must never execute")

    class PoisonDescriptor:
        def __get__(self, _instance, _owner=None):
            calls.append("forged descriptor ran")
            raise AssertionError("descriptor must never execute")

    def forbidden_inspect(*_args, **_kwargs):
        raise AssertionError("must reject before SQLite inspection")

    with monkeypatch.context() as patch:
        if attack == "initializer":
            patch.setattr(resume.OfflineScheduleResumeReview, "__init__", forbidden)
        else:
            patch.setattr(
                resume.OfflineScheduleResumeReview,
                "consent_verified", PoisonDescriptor(),
            )
        patch.setattr(ledger, "inspect", forbidden_inspect)
        with pytest.raises(
            resume.ScheduleResumeRejected, match="denial descriptor replaced",
        ):
            _review(ledger, policy, DisconnectedScheduleCursor(0), retained, 1000)

    assert calls == []


@pytest.mark.parametrize("phase", ("ledger", "preview"))
def test_late_callback_cannot_replace_result_initializer(
    tmp_path, monkeypatch, phase,
):
    _, ledger, policy, _, retained = _fixture(tmp_path)
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("forged initializer ran")
        raise AssertionError("initializer must never execute")

    with monkeypatch.context() as patch:
        if phase == "ledger":
            original = ledger.inspect

            def hook(*, retained):
                result = original(retained=retained)
                patch.setattr(
                    resume.OfflineScheduleResumeReview, "__init__", forbidden,
                )
                return result

            patch.setattr(ledger, "inspect", hook)
        else:
            original = resume.preview_disconnected_schedule

            def hook(*args, **kwargs):
                result = original(*args, **kwargs)
                patch.setattr(
                    resume.OfflineScheduleResumeReview, "__init__", forbidden,
                )
                return result

            patch.setattr(resume, "preview_disconnected_schedule", hook)

        with pytest.raises(
            resume.ScheduleResumeRejected, match="denial descriptor replaced",
        ):
            _review(ledger, policy, DisconnectedScheduleCursor(0), retained, 1000)

    assert calls == []


def test_unmodified_scheduler_restart_is_readonly_and_non_authorizing(tmp_path):
    _, ledger, policy, _, retained = _fixture(tmp_path)
    result = _review(
        ledger, policy, DisconnectedScheduleCursor(0), retained, 1000,
    )
    assert result.next_state == "DUE_UNVERIFIED"
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
