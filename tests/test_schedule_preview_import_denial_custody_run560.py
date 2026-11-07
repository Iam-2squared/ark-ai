"""The local recurrence preview must never execute substituted authority code.

No OS timer, trusted clock, notification, external action or consent is
certified by these synthetic recurrence fixtures.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.disconnected_schedule_preview as mod


def _call():
    return mod.preview_disconnected_schedule(
        mod.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500),
        mod.DisconnectedScheduleCursor(0),
        observed_now_ms=10_000,
    )


@pytest.mark.parametrize("flag", mod._DENIAL_NAMES)
def test_preinstalled_false_authority_never_runs_before_recurrence(
    monkeypatch, flag,
):
    called = []

    def malicious(_result):
        called.append(flag)
        return False

    def forbidden_hash(*_args, **_kwargs):
        raise AssertionError("recurrence was hashed before preflight")

    monkeypatch.setattr(mod.DisconnectedDuePreview, flag, property(malicious))
    monkeypatch.setattr(mod.hashlib, "sha256", forbidden_hash)
    with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
        _call()
    assert called == []


def test_hash_callback_cannot_replace_a_denial_getter(monkeypatch):
    original = hashlib.sha256

    def mutate(payload=b""):
        monkeypatch.setattr(
            mod.DisconnectedDuePreview, "notification_authorized",
            property(lambda _result: False),
        )
        return original(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", mutate)
    with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
        _call()


def test_unmodified_preview_still_quarantines_late_due_slots():
    valid = _call()
    assert valid.state == "DUE_UNVERIFIED"
    late = mod.preview_disconnected_schedule(
        mod.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500),
        mod.DisconnectedScheduleCursor(0),
        observed_now_ms=10_501,
    )
    assert late.state == "EXPIRED_QUARANTINE"
    assert late.tool_execution_authorized is False
    assert late.automatic_replay_authorized is False
