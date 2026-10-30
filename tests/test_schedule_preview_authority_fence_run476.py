"""Synthetic due previews cannot gain clock, consent or dispatch authority.

Tests only caller-supplied occurrence metadata; no timer or notification runs.
"""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_preview as mod


def _preview():
    return mod.preview_disconnected_schedule(
        mod.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500),
        mod.DisconnectedScheduleCursor(0),
        observed_now_ms=10_000,
    )


def test_ordinary_preview_is_inert_and_deterministic():
    one = _preview()
    assert one == _preview()
    assert one.state == "DUE_UNVERIFIED"
    assert one.trusted_clock_verified is False
    assert one.notification_authorized is False
    assert one.tool_execution_authorized is False
    assert one.automatic_replay_authorized is False
    assert one.consent_verified is False


@pytest.mark.parametrize(
    "name",
    (
        "trusted_clock_verified",
        "notification_authorized",
        "tool_execution_authorized",
        "automatic_replay_authorized",
        "consent_verified",
    ),
)
@pytest.mark.parametrize("forged", (True, 1, "allowed"))
def test_preview_refuses_authority_properties_on_exact_result(
    monkeypatch, name, forged,
):
    # Even the correct dataclass type can expose a falsified property if its
    # descriptor changes during synthetic construction. Reject instead of
    # returning a seemingly normal due preview with active authority flags.
    monkeypatch.setattr(
        mod.DisconnectedDuePreview,
        name,
        property(lambda _result: forged),
    )
    with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
        _preview()
