"""A false late due-preview getter cannot grant an earlier authority flag."""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_preview as mod


def _inputs():
    policy = mod.DisconnectedSchedulePolicy(
        "a" * 64, 10_000, 5_000, 3, 500,
    )
    cursor = mod.DisconnectedScheduleCursor(0)
    return policy, cursor


def _preview():
    policy, cursor = _inputs()
    return mod.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )


def test_normal_due_preview_remains_inert():
    result = _preview()
    assert result.state == "DUE_UNVERIFIED"
    assert result.automatic_replay_authorized is False
    assert result.tool_execution_authorized is False
    assert result.notification_authorized is False


@pytest.mark.parametrize("earlier_flag", (
    "trusted_clock_verified", "notification_authorized",
    "tool_execution_authorized", "automatic_replay_authorized",
))
def test_final_false_getter_cannot_grant_earlier_preview_authority(
    monkeypatch, earlier_flag,
):
    def mutate_and_deny(_result):
        monkeypatch.setattr(
            mod.DisconnectedDuePreview, earlier_flag,
            property(lambda result: True),
        )
        return False

    monkeypatch.setattr(
        mod.DisconnectedDuePreview,
        "consent_verified",
        property(mutate_and_deny),
    )
    with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
        _preview()


def test_self_mutating_false_getter_cannot_return_authoritative_preview(
    monkeypatch,
):
    def mutate_and_deny(_result):
        monkeypatch.setattr(
            mod.DisconnectedDuePreview,
            "notification_authorized",
            property(lambda result: True),
        )
        return False

    monkeypatch.setattr(
        mod.DisconnectedDuePreview,
        "notification_authorized",
        property(mutate_and_deny),
    )
    with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
        _preview()
