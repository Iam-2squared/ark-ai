"""Late due-preview authority getters cannot mutate inputs or returned fields.

Disconnected fixtures only; no timer, OS notification, or Tool execution.
"""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_preview as schedule


@pytest.mark.parametrize(
    "target",
    ("policy", "cursor", "result_state", "result_fingerprint"),
)
def test_false_authority_getter_cannot_modify_review_epoch(monkeypatch, target):
    policy = schedule.DisconnectedSchedulePolicy(
        "a" * 64, 10_000, 5_000, 3, 500,
    )
    cursor = schedule.DisconnectedScheduleCursor(0)

    def late_side_effect(result):
        if target == "policy":
            object.__setattr__(policy, "policy_sha256", "b" * 64)
        elif target == "cursor":
            object.__setattr__(cursor, "next_index", 1)
        elif target == "result_state":
            object.__setattr__(result, "state", "EXECUTABLE")
        else:
            object.__setattr__(result, "fingerprint", "f" * 64)
        return False  # A false permission does not make its getter inert.

    monkeypatch.setattr(
        schedule.DisconnectedDuePreview,
        "consent_verified",
        property(late_side_effect),
    )
    with pytest.raises(schedule.SchedulePreviewRejected):
        schedule.preview_disconnected_schedule(
            policy, cursor, observed_now_ms=10_000,
        )


def test_normal_inert_schedule_keeps_deterministic_fingerprint():
    policy = schedule.DisconnectedSchedulePolicy(
        "a" * 64, 10_000, 5_000, 3, 500,
    )
    cursor = schedule.DisconnectedScheduleCursor(0)
    first = schedule.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )
    second = schedule.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )
    assert first == second
    assert first.state == "DUE_UNVERIFIED"
    assert first.automatic_replay_authorized is False
