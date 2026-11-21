"""Run1067: scheduler preview admission helpers retain import identity.

Only synthetic recurrence inputs are used. No timer, notification, durable
cursor, consent, trusted clock, or tool dispatch is involved.
"""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_preview as schedule


def _inputs():
    return (
        schedule.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500),
        schedule.DisconnectedScheduleCursor(0),
    )


@pytest.mark.parametrize("helper", ("_valid_policy", "_occurrence"))
def test_rebound_preview_helper_is_rejected_before_callback(
    monkeypatch: pytest.MonkeyPatch, helper: str,
) -> None:
    policy, cursor = _inputs()
    called: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        called.append(helper)
        raise AssertionError("substituted schedule helper executed")

    with monkeypatch.context() as patch:
        patch.setattr(schedule, helper, forbidden)
        with pytest.raises(
            schedule.SchedulePreviewRejected,
            match="constructed preview carrier changed",
        ):
            schedule.preview_disconnected_schedule(
                policy, cursor, observed_now_ms=10_000,
            )

    assert called == []

    # The import-original helpers still produce the same inert due preview.
    healthy = schedule.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )
    assert healthy.state == "DUE_UNVERIFIED"
    assert healthy.trusted_clock_verified is False
    assert healthy.notification_authorized is False
    assert healthy.tool_execution_authorized is False
    assert healthy.automatic_replay_authorized is False
    assert healthy.consent_verified is False
